from argparse import Namespace

import pytest

from botocraft.sync.docstring import FormatterArgs

WRAP_COLUMN = 88


def test_formatter_args_cover_docformatter_runtime_fields() -> None:
    args = FormatterArgs()

    for field_name in (
        "check",
        "close_quotes_on_newline",
        "diff",
        "exclude",
        "files",
        "in_place",
        "pre_summary_space",
        "recursive",
    ):
        assert hasattr(args, field_name)


def test_code_docstring_formatter_formats_short_docstring() -> None:
    from botocraft.sync.docstring import CodeDocstringFormatter

    formatter = CodeDocstringFormatter()
    code = 'def f():\n    """hello world"""\n    pass\n'

    formatted = formatter.format_code(code)

    assert formatted == 'def f():\n    """\n    Hello world.\n    """\n    pass\n'


def test_code_docstring_formatter_formats_wrapped_docstring() -> None:
    from botocraft.sync.docstring import CodeDocstringFormatter

    formatter = CodeDocstringFormatter()
    code = 'def f():\n    """' + ("word " * 40).strip() + '"""\n    pass\n'

    formatted = formatter.format_code(code)

    assert '    """\n' in formatted
    assert "Word word word" in formatted
    assert formatted.endswith("    pass\n")


def test_code_docstring_formatter_preserves_args_section_while_wrapping() -> None:
    from botocraft.sync.docstring import CodeDocstringFormatter

    formatter = CodeDocstringFormatter()
    code = (
        'def f(long_argument_name: str) -> None:\n'
        '    """This sentence is intentionally very long so the formatter must '
        "wrap it without collapsing the Args section into a single malformed "
        'line.\n\n'
        "    Args:\n"
        "        long_argument_name: This argument description is also "
        "intentionally long so it needs wrapping but must remain attached to "
        'the right indentation level.\n'
        '    """\n'
        "    pass\n"
    )

    formatted = formatter.format_code(code)

    assert "\n    Args:\n" in formatted
    assert "Args:        " not in formatted
    assert "        long_argument_name:" in formatted


def test_code_docstring_formatter_indents_existing_args_continuation_lines() -> None:
    from botocraft.sync.docstring import CodeDocstringFormatter

    formatter = CodeDocstringFormatter()
    code = (
        'def get(CertificateArn: str) -> None:\n'
        '    """Returns detailed metadata about the specified ACM certificate.\n\n'
        "    Args:\n"
        "        CertificateArn: The Amazon Resource Name (ARN) of the ACM "
        "certificate. The\n"
        "        ARN must have the following form:\n"
        '    """\n'
        "    pass\n"
    )

    formatted = formatter.format_code(code)

    assert "        CertificateArn:" in formatted
    assert "\n            ARN must have the following form:\n" in formatted
    assert "\n        ARN must have the following form:\n" not in formatted


def test_code_docstring_formatter_prefers_new_private_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from botocraft.sync import docstring as docstring_module

    class FakeFormatter:
        def __init__(
            self,
            args: FormatterArgs,
            stderror: None,
            stdin: None,
            stdout: None,
        ) -> None:
            self.args = args
            self.stderror = stderror
            self.stdin = stdin
            self.stdout = stdout

        def _do_format_code(self, source: str) -> str:
            return f"new:{source}"

        def _format_code(self, source: str) -> str:
            return f"old:{source}"

    monkeypatch.setattr(docstring_module, "Formatter", FakeFormatter)

    formatter = docstring_module.CodeDocstringFormatter()

    assert formatter.format_code("x") == "new:x"


def test_code_docstring_formatter_falls_back_to_old_private_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from botocraft.sync import docstring as docstring_module

    class FakeFormatter:
        def __init__(
            self,
            args: FormatterArgs,
            stderror: None,
            stdin: None,
            stdout: None,
        ) -> None:
            self.args = args
            self.stderror = stderror
            self.stdin = stdin
            self.stdout = stdout

        def _format_code(self, source: str) -> str:
            return f"old:{source}"

    monkeypatch.setattr(docstring_module, "Formatter", FakeFormatter)

    formatter = docstring_module.CodeDocstringFormatter()

    assert formatter.format_code("x") == "old:x"


def test_code_docstring_formatter_uses_botocraft_defaults() -> None:
    from botocraft.sync.docstring import CodeDocstringFormatter

    formatter = CodeDocstringFormatter()

    args = formatter.args

    assert isinstance(args, Namespace)
    assert args.black is True
    assert args.force_wrap is False
    assert args.make_summary_multi_line is True
    assert args.pre_summary_newline is True
    assert args.post_description_blank is False
    assert args.style == "sphinx"
    assert args.wrap_summaries == WRAP_COLUMN
    assert args.wrap_descriptions == WRAP_COLUMN
