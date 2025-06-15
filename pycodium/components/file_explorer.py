"""Defines the file explorer component."""

from __future__ import annotations

import reflex as rx
from typing_extensions import override

from pycodium.models.files import FilePath
from pycodium.state import EditorState


class FileTree(rx.ComponentState):
    """ComponentState for a file tree."""

    @classmethod
    @override
    def get_component(cls, name: str, sub_paths: list[FilePath], is_dir: bool, path: str = "") -> rx.Component:
        """Get the component instance."""
        current_path = rx.cond(path == "", name, f"{path}/{name}")

        sub_paths = rx.Var.create(sub_paths).to(list[FilePath])  # type: ignore[reportAssignmentType]

        return rx.cond(
            is_dir,
            rx.el.div(
                rx.el.div(
                    rx.cond(
                        EditorState.expanded_folders.contains(current_path),  # type: ignore[reportAttributeAccessIssue]
                        rx.icon(tag="chevron-down", size=16),
                        rx.icon(tag="chevron-right", size=16),
                    ),
                    rx.el.span(name),
                    class_name="folder-item flex items-center px-2 py-1 hover:bg-white/5 rounded cursor-pointer text-sm text-gray-300",
                    on_click=lambda: EditorState.toggle_folder(current_path),
                ),
                rx.cond(
                    EditorState.expanded_folders.contains(current_path),  # type: ignore[reportAttributeAccessIssue]
                    rx.el.div(
                        rx.foreach(
                            sub_paths,
                            lambda file_path: file_tree(
                                name=file_path.name,
                                sub_paths=file_path.sub_paths,
                                is_dir=file_path.is_dir,
                                path=current_path,
                            ),
                        ),
                        padding_left="10px",
                    ),
                ),
            ),
            rx.el.div(
                rx.icon("file", size=16, class_name="ml-1 mr-2"),
                rx.el.span(name),
                class_name=(
                    "file-item flex items-center px-2 py-1 ${getHoverClass()} rounded cursor-pointer text-sm text-gray-300",
                    rx.cond(EditorState.current_file == current_path, "file-open-explorer-focus", ""),
                ),
                on_click=lambda: EditorState.open_file(current_path),
            ),
        )


file_tree_view = FileTree.create


@rx.memo
def file_tree(name: str, sub_paths: list[FilePath], is_dir: bool, path: str = "") -> rx.Component:
    """Render a file tree item."""
    return file_tree_view(name=name, sub_paths=sub_paths, is_dir=is_dir, path=path)


def explorer() -> rx.Component:
    """The file explorer component."""
    return rx.el.div(
        rx.el.div(
            rx.el.span("Explorer"),
            rx.el.div(
                rx.el.button(
                    rx.icon("file-plus", size=14),
                    class_name="h-6 w-6",
                    title="New File",
                ),
                rx.el.button(
                    rx.icon(tag="folder-plus", size=14),
                    class_name="h-6 w-6",
                    title="New Folder",
                ),
                rx.el.button(
                    rx.icon(tag="refresh-cw", size=14),
                    class_name="h-6 w-6",
                    title="Refresh",
                ),
                class_name="flex space-x-1",
            ),
            class_name="p-2 text-xs uppercase font-bold flex justify-between items-center",
        ),
        rx.el.div(
            file_tree_view(name=EditorState.file_tree.name, sub_paths=EditorState.file_tree.sub_paths, is_dir=True),  # type: ignore[reportOptionalMemberAccess]
            class_name="mt-2",
        ),
        class_name="w-full h-full overflow-auto",
        tab_index=-1,
        data_testid="file-explorer",
    )
