class TestClassVarTypeFieldShadowing:
    def test_services_import_and_shadowed_models(self) -> None:
        from botocraft.services.codebuild import ReportGroup
        from botocraft.services.ec2 import Subnet

        assert ReportGroup.tag_class is not None
        assert Subnet.tag_class is not None
