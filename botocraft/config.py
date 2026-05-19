"""Runtime configuration for handwritten botocraft features."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import TomlConfigSettingsSource


class TunnelSettings(BaseModel):
    """
    Store tunnel-resolution settings for private AWS resources.

    Args:
        enabled: Whether tunnel-aware endpoint resolution is enabled.
        tunnel_host_tag_key: EC2 tag key used to identify tunnel host instances.
        tunnel_host_tag_value: EC2 tag value used to identify tunnel host instances.
        ready_timeout_seconds: Maximum time to wait for a forwarded local port to
            become reachable.

    """

    #: Whether tunnel-aware endpoint resolution should attempt SSM forwarding.
    enabled: bool = True
    #: EC2 tag key used to discover tunnel host instances in a target VPC.
    tunnel_host_tag_key: str = "Purpose"
    #: EC2 tag value used to discover tunnel host instances in a target VPC.
    tunnel_host_tag_value: str = "provisioner"
    #: Maximum number of seconds to wait for a local forwarded port to open.
    ready_timeout_seconds: int = 10


class BotocraftSettings(BaseSettings):
    """
    Store env-backed and TOML-backed runtime configuration for ``botocraft``.

    Configuration is loaded in the following order of precedence:

    1. Initialization arguments
    2. Environment variables
    3. TOML configuration file
    4. Default values

    Environment variables use the ``BOTOCRAFT_`` prefix and ``__`` nested
    delimiter. By default the TOML file path is ``~/.botocraft.toml``. Set
    ``BOTOCRAFT_CONFIG_FILE`` to load a different TOML file.

    Args:
        tunnel: Nested tunnel-aware connection settings.

    """

    #: Runtime settings that control tunnel-aware endpoint resolution.
    tunnel: TunnelSettings = TunnelSettings()

    #: Pydantic settings configuration for env-backed and nested values.
    model_config = SettingsConfigDict(
        env_prefix="BOTOCRAFT_",
        env_nested_delimiter="__",
        extra="ignore",
        case_sensitive=False,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings,
        env_settings,
        dotenv_settings,  # noqa: ARG003
        file_secret_settings,
    ):
        """
        Customize configuration sources for runtime settings.

        Args:
            settings_cls: Settings class being initialized.
            init_settings: Initialization-argument source.
            env_settings: Environment-variable source.
            dotenv_settings: Dotenv-file source.
            file_secret_settings: File-secret source.

        Returns:
            Tuple of settings sources in descending precedence order.

        """
        config_file = os.getenv("BOTOCRAFT_CONFIG_FILE")
        if config_file:
            toml_file = Path(config_file).expanduser()
        else:
            toml_file = Path.home() / ".botocraft.toml"

        return (
            init_settings,
            env_settings,
            TomlConfigSettingsSource(
                settings_cls,
                toml_file if toml_file.exists() else None,
            ),
            file_secret_settings,
        )
