"""Custom component for the Monaco editor with LSP support.

Props are documented here: https://github.com/suren-atoyan/monaco-react?tab=readme-ov-file#props
"""

import reflex as rx
from reflex.constants import Hooks
from reflex.vars.base import Var, VarData
from typing_extensions import override


class MonacoEditor(rx.Component):
    """Monaco editor component with LSP support."""

    library = "@monaco-editor/react@4.7.0"
    tag = "MonacoEditor"

    is_default = True

    # Value to display in the editor.
    value: rx.Var[str]

    # Language to use in the editor.
    language: rx.Var[str]

    # Path to the file in the editor.
    path: rx.Var[str]

    # The theme to use for the editor.
    theme: rx.Var[str] = rx.color_mode_cond("light", "vs-dark")

    # The line to jump to in the editor.
    line: rx.Var[int] = rx.Var.create(1)

    # The width of the editor (default 100%).
    width: rx.Var[str]

    # The height of the editor (default 100%).
    height: rx.Var[str]

    # The default value to display in the editor.
    default_value: rx.Var[str]

    # The default language to use for the editor.
    default_language: rx.Var[str]

    # The path to the default file to load in the editor.
    default_path: rx.Var[str]

    # Triggered when the editor value changes.
    on_change: rx.EventHandler[rx.event.passthrough_event_spec(str)]

    # Triggered when the content is validated. (limited to some languages)
    on_validate: rx.EventHandler[rx.event.passthrough_event_spec(str)]

    # LSP server websocket URL
    lsp_url: rx.Var[str] = rx.Var.create("ws://localhost:5000")

    @override
    def add_hooks(self) -> list[str | Var[str]]:
        hooks = []

        # Import required dependencies
        lsp_imports = Var(
            "",
            _var_data=VarData(
                imports={
                    "react": ["useEffect"],
                    "@monaco-editor/react": ["useMonaco"],
                    "monaco-languageclient": ["MonacoLanguageClient"],
                    "monaco-languageclient/lib/services": ["MonacoServices"],
                    "vscode-ws-jsonrpc": ["toSocket", "WebSocketMessageReader", "WebSocketMessageWriter"],
                    "reconnecting-websocket": ["default as ReconnectingWebSocket"],
                    "normalize-url": ["default as normalizeUrl"],
                }
            ),
        )
        hooks.append(lsp_imports)

        # LSP connection hook
        lsp_hook = Var(
            f"""
            const monaco = useMonaco();

            // Language client creation function
            const createLanguageClient = (transports) => {{
                return new MonacoLanguageClient({{
                    name: 'Python Language Client',
                    clientOptions: {{
                        documentSelector: ['python'],
                        errorHandler: {{
                            error: () => ({{ action: 1 }}), // ErrorAction.Continue
                            closed: () => ({{ action: 1 }}) // CloseAction.DoNotRestart
                        }}
                    }},
                    connectionProvider: {{
                        get: () => {{
                            return Promise.resolve(transports);
                        }}
                    }}
                }});
            }};

            // Monaco setup
            useEffect(() => {{
                if (monaco) {{
                    // Register Python language
                    monaco.languages.register({{
                        id: 'python',
                        extensions: ['.py'],
                        aliases: ['PYTHON', 'python', 'py'],
                    }});

                    // Install Monaco services
                    MonacoServices.install();
                }}
            }}, [monaco]);

            // LSP WebSocket connection
            useEffect(() => {{
                if (!monaco) return;

                console.log("Creating LSP websocket connection");

                const url = normalizeUrl({self.lsp_url});
                const socketOptions = {{
                    maxReconnectionDelay: 10000,
                    minReconnectionDelay: 1000,
                    reconnectionDelayGrowFactor: 1.3,
                    connectionTimeout: 10000,
                    maxRetries: Infinity,
                    debug: false
                }};

                const webSocket = new ReconnectingWebSocket(url, [], socketOptions);

                webSocket.onopen = () => {{
                    console.log("LSP WebSocket connected");
                    const socket = toSocket(webSocket);
                    const reader = new WebSocketMessageReader(socket);
                    const writer = new WebSocketMessageWriter(socket);
                    const languageClient = createLanguageClient({{
                        reader,
                        writer
                    }});

                    languageClient.start();
                    reader.onClose(() => languageClient.stop());
                }};

                webSocket.onerror = (error) => {{
                    console.error("LSP WebSocket error:", error);
                }};

                return () => {{
                    console.log("Closing LSP WebSocket connection");
                    webSocket.close();
                }};
            }}, [monaco, {self.lsp_url}]);
            """,
            _var_data=VarData(position=Hooks.HookPosition.PRE_TRIGGER),
        )
        hooks.append(lsp_hook)
        return hooks


monaco = MonacoEditor.create
