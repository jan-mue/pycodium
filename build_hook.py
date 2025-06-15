"""Build hook for exporting the Reflex frontend during the build process."""

from __future__ import annotations

from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from reflex import constants
from reflex.config import environment
from reflex.utils import prerequisites
from reflex.utils.export import export
from typing_extensions import override


class ReflexBuildHook(BuildHookInterface[Any]):
    """A build hook for exporting the Reflex frontend during the build process."""

    @override
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        self.app.display_info(f"Build data: {build_data!s}")
        self.app.display_info(f"Project root: {self.root}")
        self.app.display_info(f"Build dir: {self.directory}")

        if version == "editable":
            self.app.display_info("Skipping Reflex export for editable build.")
            return super().initialize(version, build_data)

        environment.REFLEX_COMPILE_CONTEXT.set(constants.CompileContext.EXPORT)

        if prerequisites.needs_reinit():
            self.app.display_info("Initializing Reflex user directory and frontend dependencies...")
            prerequisites.initialize_reflex_user_directory()
            prerequisites.initialize_frontend_dependencies()

        self.app.display_info("Exporting Reflex frontend ...")
        export(zipping=False, frontend=True, backend=False, zip_dest_dir=self.directory, env=constants.Env.PROD)
        self.app.display_info("Successfully exported Reflex frontend.")
        return super().initialize(version, build_data)
