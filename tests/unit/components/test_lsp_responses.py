"""Empty and repeated responses must complete the corresponding browser request."""

from typing import Any

import pytest

from pycodium.state import EditorState


@pytest.mark.parametrize(
    ("feature", "response"),
    [
        ("completion", "completion_response"),
        ("hover", "hover_info"),
        ("declaration", "declaration_response"),
        ("signature_help", "signature_help_response"),
        ("reference", "reference_response"),
        ("prepare_rename", "prepare_rename_response"),
        ("rename", "rename_response"),
    ],
)
async def test_repeated_empty_results_keep_request_id(feature: str, response: str) -> None:
    state = EditorState()
    for request_id in ("first", "second"):
        request: dict[str, Any] = {
            "request_id": request_id,
            "text": "",
            "position": {"line": 0, "column": 0},
            "file_path": None,
        }
        await getattr(state, f"handle_{feature}_request")(request)
        assert getattr(state, response)["request_id"] == request_id
