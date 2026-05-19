"""Tests for botocraft runtime configuration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from botocraft.config import BotocraftSettings

DEFAULT_TIMEOUT_SECONDS = 10
CUSTOM_TIMEOUT_SECONDS = 42


class TestBotocraftSettings:
    """Verify runtime settings precedence and defaults."""

    def test_uses_default_tunnel_settings(self) -> None:
        """Use defaults when neither env vars nor TOML are present."""
        with (
            patch("botocraft.config.Path.home", return_value=Path("/nonexistent")),
            patch.dict("os.environ", {}, clear=True),
        ):
            settings = BotocraftSettings()

        assert settings.tunnel.enabled is True
        assert settings.tunnel.tunnel_host_tag_key == "Purpose"
        assert settings.tunnel.tunnel_host_tag_value == "provisioner"
        assert settings.tunnel.ready_timeout_seconds == DEFAULT_TIMEOUT_SECONDS

    def test_loads_toml_from_default_home_path(self, tmp_path: Path) -> None:
        """Load tunnel settings from ``~/.botocraft.toml`` when present."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        (fake_home / ".botocraft.toml").write_text(
            """
[tunnel]
enabled = false
tunnel_host_tag_key = "Role"
tunnel_host_tag_value = "jump-host"
ready_timeout_seconds = 42
""".strip(),
            encoding="utf-8",
        )

        with (
            patch("botocraft.config.Path.home", return_value=fake_home),
            patch.dict("os.environ", {}, clear=True),
        ):
            settings = BotocraftSettings()

        assert settings.tunnel.enabled is False
        assert settings.tunnel.tunnel_host_tag_key == "Role"
        assert settings.tunnel.tunnel_host_tag_value == "jump-host"
        assert settings.tunnel.ready_timeout_seconds == CUSTOM_TIMEOUT_SECONDS

    def test_environment_variables_override_toml(self, tmp_path: Path) -> None:
        """Prefer environment variables over TOML values."""
        config_file = tmp_path / "botocraft.toml"
        config_file.write_text(
            """
[tunnel]
tunnel_host_tag_key = "Role"
tunnel_host_tag_value = "jump-host"
""".strip(),
            encoding="utf-8",
        )

        with patch.dict(
            "os.environ",
            {
                "BOTOCRAFT_CONFIG_FILE": str(config_file),
                "BOTOCRAFT_TUNNEL__TUNNEL_HOST_TAG_KEY": "Purpose",
                "BOTOCRAFT_TUNNEL__TUNNEL_HOST_TAG_VALUE": "provisioner",
            },
            clear=True,
        ):
            settings = BotocraftSettings()

        assert settings.tunnel.tunnel_host_tag_key == "Purpose"
        assert settings.tunnel.tunnel_host_tag_value == "provisioner"

    def test_uses_explicit_config_file_override(self, tmp_path: Path) -> None:
        """Load TOML from ``BOTOCRAFT_CONFIG_FILE`` when provided."""
        config_file = tmp_path / "custom.toml"
        config_file.write_text(
            """
[tunnel]
tunnel_host_tag_key = "ManagedBy"
tunnel_host_tag_value = "provisioner-node"
""".strip(),
            encoding="utf-8",
        )

        with (
            patch("botocraft.config.Path.home", return_value=Path("/nonexistent")),
            patch.dict(
                "os.environ",
                {"BOTOCRAFT_CONFIG_FILE": str(config_file)},
                clear=True,
            ),
        ):
            settings = BotocraftSettings()

        assert settings.tunnel.tunnel_host_tag_key == "ManagedBy"
        assert settings.tunnel.tunnel_host_tag_value == "provisioner-node"
