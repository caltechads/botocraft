from collections import OrderedDict
from dataclasses import dataclass, field
from textwrap import wrap, indent
from typing import Optional

from botocraft.sync.docstring import DocumentationFormatter


@dataclass
class MethodDocstringDefinition:
    """
    A class to hold the different parts of the docstring for a method, and
    render them into a single sphinx-napoleon style docstring.
    """

    # The main method docstring.  This is the description of the method.
    method: Optional[str] = None
    #: The docstrings for our positional arguments
    args: OrderedDict[str, Optional[str]] = field(default_factory=OrderedDict)
    #: The docstrings for our keyword arguments
    kwargs: OrderedDict[str, Optional[str]] = field(default_factory=OrderedDict)
    #: The docstring for our return value
    return_value: Optional[str] = None

    @property
    def is_empty(self) -> bool:
        """
        Return ``True`` if the docstring is empty, ``False`` otherwise.
        """
        return (
            self.method is None and
            not self.args and
            not self.kwargs and
            self.return_value is None
        )

    def Args(self, formatter: DocumentationFormatter) -> str:
        """
        Return the docstring for the positional arguments.
        """
        assert self.args, "No kwargs"
        docstring = '''
        Args:
'''
        for arg_name, arg_docstring in self.args.items():
            docstring += formatter.format_argument(arg_name, arg_docstring)
            docstring += '\n'

        return docstring

    def Keyword_Args(self, formatter: DocumentationFormatter) -> str:
        """
        Return the docstring for the keyword arguments.
        """
        assert self.kwargs, "No args"
        docstring = '''
        Keyword Args:
'''
        for arg_name, arg_docstring in self.kwargs.items():
            docstring += formatter.format_argument(arg_name, arg_docstring)
            docstring += '\n'
        return docstring

    def render(self, formatter: DocumentationFormatter) -> Optional[str]:
        """
        Return the entire method docstring.
        """
        if self.is_empty:
            return None

        docstring = '''
        """
'''
        if self.method:
            method_str = formatter.clean(self.method, max_lines=1).strip()
            docstring += indent(method_str, '        ')
            docstring += '\n'
        if self.args:
            docstring += self.Args(formatter)
        if self.kwargs:
            docstring += self.Keyword_Args(formatter)
        docstring += '\n        """'
        return docstring
