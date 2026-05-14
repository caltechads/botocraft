import ast
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Protocol, Sequence, cast

import yaml

if TYPE_CHECKING:
    from botocraft.services.schemas import Schema


class SchemaManagerProtocol(Protocol):
    """
    Minimal protocol for the generated Schema manager used by the exporter.
    """

    def list(self, *, RegistryName: str, SchemaNamePrefix: str):  # noqa: N803
        """
        List schemas from a registry with a prefix filter.

        Keyword Args:
            RegistryName: Registry name to search.
            SchemaNamePrefix: Prefix used to filter schema names.

        Returns:
            Query set-like object whose ``results`` contain Schema models.

        """
        ...

    def export(
        self,
        *,
        RegistryName: str,  # noqa: N803
        SchemaName: str,  # noqa: N803
        SchemaVersion: str | None,  # noqa: N803
        Type: str,  # noqa: N803
    ):
        """
        Export one schema version in a requested format.

        Keyword Args:
            RegistryName: Registry that owns the schema.
            SchemaName: Schema name to export.
            SchemaVersion: Optional version override.
            Type: Export format, such as ``OpenApi3``.

        Returns:
            Export response with schema content.

        """
        ...


class EventBridgeAuthoringError(RuntimeError):
    """
    Raised when EventBridge schema export or code generation fails.
    """


@dataclass(frozen=True)
class ExportedEventModule:
    """
    Describe one generated raw EventBridge module.

    Args:
        registry_name: Registry used to export the schema.
        schema_name: EventBridge schema name.
        schema_version: Exported schema version.
        file_path: Generated Python module path.
        class_name: Public class name exported from the module.

    """

    #: Registry used to export the schema.
    registry_name: str
    #: EventBridge schema name.
    schema_name: str
    #: Exported schema version.
    schema_version: str | None
    #: Generated Python module path.
    file_path: Path
    #: Public class name exported from the module.
    class_name: str


@dataclass(frozen=True)
class EventBridgeExportReport:
    """
    Summarize one EventBridge raw export run.

    Args:
        service: AWS service whose schemas were exported.
        modules: Generated or planned raw modules.
        dry_run: Whether file writes and subprocesses were skipped.

    """

    #: AWS service whose schemas were exported.
    service: str
    #: Generated or planned raw modules.
    modules: tuple[ExportedEventModule, ...]
    #: Whether file writes and subprocesses were skipped.
    dry_run: bool


class EventBridgeServiceExporter:
    """
    Export EventBridge schemas for one AWS service into raw Pydantic modules.

    Args:
        schema_manager: Optional injected Schema manager for tests.
        command_runner: Optional subprocess runner for codegen steps.

    """

    def __init__(
        self,
        schema_manager: SchemaManagerProtocol | None = None,
        command_runner: Callable[[Sequence[str]], None] | None = None,
    ) -> None:
        """
        Initialize exporter collaborators.

        Keyword Args:
            schema_manager: Optional injected Schema manager for tests.
            command_runner: Optional subprocess runner for codegen steps.

        """
        #: Schema manager used for list, list_versions, and export calls.
        self.schema_manager = schema_manager or self._load_schema_manager()
        #: Subprocess runner used for code generation steps.
        self.command_runner = command_runner or self._run_command

    def export_service(
        self,
        service: str,
        *,
        registry_names: Sequence[str],
        raw_root: Path,
        schema_name_prefix: str | None = None,
        dry_run: bool = False,
    ) -> EventBridgeExportReport:
        """
        Export schemas for one AWS service into raw modules.

        Side Effects:
            Creates package directories and Python modules under ``raw_root``.
            Runs ``datamodel-codegen`` and ``bump-pydantic`` unless ``dry_run``
            is enabled.

        Args:
            service: AWS service name to export.

        Keyword Args:
            registry_names: Registries to search in order.
            raw_root: Root directory that contains per-service raw modules.
            schema_name_prefix: Optional prefix override for schema lookup.
            dry_run: When ``True``, only compute planned outputs.

        Raises:
            EventBridgeAuthoringError: No matching schemas are found or code
                generation fails.

        Returns:
            Summary of generated modules.

        """
        effective_prefix = schema_name_prefix or f"aws.{service}"
        matched_schemas = self._list_matching_schemas(
            registry_names=registry_names,
            schema_name_prefix=effective_prefix,
        )
        if not matched_schemas:
            if tuple(registry_names) == ("aws.events",):
                msg = (
                    "No EventBridge schemas matched in default registry "
                    f"'aws.events' for prefix '{effective_prefix}'. Retry with "
                    "one or more explicit --registry-name values."
                )
            else:
                registries = ", ".join(registry_names)
                msg = (
                    f"No EventBridge schemas matched prefix '{effective_prefix}' "
                    f"in registries: {registries}."
                )
            raise EventBridgeAuthoringError(msg)

        service_root = raw_root / service
        modules = [
            self._export_schema(
                service=service,
                schema=schema,
                service_root=service_root,
                dry_run=dry_run,
            )
            for schema in matched_schemas
        ]
        if not dry_run:
            self._update_service_init(service_root, modules)
            self._update_raw_root_init(raw_root, service)
        return EventBridgeExportReport(
            service=service,
            modules=tuple(modules),
            dry_run=dry_run,
        )

    def _load_schema_manager(self) -> SchemaManagerProtocol:
        """
        Load generated Schema manager lazily.

        Returns:
            Generated Schema manager object.

        """
        from botocraft.services.schemas import Schema

        return Schema.objects

    def _list_matching_schemas(
        self,
        *,
        registry_names: Sequence[str],
        schema_name_prefix: str,
    ) -> list["Schema"]:
        """
        List all schemas that match a prefix across candidate registries.

        Keyword Args:
            registry_names: Registries to search.
            schema_name_prefix: Prefix used to filter schema names.

        Returns:
            Matching public Schema models.

        """
        matches: list[Schema] = []
        for registry_name in registry_names:
            query_set = self.schema_manager.list(
                RegistryName=registry_name,
                SchemaNamePrefix=schema_name_prefix,
            )
            matches.extend(query_set.results)
        return sorted(matches, key=lambda schema: schema.SchemaName or "")

    def _export_schema(
        self,
        *,
        service: str,
        schema: "Schema",
        service_root: Path,
        dry_run: bool,
    ) -> ExportedEventModule:
        """
        Export one EventBridge schema and generate its raw module.

        Side Effects:
            Writes one Python module unless ``dry_run`` is enabled.

        Keyword Args:
            service: AWS service name used for class prefixing.
            schema: Schema model to export.
            service_root: Target raw service directory.
            dry_run: When ``True``, compute outputs without writing files.

        Returns:
            Metadata for the generated module.

        """
        registry_name = cast("str", schema.RegistryName)
        schema_name = cast("str", schema.SchemaName)
        schema_version = self._latest_schema_version(schema)
        export = self.schema_manager.export(
            RegistryName=registry_name,
            SchemaName=schema_name,
            SchemaVersion=schema_version,
            Type="JSONSchemaDraft4",
        )
        if export is None or export.Content is None:
            msg = (
                f"Schema export returned no content for {registry_name}/"
                f"{schema_name}."
            )
            raise EventBridgeAuthoringError(msg)
        module_stem, desired_class_name = self._module_names(
            service=service,
            schema_name=schema_name,
            content=export.Content,
        )
        file_path = service_root / f"{module_stem}.py"
        if not dry_run:
            service_root.mkdir(parents=True, exist_ok=True)
            self._generate_python_module(
                schema_content=export.Content,
                file_path=file_path,
            )
            self._rename_primary_class(
                file_path=file_path,
                desired_class_name=desired_class_name,
            )
        return ExportedEventModule(
            registry_name=registry_name,
            schema_name=schema_name,
            schema_version=schema_version,
            file_path=file_path,
            class_name=desired_class_name,
        )

    def _latest_schema_version(self, schema: "Schema") -> str | None:
        """
        Choose newest known version for a schema.

        Args:
            schema: Schema whose versions should be inspected.

        Returns:
            Latest version string, or ``None`` when the schema has no versions.

        """
        versions = schema.versions()
        if not versions:
            return None
        latest = max(
            versions,
            key=lambda version: self._version_sort_key(version.SchemaVersion),
        )
        return latest.SchemaVersion

    def _version_sort_key(self, version: str | None) -> tuple[int, int, str]:
        """
        Build stable sort key for schema version strings.

        Args:
            version: Schema version string from EventBridge.

        Returns:
            Tuple that sorts numeric versions numerically and falls back to
            lexical comparison otherwise.

        """
        if version is None:
            return (0, -1, "")
        if version.isdigit():
            return (1, int(version), version)
        return (0, -1, version)

    def _module_names(
        self,
        *,
        service: str,
        schema_name: str,
        content: str,
    ) -> tuple[str, str]:
        """
        Compute normalized file and class names from exported schema content.

        Keyword Args:
            service: AWS service name used for class prefixing.
            schema_name: EventBridge schema name.
            content: Exported schema document.

        Returns:
            Tuple of ``(module_stem, class_name)``.

        """
        title = self._schema_title(content) or schema_name.rsplit(".", maxsplit=1)[-1]
        module_stem = self._snake_case_title(title)
        class_name = (
            f"{self._service_class_prefix(service)}"
            f"{self._pascal_case_title(title)}Event"
        )
        return module_stem, class_name

    def _schema_title(self, content: str) -> str | None:
        """
        Extract schema title from exported schema content.

        Args:
            content: Exported schema document.

        Returns:
            Schema title when present.

        """
        parsed = yaml.safe_load(content)
        if not isinstance(parsed, dict):
            return None
        title = parsed.get("title")
        if isinstance(title, str):
            return title
        info = parsed.get("info")
        if isinstance(info, dict):
            nested_title = info.get("title")
            if isinstance(nested_title, str):
                return nested_title
        return None

    def _snake_case_title(self, title: str) -> str:
        """
        Normalize display title into snake_case module stem.

        Args:
            title: Display title or fallback schema tail.

        Returns:
            Module stem for generated raw files.

        """
        normalized = re.sub(r"[^0-9A-Za-z]+", "_", title).strip("_")
        normalized = re.sub(r"_+", "_", normalized)
        return normalized.lower()

    def _pascal_case_title(self, title: str) -> str:
        """
        Normalize display title into PascalCase.

        Args:
            title: Display title or fallback schema tail.

        Returns:
            PascalCase type suffix.

        """
        words = re.findall(r"[0-9A-Za-z]+", title)
        if not words:
            return "Event"
        return "".join(
            word if not word.islower() else word.capitalize() for word in words
        )

    def _service_class_prefix(self, service: str) -> str:
        """
        Build service-specific prefix used for raw event classes.

        Args:
            service: AWS service name passed to the CLI.

        Returns:
            Service prefix for generated class names.

        """
        parts = re.split(r"[^0-9A-Za-z]+", service)
        short_acronym_length = 3
        return "".join(
            part.upper()
            if part.islower() and len(part) <= short_acronym_length
            else part.capitalize()
            for part in parts
            if part
        )

    def _generate_python_module(self, *, schema_content: str, file_path: Path) -> None:
        """
        Run external code generators for one exported EventBridge schema.

        Side Effects:
            Creates and rewrites ``file_path``.

        Keyword Args:
            schema_content: Exported schema content.
            file_path: Target Python module path.

        Raises:
            EventBridgeAuthoringError: One of the subprocess tools fails.

        """
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_path = Path(temp_dir) / "schema.json"
            schema_path.write_text(schema_content, encoding="utf-8")
            self.command_runner(
                [
                    "datamodel-codegen",
                    "--input",
                    str(schema_path),
                    "--input-file-type",
                    "jsonschema",
                    "--output-model-type",
                    "pydantic_v2.BaseModel",
                    "--output",
                    str(file_path),
                ]
            )
            self.command_runner(["bump-pydantic", str(file_path)])

    def _rename_primary_class(
        self,
        *,
        file_path: Path,
        desired_class_name: str,
    ) -> None:
        """
        Rename primary generated class to Botocraft raw naming conventions.

        Side Effects:
            Rewrites ``file_path`` when a class rename is needed.

        Keyword Args:
            file_path: Generated Python module path.
            desired_class_name: Final class name to expose from the module.

        """
        contents = file_path.read_text(encoding="utf-8")
        class_names = self._top_level_class_names(contents)
        if not class_names:
            return
        source_class_name = class_names[-1]
        renamed = contents
        if (
            desired_class_name in class_names
            and source_class_name != desired_class_name
        ):
            helper_class_name = f"{desired_class_name}Detail"
            renamed = re.sub(
                rf"\b{re.escape(desired_class_name)}\b",
                helper_class_name,
                renamed,
            )
        if source_class_name == desired_class_name:
            return
        renamed = re.sub(
            rf"\b{re.escape(source_class_name)}\b",
            desired_class_name,
            renamed,
        )
        file_path.write_text(renamed, encoding="utf-8")

    def _top_level_class_names(self, contents: str) -> list[str]:
        """
        Parse top-level class names from generated Python source.

        Args:
            contents: Python source text.

        Returns:
            Top-level class names in source order.

        """
        module = ast.parse(contents)
        return [
            node.name
            for node in module.body
            if isinstance(node, ast.ClassDef)
        ]

    def _update_service_init(
        self,
        service_root: Path,
        modules: Sequence[ExportedEventModule],
    ) -> None:
        """
        Update per-service raw exports idempotently.

        Side Effects:
            Creates or rewrites ``service_root / "__init__.py"``.

        Args:
            service_root: Raw service package directory.
            modules: Exported modules that should be re-exported.

        """
        export_lines = sorted(
            {
                (
                    f"from .{module.file_path.stem} import "
                    f"{module.class_name}  # noqa: F401"
                )
                for module in modules
            }
        )
        init_path = service_root / "__init__.py"
        self._write_export_file(init_path, export_lines)

    def _update_raw_root_init(self, raw_root: Path, service: str) -> None:
        """
        Update raw package root to export one service package.

        Side Effects:
            Creates or rewrites ``raw_root / "__init__.py"``.

        Args:
            raw_root: EventBridge raw package root.
            service: AWS service package name to export.

        """
        init_path = raw_root / "__init__.py"
        existing_lines: list[str] = []
        if init_path.exists():
            existing_lines = [
                line.rstrip("\n")
                for line in init_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        export_line = f"from .{service} import *  # noqa: F403"
        if export_line not in existing_lines:
            existing_lines.append(export_line)
        self._write_export_file(init_path, sorted(existing_lines))

    def _write_export_file(self, path: Path, lines: Sequence[str]) -> None:
        """
        Write deterministic export file.

        Side Effects:
            Creates or rewrites ``path``.

        Args:
            path: Python export file to write.
            lines: Export statements that should appear in the file.

        """
        path.parent.mkdir(parents=True, exist_ok=True)
        rendered = "\n".join(lines)
        if rendered:
            rendered = f"{rendered}\n"
        path.write_text(rendered, encoding="utf-8")

    def _run_command(self, command: Sequence[str]) -> None:
        """
        Execute one external authoring command.

        Side Effects:
            Runs an external subprocess.

        Args:
            command: Command line to execute.

        Raises:
            EventBridgeAuthoringError: Subprocess exits non-zero.

        """
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.strip()
            stdout = exc.stdout.strip()
            details = stderr or stdout or f"exit code {exc.returncode}"
            msg = f"Command failed: {' '.join(command)}: {details}"
            raise EventBridgeAuthoringError(msg) from exc
