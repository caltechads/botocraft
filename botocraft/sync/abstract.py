from functools import cached_property
from pathlib import Path
from typing import Dict, List, Any

import black
import black.parsing
from docformatter.format import Formatter
import yaml

from .docstring import FormatterArgs


class AbstractGenerator:

    #: The path to the data directory where our yaml configs
    #: for services are stored.
    data_path: Path = Path(__file__).parent.parent / 'data'
    subfolder: str
    data_file: str

    def __init__(self, service_name: str):
        #: The AWS service name.  Examples: ``s3``, ``ec2``, ``sqs``.
        self.service_name = service_name

    @cached_property
    def config(self) -> Dict[str, Any]:
        """
        Load the config for this service from the data directory.

        Returns:
            A dictionary of config values.
        """
        path = self.data_path / self.service_name / self.data_file
        with open(path, encoding='utf-8') as file:
            return yaml.safe_load(file)

    @cached_property
    def models(self) -> List[str]:
        return list(self.config.keys())

    def generate(self):
        raise NotImplementedError

    def write(self, code: str) -> None:
        """
        Write the generated code to the output file, and format it with black,
        and with docformatter.

        Args:
            code: the code to write to the output file.
        """
        try:
            formatted_code = black.format_str(code, mode=black.FileMode())
        except (KeyError, black.parsing.InvalidInput):
            print(code)
            raise
        formatted_code = Formatter(FormatterArgs(), None, None, None)._format_code(formatted_code)
        output_file = Path(__file__).parent.parent / self.subfolder / f'{self.service_name}.py'
        with open(output_file, 'w', encoding='utf-8') as fd:
            fd.write(formatted_code)
