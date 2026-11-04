from botocraft.sync.models import BotocraftInterface
from botocraft.sync.service import ServiceGenerator


def test_generated_imports_are_sorted() -> None:
    """
    Generated imports must not depend on set iteration order, or every sync
    rewrites the import block of every service file.
    """
    interface = BotocraftInterface()
    interface.load()
    generator = ServiceGenerator(interface.services["acm"])
    generator.imports = {"import zeta", "import alpha", "import mid"}

    code = generator.code

    assert code.index("import alpha") < code.index("import mid")
    assert code.index("import mid") < code.index("import zeta")
