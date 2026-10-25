"""Custom component for the Monaco editor.

Props are documented here: https://github.com/suren-atoyan/monaco-react?tab=readme-ov-file#props
LSP client based on https://github.com/microsoft/vscode-languageserver-node/tree/main/client
"""

from dataclasses import dataclass
from typing import Any

import reflex as rx
from reflex.utils import imports
from typing_extensions import override

from pycodium.models.monaco import (
    CompletionRequest,
    DeclarationRequest,
    HoverRequest,
    PrepareRenameRequest,
    ReferenceRequest,
    RenameRequest,
    SignatureHelpRequest,
)


@dataclass(frozen=True)
class LSPProvider:
    """Configuration for a Monaco provider and its backend bridge."""

    trigger: str
    response: str
    register: str
    method: str
    options: dict[str, Any]


LSP_PROVIDERS = {
    "completion": LSPProvider(
        "on_completion_request",
        "completion_response",
        "registerCompletionItemProvider",
        "provideCompletionItems",
        {"triggerCharacters": ["."]},
    ),
    "hover": LSPProvider("on_hover_request", "hover_info", "registerHoverProvider", "provideHover", {}),
    "declaration": LSPProvider(
        "on_declaration_request", "declaration_response", "registerDeclarationProvider", "provideDeclaration", {}
    ),
    "definition": LSPProvider(
        "on_declaration_request", "declaration_response", "registerDefinitionProvider", "provideDefinition", {}
    ),
    "signature_help": LSPProvider(
        "on_signature_help_request",
        "signature_help_response",
        "registerSignatureHelpProvider",
        "provideSignatureHelp",
        {"signatureHelpTriggerCharacters": ["(", ","]},
    ),
    "reference": LSPProvider(
        "on_reference_request", "reference_response", "registerReferenceProvider", "provideReferences", {}
    ),
    "prepare_rename": LSPProvider(
        "on_prepare_rename_request", "prepare_rename_response", "registerRenameProvider", "provideRenameLocation", {}
    ),
    "rename": LSPProvider("on_rename_request", "rename_response", "registerRenameProvider", "provideRenameEdits", {}),
}


class MonacoEditor(rx.Component):
    """Monaco editor component."""

    library = "@monaco-editor/react"
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
    completion_response: rx.Var[dict[str, Any]] = rx.Var.create({})

    diagnostics_response: rx.Var[dict[str, Any]] = rx.Var.create({})
    on_diagnostics_request: rx.EventHandler[rx.event.passthrough_event_spec(CompletionRequest)]

    # Hover info from state
    hover_info: rx.Var[dict[str, Any]] = rx.Var.create({})

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

    def _provider_config(self) -> str:
        """Build provider callbacks from Python configuration, as for menu actions."""
        return str(
            rx.Var.create(
                {
                    name: {
                        "callback": rx.Var.create(self.event_triggers[config.trigger]),
                        "register": config.register,
                        "method": config.method,
                        "options": config.options,
                    }
                    for name, config in LSP_PROVIDERS.items()
                    if config.trigger in self.event_triggers
                }
            )
        )

    @override
    def _exclude_props(self) -> list[str]:
        """Keep backend response data and bridge callbacks off the React editor."""
        return [
            *super()._exclude_props(),
            *{config.trigger for config in LSP_PROVIDERS.values()},
            "on_diagnostics_request",
            "diagnostics_response",
            *{config.response for config in LSP_PROVIDERS.values()},
        ]

    @override
    def add_hooks(self) -> list[str | rx.Var[str]]:
        """Register data driven providers with correlated, cancellable requests."""
        hooks: list[str | rx.Var[str]] = ["const monaco = useMonaco(); const lspPending = useRef(new Map());"]
        for response in dict.fromkeys(config.response for config in LSP_PROVIDERS.values()):
            value = getattr(self, response)
            hooks.append(f"""
useEffect(() => {{
    const response = {value!s};
    lspPending.current.get(response.request_id)?.(response);
}}, [{value!s}]);
""")
        hooks.append(
            """
useEffect(() => {
    if (!monaco) return;
    const pending = lspPending.current;
    const range = r => ({startLineNumber: r.start.line + 1, startColumn: r.start.character + 1,
                         endLineNumber: r.end.line + 1, endColumn: r.end.character + 1});
    const locations = r => (r.items || []).map(item => ({...item, uri: monaco.Uri.parse(item.uri)}));
    const convert = {
        completion: (r, model, position) => ({suggestions: (r.items || []).map(item => ({
            range: {startLineNumber: position.lineNumber, endLineNumber: position.lineNumber,
                    startColumn: model.getWordUntilPosition(position).startColumn, endColumn: position.column},
            label: item.label, kind: [18, 0, 1, 2, 3, 4, 5, 7, 8, 9, 12, 13, 15, 17, 27, 19, 20, 21, 23, 16, 14, 6, 10, 11, 24][(item.kind || 1) - 1] ?? 18,
            insertText: item.insert_text || item.label,
            insertTextRules: item.insert_text?.includes('${') ? 4 : undefined,
            documentation: item.documentation, detail: item.detail || ''
        }))}),
        hover: r => ({contents: r.contents ? [{value: r.contents}] : []}),
        declaration: locations,
        definition: locations,
        reference: locations,
        signature_help: r => r.signatures ? {value: r, dispose() {}} : null,
        prepare_rename: r => r.range ? {range: range(r.range), text: r.placeholder || ''} : null,
        rename: r => r.edit ? {edits: [
            ...Object.entries(r.edit.changes || {}).flatMap(([uri, edits]) =>
                edits.map(edit => ({resource: monaco.Uri.parse(uri), versionId: undefined,
                                   textEdit: {range: range(edit.range), text: edit.newText}}))),
            ...(r.edit.documentChanges || []).flatMap(change => (change.edits || []).map(edit => ({
                resource: monaco.Uri.parse(change.textDocument.uri), versionId: undefined,
                textEdit: {range: range(edit.range), text: edit.newText}
            })))
        ]} : null
    };
    const request = (name, config, model, position, token, extra = {}) => new Promise(resolve => {
        const request_id = crypto.randomUUID();
        let timer;
        let cancellation;
        const finish = response => {
            if (!pending.delete(request_id)) return;
            clearTimeout(timer);
            cancellation?.dispose();
            if (name === 'prepare_rename' && response.range && !response.placeholder) {
                response.placeholder = model.getValueInRange(range(response.range));
            }
            resolve(convert[name](response, model, position));
        };
        pending.set(request_id, finish);
        timer = setTimeout(() => finish({}), 30000);
        cancellation = token?.onCancellationRequested(() => finish({}));
        if (token?.isCancellationRequested) { finish({}); return; }
        config.callback({request_id, text: model.getValue(), file_path: model.uri.toString(),
            position: {line: position.lineNumber - 1, column: position.column - 1}, ...extra});
    });
    const configs = __CONFIG__;
    const providers = Object.entries(configs).filter(([name]) => name !== 'prepare_rename').map(([name, config]) => {
        const provider = {...config.options};
        provider[config.method] = (model, position, ...args) => {
            const token = ['reference', 'rename', 'completion'].includes(name) ? args[1] : args[0];
            return request(name, config, model, position, token, name === 'rename' ? {new_name: args[0]} : {});
        };
        if (name === 'rename' && configs.prepare_rename) {
            provider.resolveRenameLocation = (model, position, token) =>
                request('prepare_rename', configs.prepare_rename, model, position, token);
        }
        return monaco.languages[config.register]('python', provider);
    });
    return () => {
        providers.forEach(provider => provider.dispose());
        [...pending.values()].forEach(finish => finish({}));
    };
}, [monaco]);
""".replace("__CONFIG__", self._provider_config())
        )
        if "on_diagnostics_request" in self.event_triggers:
            callback = rx.Var.create(self.event_triggers["on_diagnostics_request"])
            hooks.extend(
                [
                    f"""
useEffect(() => {{
    const timer = setTimeout(() => {{
        if ({self.language!s} === 'python') ({callback!s})({{
            request_id: crypto.randomUUID(), text: {self.value!s}, file_path: {self.path!s},
            position: {{line: 0, column: 0}}
        }});
    }}, 300);
    return () => clearTimeout(timer);
}}, [{self.value!s}, {self.path!s}, {self.language!s}]);
""",
                    f"""
useEffect(() => {{
    if (!monaco) return;
    const response = {self.diagnostics_response!s};
    const model = monaco.editor.getModel(monaco.Uri.parse(response.uri || 'inmemory://empty'));
    if (!model || model.getValue() !== response.text) return;
    monaco.editor.setModelMarkers(model, 'basedpyright', (response.items || []).map(item => ({{
        startLineNumber: item.range.start.line + 1, startColumn: item.range.start.character + 1,
        endLineNumber: item.range.end.line + 1, endColumn: item.range.end.character + 1,
        message: item.message, severity: ({{1: 8, 2: 4, 3: 2, 4: 1}})[item.severity] || 2,
        source: item.source || 'basedpyright'
    }})));
}}, [monaco, {self.diagnostics_response!s}]);
""",
                ]
            )
        return hooks


monaco = MonacoEditor.create
