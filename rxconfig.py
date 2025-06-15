"""Configuration for the Reflex application."""

import reflex as rx

tailwind_config = {
    "darkMode": ["class"],
    "prefix": "",
    "theme": {
        "container": {"center": True, "padding": "2rem", "screens": {"2xl": "1400px"}},
        "extend": {
            "colors": {
                "border": "hsl(var(--border))",
                "input": "hsl(var(--input))",
                "ring": "hsl(var(--ring))",
                "background": "hsl(var(--background))",
                "foreground": "hsl(var(--foreground))",
                "primary": {"DEFAULT": "hsl(var(--primary))", "foreground": "hsl(var(--primary-foreground))"},
                "secondary": {"DEFAULT": "hsl(var(--secondary))", "foreground": "hsl(var(--secondary-foreground))"},
                "destructive": {
                    "DEFAULT": "hsl(var(--destructive))",
                    "foreground": "hsl(var(--destructive-foreground))",
                },
                "muted": {"DEFAULT": "hsl(var(--muted))", "foreground": "hsl(var(--muted-foreground))"},
                "accent": {"DEFAULT": "hsl(var(--accent))", "foreground": "hsl(var(--accent-foreground))"},
                "popover": {"DEFAULT": "hsl(var(--popover))", "foreground": "hsl(var(--popover-foreground))"},
                "card": {"DEFAULT": "hsl(var(--card))", "foreground": "hsl(var(--card-foreground))"},
                "pycodium": {
                    "bg": "var(--pycodium-bg)",
                    "sidebar-bg": "var(--pycodium-sidebar-bg)",
                    "activity-bar": "var(--pycodium-activity-bar)",
                    "editor-bg": "var(--pycodium-editor-bg)",
                    "panel-bg": "var(--pycodium-panel-bg)",
                    "statusbar-bg": "var(--pycodium-statusbar-bg)",
                    "tab-active": "var(--pycodium-tab-active)",
                    "tab-inactive": "var(--pycodium-tab-inactive)",
                    "highlight": "var(--pycodium-highlight)",
                    "text": "var(--pycodium-text)",
                    "icon": "var(--pycodium-icon)",
                },
            },
            "backgroundColor": {
                "pycodium-highlight": "var(--pycodium-highlight)",
            },
            "textColor": {
                "pycodium-text": "var(--pycodium-text)",
                "pycodium-icon": "var(--pycodium-icon)",
            },
            "borderRadius": {
                "lg": "var(--radius)",
                "md": "calc(var(--radius) - 2px)",
                "sm": "calc(var(--radius) - 4px)",
            },
            "keyframes": {
                "accordion-down": {"from": {"height": "0"}, "to": {"height": "var(--radix-accordion-content-height)"}},
                "accordion-up": {"from": {"height": "var(--radix-accordion-content-height)"}, "to": {"height": "0"}},
            },
            "animation": {
                "accordion-down": "accordion-down 0.2s ease-out",
                "accordion-up": "accordion-up 0.2s ease-out",
            },
        },
    },
    "plugins": ["tailwindcss-animate"],
}

config = rx.Config(
    app_name="pycodium",
    telemetry_enabled=False,
    show_built_with_reflex=False,
    plugins=[rx.plugins.TailwindV3Plugin()],  # type: ignore[reportPrivateImportUsage]
    tailwind=tailwind_config,
)
