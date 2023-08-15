from typing import Dict, cast

import botocore.model


class AbstractShapeConverter:

    def to_python(self, value: botocore.model.Shape) -> str:
        raise NotImplementedError


class StringShapeConverter(AbstractShapeConverter):

    def to_python(self, value: botocore.model.Shape) -> str:
        if value.type_name == 'string' or value.name == 'String':
            value = cast(botocore.model.StringShape, value)
            if value.enum:
                contents = ', '.join([f"'{value}'" for value in value.enum])
                python_type = f'Literal[{contents}]'
            else:
                python_type = 'str'
            return python_type
        raise ValueError(f'Not string type: {value.type_name}')


class BooleanShapeConverter(AbstractShapeConverter):

    def to_python(self, value: botocore.model.Shape) -> str:
        if value.type_name == 'boolean':
            return 'bool'
        raise ValueError(f'Not boolean type: {value.type_name}')


class IntegerShapeConverter(AbstractShapeConverter):

    def to_python(self, value: botocore.model.Shape) -> str:
        if value.type_name in ['integer', 'long']:
            return 'int'
        raise ValueError(f'Not integer type: {value.type_name}')


class DoubleShapeConverter(AbstractShapeConverter):

    def to_python(self, value: botocore.model.Shape) -> str:
        if value.type_name == 'double':
            return 'float'
        raise ValueError(f'Not double type: {value.type_name}')


class PythonTypeShapeConverter:

    CONVERTERS: Dict[str, AbstractShapeConverter] = {
        'string': StringShapeConverter(),
        'boolean': BooleanShapeConverter(),
        'integer': IntegerShapeConverter(),
        'double': DoubleShapeConverter(),
    }

    def convert(self, value: botocore.model.Shape) -> str:
        for converter in self.CONVERTERS.values():
            try:
                return converter.to_python(value)
            except ValueError:
                pass
        raise ValueError(f'No converter for {value.type_name}')
