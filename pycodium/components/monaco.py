"""Custom component for the Monaco editor.

Props are documented here: https://github.com/suren-atoyan/monaco-react?tab=readme-ov-file#props
LSP client based on https://github.com/microsoft/vscode-languageserver-node/tree/main/client
"""

from typing import Any

import reflex as rx
from reflex.utils import imports
from typing_extensions import override

from pycodium.models.monaco import (
    CompletionItem,
    CompletionRequest,
    DeclarationRequest,
    HoverRequest,
    PrepareRenameRequest,
    ReferenceRequest,
    RenameRequest,
    SignatureHelpRequest,
)


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

    # Completion response from state
    completion_response: rx.Var[dict[str, list[CompletionItem]]] = rx.Var.create({})

    # Hover info from state
    hover_info: rx.Var[dict[str, str]] = rx.Var.create({})

    # Reference response from state
    reference_response: rx.Var[dict[str, list[dict[str, Any]]]] = rx.Var.create({})

    # Declaration response from state
    declaration_response: rx.Var[dict[str, Any]] = rx.Var.create({})

    # Signature help response from state
    signature_help_response: rx.Var[dict[str, Any]] = rx.Var.create({})

    # Rename response from state
    rename_response: rx.Var[dict[str, Any]] = rx.Var.create({})

    # Prepare rename response from state
    prepare_rename_response: rx.Var[dict[str, Any]] = rx.Var.create({})

    # Triggered when the editor value changes.
    on_change: rx.EventHandler[rx.event.passthrough_event_spec(str)]

    # Triggered when the content is validated. (limited to some languages)
    on_validate: rx.EventHandler[rx.event.passthrough_event_spec(str)]

    # Triggered when a completion request is made.
    on_completion_request: rx.EventHandler[rx.event.passthrough_event_spec(CompletionRequest)]

    # Triggered when a hover request is made.
    on_hover_request: rx.EventHandler[rx.event.passthrough_event_spec(HoverRequest)]

    # Triggered when a declaration request is made.
    on_declaration_request: rx.EventHandler[rx.event.passthrough_event_spec(DeclarationRequest)]

    # Triggered when a signature help request is made.
    on_signature_help_request: rx.EventHandler[rx.event.passthrough_event_spec(SignatureHelpRequest)]

    # Triggered when a reference request is made.
    on_reference_request: rx.EventHandler[rx.event.passthrough_event_spec(ReferenceRequest)]

    # Triggered when a prepare rename request is made.
    on_prepare_rename_request: rx.EventHandler[rx.event.passthrough_event_spec(PrepareRenameRequest)]

    # Triggered when a rename request is made.
    on_rename_request: rx.EventHandler[rx.event.passthrough_event_spec(RenameRequest)]

    @override
    def add_imports(self) -> imports.ImportDict:
        """Add the imports for the component."""
        return {
            "react": [imports.ImportVar(tag="useEffect"), imports.ImportVar(tag="useRef")],
            "@monaco-editor/react": [imports.ImportVar(tag="useMonaco")],
        }

    @override
    def add_hooks(self) -> list[str | rx.Var[str]]:
        """Add hooks for LSP event handling with Promise-based completions."""
        return [
            f"""
                const monaco = useMonaco();
                const completionProviderRef = useRef(null);
                const hoverProviderRef = useRef(null);
                const declarationProviderRef = useRef(null);
                const definitionProviderRef = useRef(null);
                const signatureHelpProviderRef = useRef(null);
                const referenceProviderRef = useRef(null);
                const renameProviderRef = useRef(null);
                const pendingCompletionRef = useRef(null);
                const pendingHoverRef = useRef(null);
                const pendingDeclarationRef = useRef(null);
                const pendingSignatureHelpRef = useRef(null);
                const pendingReferenceRef = useRef(null);
                const pendingPrepareRenameRef = useRef(null);
                const pendingRenameRef = useRef(null);
                const lastCompletionItemsRef = useRef([]);
                const lastHoverInfoRef = useRef({{}});
                const lastDeclarationInfoRef = useRef([]);
                const lastSignatureHelpRef = useRef({{}});
                const lastReferenceRef = useRef([]);
                const lastPrepareRenameRef = useRef({{}});
                const lastRenameRef = useRef({{}});

                // Update refs when state changes
                useEffect(() => {{
                    const completionResponse = {self.completion_response!s};
                    const completionItems = completionResponse.items || [];
                    if (JSON.stringify(completionItems) !== JSON.stringify(lastCompletionItemsRef.current)) {{
                        lastCompletionItemsRef.current = completionItems;
                        if (pendingCompletionRef.current) {{
                            const suggestions = completionItems.map(item => ({{
                                label: item.label,
                                kind: item.kind || monaco?.languages?.CompletionItemKind?.Text || 1,
                                insertText: item.insert_text || item.label,
                                insertTextRules: item.insert_text && item.insert_text.includes('${{{{')
                                    ? monaco?.languages?.CompletionItemInsertTextRule?.InsertAsSnippet
                                    : undefined,
                                documentation: item.documentation || '',
                                detail: item.detail || ''
                            }}));
                            console.log('Resolving completion suggestions:', suggestions);
                            pendingCompletionRef.current({{ suggestions }});
                            pendingCompletionRef.current = null;
                        }}
                    }}
                }}, [{self.completion_response!s}]);

                useEffect(() => {{
                    const hoverInfo = {self.hover_info!s};
                    if (JSON.stringify(hoverInfo) !== JSON.stringify(lastHoverInfoRef.current)) {{
                        lastHoverInfoRef.current = hoverInfo;
                        if (pendingHoverRef.current) {{
                            console.log('Resolving hover info:', hoverInfo);
                            pendingHoverRef.current({{
                                contents: hoverInfo.contents ? [ {{ value: hoverInfo.contents }} ] : []
                            }});
                            pendingHoverRef.current = null;
                        }}
                    }}
                }}, [{self.hover_info!s}]);

                useEffect(() => {{
                    const declarationResponse = {self.declaration_response!s};
                    if (JSON.stringify(declarationResponse) !== JSON.stringify(lastDeclarationInfoRef.current)) {{
                        lastDeclarationInfoRef.current = declarationResponse;
                        if (pendingDeclarationRef.current) {{
                            console.log('Resolving declaration info:', declarationResponse);
                            pendingDeclarationRef.current(declarationResponse.items || []);
                            pendingDeclarationRef.current = null;
                        }}
                    }}
                }}, [{self.declaration_response!s}]);

                // Signature help response effect
                useEffect(() => {{
                    const signatureHelpResponse = {self.signature_help_response!s};
                    if (JSON.stringify(signatureHelpResponse) !== JSON.stringify(lastSignatureHelpRef.current)) {{
                        lastSignatureHelpRef.current = signatureHelpResponse;
                        if (pendingSignatureHelpRef.current) {{
                            console.log('Resolving signature help:', signatureHelpResponse);
                            pendingSignatureHelpRef.current(signatureHelpResponse.signatures ? signatureHelpResponse : null);
                            pendingSignatureHelpRef.current = null;
                        }}
                    }}
                }}, [{self.signature_help_response!s}]);

                // Reference response effect
                useEffect(() => {{
                    const referenceResponse = {self.reference_response!s};
                    if (JSON.stringify(referenceResponse) !== JSON.stringify(lastReferenceRef.current)) {{
                        lastReferenceRef.current = referenceResponse;
                        if (pendingReferenceRef.current) {{
                            console.log('Resolving references:', referenceResponse);
                            pendingReferenceRef.current(referenceResponse.items || []);
                            pendingReferenceRef.current = null;
                        }}
                    }}
                }}, [{self.reference_response!s}]);

                // Prepare rename response effect
                useEffect(() => {{
                    const prepareRenameResponse = {self.prepare_rename_response!s};
                    if (JSON.stringify(prepareRenameResponse) !== JSON.stringify(lastPrepareRenameRef.current)) {{
                        lastPrepareRenameRef.current = prepareRenameResponse;
                        if (pendingPrepareRenameRef.current) {{
                            console.log('Resolving prepare rename:', prepareRenameResponse);
                            pendingPrepareRenameRef.current(prepareRenameResponse.range ? prepareRenameResponse : null);
                            pendingPrepareRenameRef.current = null;
                        }}
                    }}
                }}, [{self.prepare_rename_response!s}]);

                // Rename response effect
                useEffect(() => {{
                    const renameResponse = {self.rename_response!s};
                    if (JSON.stringify(renameResponse) !== JSON.stringify(lastRenameRef.current)) {{
                        lastRenameRef.current = renameResponse;
                        if (pendingRenameRef.current) {{
                            console.log('Resolving rename:', renameResponse);
                            pendingRenameRef.current(renameResponse.edit || null);
                            pendingRenameRef.current = null;
                        }}
                    }}
                }}, [{self.rename_response!s}]);

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
                        // Handle go to declaration requests
                        const handleDeclarationRequest = {rx.Var.create(self.event_triggers["on_declaration_request"])!s};
                        // Handle signature help requests
                        const handleSignatureHelpRequest = {rx.Var.create(self.event_triggers["on_signature_help_request"])!s};
                        // Handle reference requests
                        const handleReferenceRequest = {rx.Var.create(self.event_triggers["on_reference_request"])!s};
                        // Handle prepare rename requests
                        const handlePrepareRenameRequest = {rx.Var.create(self.event_triggers["on_prepare_rename_request"])!s};
                        // Handle rename requests
                        const handleRenameRequest = {rx.Var.create(self.event_triggers["on_rename_request"])!s};

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
                                    console.log('Completion request sent:', completionData);

                                    // Set a timeout fallback in case state doesn't update
                                    setTimeout(() => {{
                                        if (pendingCompletionRef.current === resolve) {{
                                            pendingCompletionRef.current = null;
                                            console.log('Completion request timed out, returning empty suggestions');
                                            resolve({{
                                                suggestions: []
                                            }});
                                        }}
                                    }}, 30000); // 30 second timeout
                                }});
                            }}
                        }});

                        // Register hover provider
                        if (hoverProviderRef.current) {{
                            hoverProviderRef.current.dispose();
                        }}

                        hoverProviderRef.current = monaco.languages.registerHoverProvider('python', {{
                            provideHover: async (model, position) => {{
                                return new Promise((resolve) => {{
                                    const text = model.getValue();
                                    const hoverData = {{
                                        text: text,
                                        position: {{
                                            line: position.lineNumber - 1,
                                            column: position.column - 1
                                        }},
                                        file_path: model.uri ? model.uri.toString() : null
                                    }};

                                    // Store the resolve function for later use
                                    pendingHoverRef.current = resolve;

                                    // Trigger Python event handler
                                    handleHoverRequest(hoverData);
                                    console.log('Hover request sent:', hoverData);

                                    // Set a timeout fallback in case state doesn't update
                                    setTimeout(() => {{
                                        if (pendingHoverRef.current === resolve) {{
                                            pendingHoverRef.current = null;
                                            console.log('Hover request timed out, returning empty hover');
                                            resolve({{
                                                range: new monaco.Range(position.lineNumber, 1, position.lineNumber, model.getLineMaxColumn(position.lineNumber)),
                                                contents: []
                                            }});
                                        }}
                                    }}, 5000); // 5 second timeout
                                }});
                            }}
                        }});

                        // Register declaration provider
                        if (declarationProviderRef.current) {{
                            declarationProviderRef.current.dispose();
                        }}
                        declarationProviderRef.current = monaco.languages.registerDeclarationProvider('python', {{
                            provideDeclaration: async (model, position, token) => {{
                                return new Promise((resolve) => {{
                                    const text = model.getValue();
                                    const declarationData = {{
                                        text: text,
                                        position: {{
                                            line: position.lineNumber - 1,
                                            column: position.column - 1
                                        }},
                                        file_path: model.uri ? model.uri.toString() : null
                                    }};
                                    pendingDeclarationRef.current = resolve;
                                    handleDeclarationRequest(declarationData);
                                    console.log('Declaration request sent:', declarationData);
                                    setTimeout(() => {{
                                        if (pendingDeclarationRef.current === resolve) {{
                                            pendingDeclarationRef.current = null;
                                            console.log('Declaration request timed out, returning empty definition');
                                            resolve([]);
                                        }}
                                    }}, 10000);
                                }});
                            }}
                        }});

                        // Register definition provider (for Cmd+Click / F12)
                        if (definitionProviderRef.current) {{
                            definitionProviderRef.current.dispose();
                        }}
                        definitionProviderRef.current = monaco.languages.registerDefinitionProvider('python', {{
                            provideDefinition: async (model, position, token) => {{
                                return new Promise((resolve) => {{
                                    const text = model.getValue();
                                    const definitionData = {{
                                        text: text,
                                        position: {{
                                            line: position.lineNumber - 1,
                                            column: position.column - 1
                                        }},
                                        file_path: model.uri ? model.uri.toString() : null
                                    }};
                                    // Reuse declaration pending ref since they serve same purpose
                                    pendingDeclarationRef.current = resolve;
                                    handleDeclarationRequest(definitionData);
                                    console.log('Definition request sent:', definitionData);
                                    setTimeout(() => {{
                                        if (pendingDeclarationRef.current === resolve) {{
                                            pendingDeclarationRef.current = null;
                                            console.log('Definition request timed out');
                                            resolve([]);
                                        }}
                                    }}, 10000);
                                }});
                            }}
                        }});

                        // Register signature help provider
                        if (signatureHelpProviderRef.current) {{
                            signatureHelpProviderRef.current.dispose();
                        }}
                        signatureHelpProviderRef.current = monaco.languages.registerSignatureHelpProvider('python', {{
                            signatureHelpTriggerCharacters: ['(', ','],
                            provideSignatureHelp: async (model, position, token, context) => {{
                                return new Promise((resolve) => {{
                                    const text = model.getValue();
                                    const signatureData = {{
                                        text: text,
                                        position: {{
                                            line: position.lineNumber - 1,
                                            column: position.column - 1
                                        }},
                                        file_path: model.uri ? model.uri.toString() : null
                                    }};
                                    pendingSignatureHelpRef.current = resolve;
                                    handleSignatureHelpRequest(signatureData);
                                    console.log('Signature help request sent:', signatureData);
                                    setTimeout(() => {{
                                        if (pendingSignatureHelpRef.current === resolve) {{
                                            pendingSignatureHelpRef.current = null;
                                            console.log('Signature help request timed out');
                                            resolve(null);
                                        }}
                                    }}, 5000);
                                }});
                            }}
                        }});

                        // Register reference provider
                        if (referenceProviderRef.current) {{
                            referenceProviderRef.current.dispose();
                        }}
                        referenceProviderRef.current = monaco.languages.registerReferenceProvider('python', {{
                            provideReferences: async (model, position, context, token) => {{
                                return new Promise((resolve) => {{
                                    const text = model.getValue();
                                    const referenceData = {{
                                        text: text,
                                        position: {{
                                            line: position.lineNumber - 1,
                                            column: position.column - 1
                                        }},
                                        file_path: model.uri ? model.uri.toString() : null
                                    }};
                                    pendingReferenceRef.current = resolve;
                                    handleReferenceRequest(referenceData);
                                    console.log('Reference request sent:', referenceData);
                                    setTimeout(() => {{
                                        if (pendingReferenceRef.current === resolve) {{
                                            pendingReferenceRef.current = null;
                                            console.log('Reference request timed out');
                                            resolve([]);
                                        }}
                                    }}, 10000);
                                }});
                            }}
                        }});

                        // Register rename provider
                        if (renameProviderRef.current) {{
                            renameProviderRef.current.dispose();
                        }}
                        renameProviderRef.current = monaco.languages.registerRenameProvider('python', {{
                            provideRenameEdits: async (model, position, newName, token) => {{
                                return new Promise((resolve) => {{
                                    const text = model.getValue();
                                    const renameData = {{
                                        text: text,
                                        position: {{
                                            line: position.lineNumber - 1,
                                            column: position.column - 1
                                        }},
                                        file_path: model.uri ? model.uri.toString() : null,
                                        new_name: newName
                                    }};
                                    pendingRenameRef.current = resolve;
                                    handleRenameRequest(renameData);
                                    console.log('Rename request sent:', renameData);
                                    setTimeout(() => {{
                                        if (pendingRenameRef.current === resolve) {{
                                            pendingRenameRef.current = null;
                                            console.log('Rename request timed out');
                                            resolve(null);
                                        }}
                                    }}, 10000);
                                }});
                            }},
                            resolveRenameLocation: async (model, position, token) => {{
                                return new Promise((resolve) => {{
                                    const text = model.getValue();
                                    const prepareData = {{
                                        text: text,
                                        position: {{
                                            line: position.lineNumber - 1,
                                            column: position.column - 1
                                        }},
                                        file_path: model.uri ? model.uri.toString() : null
                                    }};
                                    pendingPrepareRenameRef.current = resolve;
                                    handlePrepareRenameRequest(prepareData);
                                    console.log('Prepare rename request sent:', prepareData);
                                    setTimeout(() => {{
                                        if (pendingPrepareRenameRef.current === resolve) {{
                                            pendingPrepareRenameRef.current = null;
                                            console.log('Prepare rename request timed out');
                                            resolve(null);
                                        }}
                                    }}, 5000);
                                }});
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
                        if (declarationProviderRef.current) {{
                            declarationProviderRef.current.dispose();
                        }}
                        if (definitionProviderRef.current) {{
                            definitionProviderRef.current.dispose();
                        }}
                        if (signatureHelpProviderRef.current) {{
                            signatureHelpProviderRef.current.dispose();
                        }}
                        if (referenceProviderRef.current) {{
                            referenceProviderRef.current.dispose();
                        }}
                        if (renameProviderRef.current) {{
                            renameProviderRef.current.dispose();
                        }}
                        // Clear any pending promises
                        pendingCompletionRef.current = null;
                        pendingHoverRef.current = null;
                        pendingDeclarationRef.current = null;
                        pendingSignatureHelpRef.current = null;
                        pendingReferenceRef.current = null;
                        pendingPrepareRenameRef.current = null;
                        pendingRenameRef.current = null;
                    }};
                }}, [monaco]);
            """
        ]


monaco = MonacoEditor.create
