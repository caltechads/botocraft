from .create import CreateMethodGenerator


class UpdateMethodGenerator(CreateMethodGenerator):

    operation: str = 'update'
