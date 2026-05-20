from botocraft.sync.service import resolve_list_forward_ref_shadowing


class TestResolveListForwardRefShadowing:
    def test_creates_alias_when_field_name_shadows_list_item(self) -> None:
        python_type, alias_line = resolve_list_forward_ref_shadowing(
            "VpnConnection",
            "VgwTelemetry",
            '"builtins.list[VgwTelemetry]"',
        )
        assert python_type == '"builtins.list[VpnConnectionVgwTelemetry]"'
        assert alias_line == "VpnConnectionVgwTelemetry = VgwTelemetry"

    def test_creates_alias_for_optional_list_types(self) -> None:
        python_type, alias_line = resolve_list_forward_ref_shadowing(
            "DescribeDhcpOptionsResult",
            "DhcpOptions",
            '"builtins.list[DhcpOptions] | None"',
        )
        expected = '"builtins.list[DescribeDhcpOptionsResultDhcpOptions] | None"'
        assert python_type == expected
        assert alias_line == "DescribeDhcpOptionsResultDhcpOptions = DhcpOptions"

    def test_leaves_unrelated_names_unchanged(self) -> None:
        original = '"builtins.list[VpnStaticRoute]"'
        python_type, alias_line = resolve_list_forward_ref_shadowing(
            "VpnConnection",
            "Routes",
            original,
        )
        assert python_type == original
        assert alias_line is None
