"""LSP client for interacting with the basedpyright language server."""

import asyncio
import contextlib
import json
import logging
from typing import Any, cast


class BasedPyrightLSPClient:
    """Client for interacting with the basedpyright LSP server."""

    def __init__(self, server_path: str = "basedpyright-langserver", python_path: str | None = None) -> None:
        """Initialize the BasedPyrightLSPClient."""
        self.server_path = server_path
        self.python_path = python_path
        self.process: asyncio.subprocess.Process | None = None
        self.request_id = 0
        self.documents: dict[str, tuple[int, str]] = {}
        self.diagnostics: dict[str, list[dict[str, Any]]] = {}
        self.diagnostic_events: dict[str, asyncio.Event] = {}
        # TODO: improve type annotation for futures
        self.pending_requests: dict[int, asyncio.Future[Any]] = {}
        self.logger = logging.getLogger(__name__)

    async def start_server(self) -> None:
        """Start the basedpyright LSP server process."""
        try:
            # Start the basedpyright language server with stdio
            self.process = await asyncio.create_subprocess_exec(
                self.server_path,
                "--stdio",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Start the response handler
            asyncio.create_task(self._handle_responses())  # noqa: RUF006

            # Send initialize request
            await self._initialize()

            self.logger.info("basedpyright LSP server started successfully")

        except (OSError, RuntimeError, asyncio.TimeoutError, asyncio.CancelledError):
            self.logger.exception("Failed to start basedpyright server")
            await self._terminate_process()
            raise

    async def _terminate_process(self) -> None:
        """Reap the child even if initialization or protocol shutdown failed."""
        process = self.process
        if process is None:
            return
        if process.returncode is None:
            with contextlib.suppress(ProcessLookupError):
                process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.logger.warning("Language server ignored termination; killing it")
                with contextlib.suppress(ProcessLookupError):
                    process.kill()
                await asyncio.wait_for(process.wait(), timeout=5)
        self.process = None
        self.documents.clear()
        self.diagnostics.clear()
        self.diagnostic_events.clear()

    async def stop_server(self) -> None:
        """Attempt protocol shutdown and always reap the language server."""
        if self.process is None:
            return
        try:
            await self._send_request("shutdown", None)
            await self._send_notification("exit", None)
            await asyncio.wait_for(self.process.wait(), timeout=5)
        except (OSError, RuntimeError, asyncio.TimeoutError):
            self.logger.warning("Language server protocol shutdown failed", exc_info=True)
        finally:
            await self._terminate_process()
        self.logger.info("basedpyright LSP server stopped")

    async def get_completions(self, uri: str, line: int, character: int) -> list[dict[str, Any]]:
        """Get code completions at the specified position."""
        params = {"textDocument": {"uri": uri}, "position": {"line": line, "character": character}}

        response = await self._send_request("textDocument/completion", params)
        if isinstance(response, dict) and "items" in response:
            return response["items"]
        elif isinstance(response, list):
            return response
        return []

    async def get_hover_info(self, uri: str, line: int, character: int) -> dict[str, Any] | None:
        """Get hover information at the specified position."""
        params = {"textDocument": {"uri": uri}, "position": {"line": line, "character": character}}
        return cast(dict[str, Any] | None, await self._send_request("textDocument/hover", params))

    async def get_references(
        self, uri: str, line: int, character: int, include_declaration: bool = True
    ) -> list[dict[str, Any]]:
        """Get all references to the symbol at the specified position."""
        params = {
            "textDocument": {"uri": uri},
            "position": {"line": line, "character": character},
            "context": {"includeDeclaration": include_declaration},
        }
        response = await self._send_request("textDocument/references", params)
        if isinstance(response, list):
            return response
        return []

    async def get_declaration(self, uri: str, line: int, character: int) -> dict[str, Any] | None:
        """Get the declaration of the symbol at the specified position."""
        params = {"textDocument": {"uri": uri}, "position": {"line": line, "character": character}}
        return cast(dict[str, Any] | None, await self._send_request("textDocument/declaration", params))

    async def get_definition(self, uri: str, line: int, character: int) -> list[dict[str, Any]]:
        """Get the definition of the symbol at the specified position."""
        params = {"textDocument": {"uri": uri}, "position": {"line": line, "character": character}}
        response = await self._send_request("textDocument/definition", params)
        if isinstance(response, list):
            return response
        elif isinstance(response, dict):
            return [response]
        return []

    async def get_signature_help(self, uri: str, line: int, character: int) -> dict[str, Any] | None:
        """Get signature help at the specified position.

        Typically triggered when typing '(' or ',' in a function call.
        """
        params = {"textDocument": {"uri": uri}, "position": {"line": line, "character": character}}
        return cast(dict[str, Any] | None, await self._send_request("textDocument/signatureHelp", params))

    async def rename_symbol(self, uri: str, line: int, character: int, new_name: str) -> dict[str, Any] | None:
        """Rename a symbol at the specified position.

        Returns a WorkspaceEdit that describes the changes to be made.
        """
        params = {
            "textDocument": {"uri": uri},
            "position": {"line": line, "character": character},
            "newName": new_name,
        }
        response = await self._send_request("textDocument/rename", params)
        return cast(dict[str, Any] | None, response)

    async def prepare_rename(self, uri: str, line: int, character: int) -> dict[str, Any] | None:
        """Prepare a rename operation at the specified position.

        Returns the range of the symbol to be renamed, or null if renaming is not allowed.
        """
        params = {"textDocument": {"uri": uri}, "position": {"line": line, "character": character}}
        return cast(dict[str, Any] | None, await self._send_request("textDocument/prepareRename", params))

    async def open_document(self, uri: str, content: str, language_id: str = "python") -> None:
        """Open a document in the server."""
        previous = self.documents.get(uri)
        if previous and previous[1] == content:
            return
        version = previous[0] + 1 if previous else 1
        self.documents[uri] = (version, content)
        self.diagnostic_events.setdefault(uri, asyncio.Event()).clear()
        if previous:
            await self._send_notification(
                "textDocument/didChange",
                {"textDocument": {"uri": uri, "version": version}, "contentChanges": [{"text": content}]},
            )
        else:
            await self._send_notification(
                "textDocument/didOpen",
                {"textDocument": {"uri": uri, "languageId": language_id, "version": version, "text": content}},
            )

    async def get_diagnostics(self, uri: str) -> list[dict[str, Any]]:
        """Wait for diagnostics for the latest document content."""
        event = self.diagnostic_events.setdefault(uri, asyncio.Event())
        try:
            await asyncio.wait_for(event.wait(), timeout=10)
        except asyncio.TimeoutError:
            self.logger.warning("Timed out waiting for diagnostics for %s", uri)
        return self.diagnostics.get(uri, [])

    async def close_document(self, uri: str) -> None:
        """Close a document in the server."""
        self.documents.pop(uri, None)
        self.diagnostics.pop(uri, None)
        self.diagnostic_events.pop(uri, None)
        params = {"textDocument": {"uri": uri}}
        await self._send_notification("textDocument/didClose", params)

    async def _initialize(self) -> None:
        """Send the initialize request to the server."""
        params = {
            "processId": None,
            "clientInfo": {"name": "PyCodiumLSPClient", "version": "1.0.0"},
            "capabilities": {
                "textDocument": {
                    "completion": {
                        "completionItem": {"snippetSupport": True, "documentationFormat": ["markdown", "plaintext"]}
                    },
                    "hover": {"contentFormat": ["markdown", "plaintext"]},
                    "references": {"dynamicRegistration": False},
                    "rename": {"prepareSupport": True},
                    "signatureHelp": {"signatureInformation": {"documentationFormat": ["markdown", "plaintext"]}},
                    "declaration": {"dynamicRegistration": False, "linkSupport": True},
                }
            },
            "workspaceFolders": None,
        }

        await self._send_request("initialize", params)
        await self._send_notification("initialized", {})
        if self.python_path:
            await self._send_notification(
                "workspace/didChangeConfiguration", {"settings": {"python": {"pythonPath": self.python_path}}}
            )

    async def _send_request(
        self, method: str, params: dict[str, Any] | None
    ) -> dict[str, Any] | list[dict[str, Any]] | None:
        """Send a JSON-RPC request and wait for response."""
        if not self.process or not self.process.stdin:
            raise RuntimeError("Server not started")

        self.request_id += 1
        request_id = self.request_id

        # TODO: improve type hint for message
        message: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}

        # Only add params if not None
        if params is not None:
            message["params"] = params

        # Create future for response
        future = asyncio.Future()
        self.pending_requests[request_id] = future

        # Send request
        await self._write_message(message)

        try:
            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=30.0)
            return response
        finally:
            self.pending_requests.pop(request_id, None)

    async def _send_notification(self, method: str, params: dict[str, Any] | None) -> None:
        """Send a JSON-RPC notification (no response expected)."""
        if not self.process or not self.process.stdin:
            raise RuntimeError("Server not started")

        # TODO: improve type hint for message
        message: dict[str, Any] = {"jsonrpc": "2.0", "method": method}

        if params is not None:
            message["params"] = params

        await self._write_message(message)

    async def _write_message(self, message: dict[str, Any]) -> None:
        """Write a JSON-RPC message to the server."""
        if not self.process or not self.process.stdin:
            raise RuntimeError("Server not started")

        content = json.dumps(message, separators=(",", ":"))
        content_bytes = content.encode("utf-8")

        header = f"Content-Length: {len(content_bytes)}\r\n\r\n"
        full_message = header.encode("utf-8") + content_bytes

        self.process.stdin.write(full_message)
        await self.process.stdin.drain()

    async def _handle_responses(self) -> None:
        """Handle responses from the server."""
        if not self.process or not self.process.stdout:
            return

        buffer = b""

        while True:
            data = await self.process.stdout.read(4096)
            if not data:
                break

            buffer += data

            while True:
                # Look for Content-Length header
                if b"\r\n\r\n" not in buffer:
                    break

                header_end = buffer.find(b"\r\n\r\n")
                header = buffer[:header_end].decode("utf-8")

                # Parse Content-Length
                content_length = None
                for line in header.split("\r\n"):
                    if line.startswith("Content-Length:"):
                        content_length = int(line.split(":", 1)[1].strip())
                        break

                if content_length is None:
                    self.logger.error("No Content-Length header found")
                    buffer = buffer[header_end + 4 :]
                    continue

                    # Check if we have the full message
                message_start = header_end + 4
                if len(buffer) < message_start + content_length:
                    break

                    # Extract and process message
                message_bytes = buffer[message_start : message_start + content_length]
                buffer = buffer[message_start + content_length :]

                try:
                    message = json.loads(message_bytes.decode("utf-8"))
                    await self._process_message(message)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to decode JSON message: {e}")

    async def _process_message(self, message: dict[str, Any]) -> None:
        """Process a message from the server."""
        if "id" in message:
            # This is a response to a request
            request_id = message["id"]
            if request_id in self.pending_requests:
                future = self.pending_requests[request_id]
                if future.done():
                    return
                if "error" in message:
                    future.set_exception(RuntimeError(f"LSP Error: {message['error']}"))
                else:
                    future.set_result(message.get("result"))
        else:
            # This is a notification from the server
            method = message.get("method")
            if method == "textDocument/publishDiagnostics":
                params = message["params"]
                uri = params["uri"]
                version = params.get("version")
                if version is None or version == self.documents.get(uri, (None, ""))[0]:
                    self.diagnostics[uri] = params.get("diagnostics", [])
                    self.diagnostic_events.setdefault(uri, asyncio.Event()).set()
            if method:
                self.logger.debug(f"Received notification: {method}")


lsp_client: BasedPyrightLSPClient | None = None


async def get_lsp_client() -> BasedPyrightLSPClient:
    """Get the singleton instance of the BasedPyrightLSPClient."""
    global lsp_client  # noqa: PLW0603
    if lsp_client is None:
        candidate = BasedPyrightLSPClient()
        await candidate.start_server()
        lsp_client = candidate
    return lsp_client
