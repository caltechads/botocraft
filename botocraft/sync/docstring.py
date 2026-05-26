import re
from argparse import Namespace
from dataclasses import asdict, dataclass, field
from textwrap import wrap
from typing import Any, ClassVar, Literal

from docformatter import Formatter
from markdownify import markdownify


@dataclass
class FormatterArgs:
    """
    Store Botocraft docformatter defaults for generated service code.
    """

    #: Optional line range filter.
    line_range: tuple[int, int] | None = None
    #: Optional docstring length range filter.
    length_range: tuple[int, int] | None = None
    #: Use Black-compatible formatting behavior.
    black: bool = True
    #: Check mode flag for docformatter.
    check: bool = False
    #: Place closing quotes on a new line for wrapped one-line docstrings.
    close_quotes_on_newline: bool = False
    #: Diff mode flag for docformatter.
    diff: bool = False
    #: Optional excluded paths.
    exclude: list[str] | None = None
    #: Explicit file list for CLI-oriented formatter API.
    files: list[str] = field(default_factory=list)
    #: Parameter-list formatting style.
    style: Literal["sphinx", "epytext"] = "sphinx"
    #: Leave aggressive wrapping to Botocraft's post-processing pass.
    force_wrap: bool = False
    #: In-place mode flag for docformatter.
    in_place: bool = False
    #: Expand one-line summaries to multiline docstrings.
    make_summary_multi_line: bool = True
    #: Insert newline before multiline summary.
    pre_summary_newline: bool = True
    #: Insert space after opening quotes.
    pre_summary_space: bool = True
    #: Preserve post-summary newline option for legacy compatibility.
    post_summary_newline: bool = True
    #: Do not insert blank line after description.
    post_description_blank: bool = False
    #: Use strict formatting rules.
    non_strict: bool = False
    #: Recursive mode flag for docformatter.
    recursive: bool = False
    #: Regex that identifies reST section adornments.
    rest_section_adorns: str = r"""[!\"#$%&'()*+,-./\\:;<=>?@[]^_`{|}~]{4,}"""
    #: Tab width used when wrapping docstrings.
    tab_width: int = 4
    #: Summary wrap column.
    wrap_summaries: int = 88
    #: Description wrap column.
    wrap_descriptions: int = 88
    #: Words that should not be auto-capitalized.
    non_cap: list[str] = field(default_factory=list)


class CodeDocstringFormatter:
    """
    Format generated Python source docstrings with installed docformatter API.

    This adapter preserves Botocraft's historical formatter defaults while
    tolerating private method renames across docformatter releases.

    Args:
        formatter_cls: Optional formatter implementation override for tests.

    """

    #: Regex for section headers that docformatter can collapse onto one line.
    SECTION_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?P<indent>\s+)"
        r"(?P<section>Args|Returns|Raises|Yields|Keyword Args|Side Effects):"
        r"\s+(?P<rest>\S.*)$"
    )
    #: Regex for argument/field lines inside docstring sections.
    ARGUMENT_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?P<name>[^:]+:\s+)(?P<rest>.+)$"
    )
    #: Section headers that should never be wrapped inline.
    SECTION_HEADERS: ClassVar[frozenset[str]] = frozenset(
        {
            "Args:",
            "Keyword Args:",
            "Raises:",
            "Returns:",
            "Side Effects:",
            "Yields:",
        }
    )
    #: Section headers whose bodies use parameter-style continuation indentation.
    PARAMETER_SECTIONS: ClassVar[frozenset[str]] = frozenset({"Args:", "Keyword Args:"})

    def __init__(self, formatter_cls: type[Any] | None = None):
        """
        Initialize formatter adapter for generated source code.

        Args:
            formatter_cls: docformatter formatter implementation to wrap.

        """
        #: Formatter implementation used for code formatting.
        self.formatter_cls = formatter_cls or Formatter
        #: Namespace of Botocraft docformatter defaults.
        self.args = Namespace(**asdict(FormatterArgs()))
        #: Maximum line length for conservative docstring rewrapping.
        self.wrap_length = 88

    def format_code(self, source: str) -> str:
        """
        Format Python source code docstrings using docformatter compatibility path.

        Args:
            source: generated Python source code

        Returns:
            Source code with docstrings formatted.

        """
        formatter = self.formatter_cls(self.args, None, None, None)
        format_method = getattr(formatter, "_do_format_code", None)
        if format_method is None:
            format_method = getattr(formatter, "_format_code")  # noqa: B009
        return self._rewrap_docstring_lines(format_method(source))

    def _rewrap_docstring_lines(self, source: str) -> str:
        """
        Rewrap docstring prose conservatively after docformatter runs.

        Args:
            source: Python source code after docformatter processing.

        Returns:
            Source code with section-safe docstring wrapping.

        """
        output_lines: list[str] = []
        in_docstring = False
        active_section: str | None = None
        continuation_indent: str | None = None
        for line in source.splitlines():
            if line.count('"""') % 2 == 1:
                if in_docstring:
                    active_section = None
                    continuation_indent = None
                output_lines.append(line)
                in_docstring = not in_docstring
                continue

            if not in_docstring:
                output_lines.append(line)
                continue

            normalized_line, active_section, continuation_indent = (
                self._normalize_section_line(line, active_section, continuation_indent)
            )
            if self._is_wrappable_docstring_line(normalized_line):
                output_lines.extend(self._wrap_docstring_line(normalized_line))
            else:
                output_lines.append(normalized_line)

        return "\n".join(output_lines) + ("\n" if source.endswith("\n") else "")

    def _normalize_section_line(
        self,
        line: str,
        active_section: str | None,
        continuation_indent: str | None,
    ) -> tuple[str, str | None, str | None]:
        """
        Normalize section and continuation indentation for docstring lines.

        Args:
            line: Single source line inside a docstring block.
            active_section: Current docstring section header, if any.
            continuation_indent: Expected continuation indentation for active param.

        Returns:
            Tuple of normalized line, updated active section, and continuation indent.

        """
        stripped = line.strip()
        if not stripped:
            return line, active_section, continuation_indent
        if stripped in self.SECTION_HEADERS:
            return line, stripped, None

        line_indent = line[: len(line) - len(line.lstrip())]
        if active_section in self.PARAMETER_SECTIONS:
            argument_match = self.ARGUMENT_RE.match(line.lstrip())
            if argument_match is not None:
                return (
                    line,
                    active_section,
                    f"{line_indent}    ",
                )
            if (
                continuation_indent is not None
                and line_indent == continuation_indent[:-4]
            ):
                return (
                    f"{continuation_indent}{line.lstrip()}",
                    active_section,
                    continuation_indent,
                )
        return line, active_section, continuation_indent

    def _is_wrappable_docstring_line(self, line: str) -> bool:
        """
        Check whether a docstring line is safe for Botocraft rewrapping.

        Args:
            line: Single source line inside a docstring block.

        Returns:
            ``True`` when line should be rewrapped.

        """
        stripped = line.strip()
        if not stripped or stripped == '"""':
            return False
        if stripped in self.SECTION_HEADERS:
            return False
        return len(line) > self.wrap_length or bool(self.SECTION_RE.match(line))

    def _wrap_docstring_line(self, line: str) -> list[str]:
        """
        Wrap one docstring line while preserving section indentation.

        Args:
            line: Single source line inside a docstring block.

        Returns:
            Wrapped replacement lines.

        """
        section_match = self.SECTION_RE.match(line)
        if section_match is not None:
            section_indent = section_match.group("indent")
            section_lines = self._wrap_docstring_line(
                f"{section_indent}    {section_match.group('rest')}"
            )
            return [f"{section_indent}{section_match.group('section')}", *section_lines]

        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]
        if "http" in stripped or "`<" in stripped:
            return [line]

        argument_match = self.ARGUMENT_RE.match(stripped)
        if argument_match is not None:
            wrapped = wrap(
                argument_match.group("rest"),
                width=self.wrap_length,
                initial_indent=f"{indent}{argument_match.group('name')}",
                subsequent_indent=f"{indent}    ",
                break_long_words=False,
                break_on_hyphens=False,
            )
            return wrapped or [line]

        wrapped = wrap(
            stripped,
            width=self.wrap_length,
            initial_indent=indent,
            subsequent_indent=indent,
            break_long_words=False,
            break_on_hyphens=False,
        )
        return wrapped or [line]


class DocumentationFormatter:
    """
    Convert botocore HTML docs into reStructuredText fragments for generators.

    Args:
        max_length: Maximum output line length for wrapped prose.

    """

    #: Regex for Markdown-style links.
    MARKDOWN_LINK_RE = re.compile(
        r"(?:\[(?P<text>.*?)\])\((?P<link>.*?)\)", re.MULTILINE | re.DOTALL
    )
    #: Regex for Python object references that need single backticks restored.
    PY_OBJECT_RE = re.compile(r"py:(.*?):``(.*?)``", re.MULTILINE | re.DOTALL)

    def __init__(self, max_length: int = 120):
        """
        Initialize documentation formatter.

        Args:
            max_length: Maximum output line length for wrapped prose.

        """
        #: Wrap lines at this length.
        self.max_length = max_length

    def _clean_uls(self, documentation: str) -> str:
        """
        Look through ``documentation`` for unordered lists and clean them up.

        This means wrapping them properly at 79 characters, and adding a blank
        line before and after.

        Args:
            documentation: the partially processed reStructuredText
                documentation

        Returns:
            The documentation with unordered lists cleaned up.

        """
        lines = []
        source_lines = documentation.split("\n")
        for i, line in enumerate(source_lines):
            if line.startswith("*"):
                previous_line = source_lines[i - 1]
                if previous_line.strip() != "" and not previous_line.startswith("*"):
                    lines.append("")
                if len(line) > self.max_length:
                    wrapped = wrap(line, self.max_length)
                    lines.append(wrapped[0])
                    lines.extend([f"  {line}" for line in wrapped[1:]])
                else:
                    lines.append(line)
            elif len(line) > self.max_length:
                lines.extend(wrap(line, self.max_length))
            else:
                lines.append(line)
        return "\n".join(lines)

    def _clean_links(self, documentation: str) -> str:
        """
        Transform our Markdown links to reStructuredText links.

        Args:
            documentation: the partially processed reStructuredText
                documentation

        Returns:
            The documentation with links cleaned up.

        """
        for match in self.MARKDOWN_LINK_RE.finditer(documentation):
            text = match.group("text")
            link = match.group("link")
            link = link.replace(" ", "")
            documentation = documentation.replace(match.group(0), f"`{text} <{link}>`_")
        return documentation

    def _undo_double_backticks(self, documentation: str) -> str:
        """
        If we have custom docstrings that are already in reStructuredText, then
        we can end up with double backticks in our documentation from when we
        convert single back ticks to double in the Markdown -> reStructuredText
        conversion.  We need to undo some of those, especially when we have
        ``:py:obj:`` style references.

        Args:
            documentation: input documentation

        Returns:
            Cleaned up documentation.

        """
        for match in self.PY_OBJECT_RE.finditer(documentation):
            py_obj = match.group(0)
            updated_py_obj = py_obj.replace("``", "`")
            documentation = documentation.replace(py_obj, updated_py_obj)
        return documentation

    def clean(self, documentation: str, max_lines: int | None = None) -> str:
        """
        Take the input documentation in HTML format and clean it up for use in a
        docstring, as reStructuredText.

        Args:
            documentation: the HTML documentation to clean up

        Keyword Args:
            max_lines: the maximum number of lines to include in the output

        Returns:
            Properly formatted reStructuredText documentation.

        """
        documentation = markdownify(documentation)
        if max_lines is not None:
            documentation = "\n".join(documentation.split("\n")[:max_lines])
        if "\n" in documentation:
            documentation = "\n".join(
                [line.strip() for line in documentation.split("\n")]
            )
        documentation = documentation.replace("`", "``")
        documentation = self._clean_uls(documentation)
        documentation = self._clean_links(documentation)
        documentation = self._undo_double_backticks(documentation)
        # remove any double backslashes
        documentation = re.sub(r"\\{1}", "", documentation)
        # Change en-dashes to hyphens
        documentation = documentation.replace("–", "-")  # noqa: RUF001
        # Change forward ticks to backticks
        return documentation.replace("‘", "`")  # noqa: RUF001

    def format_docstring(self, documentation: str) -> str:
        """
        Format the documentation for a model.

        Args:
            documentation: the documentation for the model

        Returns:
            The formatted documentation for the model as reStructuredText.

        """
        documentation = self.clean(documentation)
        return documentation  # noqa: RET504

    def format_attribute(self, docs: str) -> str:
        """
        Format the documentation for a single attribute of a model.

        Args:
            docs: the documentation for the attribute

        Returns:
            The formatted documentation for the attribute as reStructuredText.

        """
        documentation = self.clean(docs, max_lines=1)
        docs = '    """\n'
        docs += documentation
        docs += '\n    """'
        return docs

    def format_argument(self, arg: str, docs: str | None) -> str:
        """
        Format the documentation for a single argument of a method.

        Args:
            arg: the name of the argument
            docs: the documentation for the argument

        Returns:
            The formatted documentation for the argument as reStructuredText.

        """
        if not docs:
            docs = f"the value to set for {arg}"
        documentation = self.clean(docs, max_lines=1)
        lines = wrap(f"{arg}: {documentation}", self.max_length - 4)
        lines[0] = f"            {lines[0]}"
        for i, line in enumerate(lines[1:]):
            lines[i + 1] = f"                {line}"
        lines[-1] += "\n"
        return "\n".join([line.rstrip() for line in lines])
    #: Regex for section headers that docformatter can collapse onto one line.
