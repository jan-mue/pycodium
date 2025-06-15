"""Configuration for the Reflex application."""

import reflex as rx

config = rx.Config(
    app_name="pycodium",
    plugins=[rx.plugins.TailwindV3Plugin()],  # type: ignore[reportPrivateImportUsage]
)
