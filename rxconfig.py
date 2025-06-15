"""Configuration for the Reflex application."""

import reflex as rx

config = rx.Config(
    app_name="pycodium",
    telemetry_enabled=False,
    show_built_with_reflex=False,
    plugins=[rx.plugins.TailwindV3Plugin()],  # type: ignore[reportPrivateImportUsage]
)
