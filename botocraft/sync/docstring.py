import re
from dataclasses import dataclass, field
from textwrap import wrap
from typing import List, Literal, Optional, Tuple

import botocore.model
from markdownify import markdownify


@dataclass
class FormatterArgs:
    line_range: Optional[Tuple[int, int]] = None
    length_range: Optional[Tuple[int, int]] = None
    black: bool = True
    style: Literal["sphinx", "epytext"] = "sphinx"
    force_wrap: bool = False
    make_summary_multi_line: bool = True
    pre_summary_newline: bool = True
    post_summary_newline: bool = True
    post_description_blank: bool = False
    non_strict: bool = False
    rest_section_adorns: str = r"""[!\"#$%&'()*+,-./\\:;<=>?@[]^_`{|}~]{4,}"""
    tab_width: int = 4
    wrap_summaries: int = 79
    wrap_descriptions: int = 79
    non_cap: List[str] = field(default_factory=list)


class DocumentationFormatter:
    MARKDOWN_LINK_RE = re.compile(
        r"(?:\[(?P<text>.*?)\])\((?P<link>.*?)\)", re.MULTILINE | re.DOTALL
    )
    PY_OBJECT_RE = re.compile(r"py:(.*?):``(.*?)``", re.MULTILINE | re.DOTALL)

    def __init__(self, max_length: int = 79):
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

    def clean(self, documentation: str, max_lines: Optional[int] = None) -> str:
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
        return documentation  # noqa: RET504

    def format_docstring(self, shape: botocore.model.Shape) -> str:
        """
        Format the documentation for a model.

        Args:
            shape: the botocore shape for the model

        Returns:
            The formatted documentation for the model as reStructuredText.

        """
        documentation = shape.documentation
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

    def format_argument(self, arg: str, docs: Optional[str]) -> str:
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
