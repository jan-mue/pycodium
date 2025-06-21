"""Custom component for the Monaco editor.

Props are documented here: https://github.com/suren-atoyan/monaco-react?tab=readme-ov-file#props
"""

import reflex as rx
from reflex.utils import imports
from typing_extensions import override

from pycodium.models.monaco import CompletionItem, CompletionRequest, HoverRequest


class MonacoEditor(rx.Component):
    """Monaco editor component."""

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

    # Completion items from state
    completion_items: rx.Var[list[CompletionItem]] = rx.Var.create([])

    # Triggered when the editor value changes.
    on_change: rx.EventHandler[rx.event.passthrough_event_spec(str)]

    # Triggered when the content is validated. (limited to some languages)
    on_validate: rx.EventHandler[rx.event.passthrough_event_spec(str)]

    # Triggered when a completion request is made.
    on_completion_request: rx.EventHandler[rx.event.passthrough_event_spec(CompletionRequest)]

    # Triggered when a hover request is made.
    on_hover_request: rx.EventHandler[rx.event.passthrough_event_spec(HoverRequest)]

    @override
    def add_imports(self) -> imports.ImportDict:
        """Add the imports for the component."""
        return {
            "react": [imports.ImportVar(tag="useEffect"), imports.ImportVar(tag="useRef")],
            "@monaco-editor/react": [imports.ImportVar(tag="useMonaco")],
        }

    @override
    def add_hooks(self) -> list[str | rx.Var[str]]:
        """Add hooks for LSP event handling with state-based completions."""
        return [
            f"""
                const monaco = useMonaco();
                const completionProviderRef = useRef(null);
                const hoverProviderRef = useRef(null);
                const pendingCompletionRef = useRef(null);

                // Setup Monaco when available
                useEffect(() => {{
                    if (monaco) {{
                        // Register Python language if not already registered
                        if (!monaco.languages.getLanguages().find(lang => lang.id === 'python')) {{
                            monaco.languages.register({{
                                id: 'python',
                                extensions: ['.py'],
                                aliases: ['PYTHON', 'python', 'py'],
                            }});
                        }}

                        // Handle completion requests
                        const handleCompletionRequest = {rx.Var.create(self.event_triggers["on_completion_request"])!s};

                        // Handle hover requests
                        const handleHoverRequest = {rx.Var.create(self.event_triggers["on_hover_request"])!s};

                        // Register completion provider
                        if (completionProviderRef.current) {{
                            completionProviderRef.current.dispose();
                        }}

                        completionProviderRef.current = monaco.languages.registerCompletionItemProvider('python', {{
                            provideCompletionItems: async (model, position) => {{
                                return new Promise((resolve) => {{
                                    const text = model.getValue();
                                    const completionData = {{
                                        text: text,
                                        position: {{
                                            line: position.lineNumber - 1,  // Convert to 0-based
                                            column: position.column - 1
                                        }},
                                        file_path: model.uri ? model.uri.toString() : null
                                    }};

                                    // Store the resolve function for later use
                                    pendingCompletionRef.current = resolve;

                                    // Trigger Python event handler
                                    handleCompletionRequest(completionData);

                                    // Set a timeout fallback in case state doesn't update
                                    setTimeout(() => {{
                                        if (pendingCompletionRef.current === resolve) {{
                                            pendingCompletionRef.current = null;
                                            resolve({{
                                                suggestions: [
                                                    {{
                                                        label: 'print',
                                                        kind: monaco.languages.CompletionItemKind.Function,
                                                        insertText: 'print(${{1}})',
                                                        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                                                        documentation: 'Print function'
                                                    }}
                                                ]
                                            }});
                                        }}
                                    }}, 1000); // 1 second timeout
                                }});
                            }}
                        }});

                        // Register hover provider
                        if (hoverProviderRef.current) {{
                            hoverProviderRef.current.dispose();
                        }}

                        hoverProviderRef.current = monaco.languages.registerHoverProvider('python', {{
                            provideHover: async (model, position) => {{
                                const text = model.getValue();
                                const hoverData = {{
                                    text: text,
                                    position: {{
                                        line: position.lineNumber - 1,
                                        column: position.column - 1
                                    }},
                                    file_path: model.uri ? model.uri.toString() : null
                                }};

                                // Trigger Python event handler
                                handleHoverRequest(hoverData);

                                // Return basic hover info
                                const word = model.getWordAtPosition(position);
                                if (word) {{
                                    return {{
                                        range: new monaco.Range(position.lineNumber, word.startColumn, position.lineNumber, word.endColumn),
                                        contents: [{{
                                            value: `**${{word.word}}**\\n\\nPython identifier`
                                        }}]
                                    }};
                                }}
                                return null;
                            }}
                        }});
                    }}

                    // Cleanup on unmount
                    return () => {{
                        if (completionProviderRef.current) {{
                            completionProviderRef.current.dispose();
                        }}
                        if (hoverProviderRef.current) {{
                            hoverProviderRef.current.dispose();
                        }}
                        pendingCompletionRef.current = null;
                    }};
                }}, [monaco]);

                // Watch for completion_items changes and resolve pending completion requests
                useEffect(() => {{
                    if (pendingCompletionRef.current && {self.completion_items!s}) {{
                        const resolve = pendingCompletionRef.current;
                        pendingCompletionRef.current = null;

                        const suggestions = {self.completion_items!s}.map(item => ({{
                            label: item.label,
                            kind: item.kind || monaco?.languages?.CompletionItemKind?.Text || 1,
                            insertText: item.insert_text || item.label,
                            insertTextRules: item.insert_text && item.insert_text.includes('${{')
                                ? monaco?.languages?.CompletionItemInsertTextRule?.InsertAsSnippet
                                : undefined,
                            documentation: item.documentation || '',
                            detail: item.detail || ''
                        }}));

                        resolve({{
                            suggestions: suggestions
                        }});
                    }}
                }}, [{self.completion_items!s}]);
                """
        ]


monaco = MonacoEditor.create
