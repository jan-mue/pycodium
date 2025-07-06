# PyCodium Development Guidelines

## Project Overview

- PyCodium is a Python IDE built with [Reflex](https://github.com/reflex-dev/reflex) and the [Monaco](https://github.com/microsoft/monaco-editor) editor
- [uv](https://github.com/astral-sh/uv) is used for dependency management. Dependencies are defined in `pyproject.toml` and installed with `uv sync`. Run `uv lock` when you modify dependencies to update the lock file.
- pre-commit is used for formatting and linting. Run `pre-commit run --all-files` to format all files. The pre-commit hooks are defined in `.pre-commit-config.yaml`.

## Reflex Development Guidelines

- Import Reflex with `import reflex as rx`
- Components are created using functions that return a component object
- Components can be nested as children (passed as positional arguments)
- Props are passed as keyword arguments (use snake_case for CSS properties)
- **Critical**: Understand compile-time vs. runtime distinction
  - Components are compiled to JavaScript at compile-time
  - State runs on the backend in Python at runtime
  - Cannot use arbitrary Python operations in components

### Proper Component Development

- Cannot use if/else statements with state vars - use `rx.cond()` instead:

  ```python
  # WRONG: rx.text(State.count if State.count % 2 == 0 else "Odd")
  # RIGHT:
  rx.cond(
      State.count % 2 == 0,
      rx.text("Even"),
      rx.text("Odd")
  )
  ```

- Cannot iterate over lists with for loops - use `rx.foreach()` instead:

  ```python
  # WRONG: *[rx.text(item) for item in State.items]
  # RIGHT:
  rx.foreach(
      State.items,
      lambda item: rx.text(item)  # Note: item is a Var, not a str
  )
  ```

- Cannot perform Python operations like `len()` on state vars directly
- Use Var operations for state calculations (e.g., `State.count % 2 == 0`)
- `&` is logical AND, `|` is logical OR, and `~` is the NOT operator for boolean vars
- Use the `.length()` operator to get the length of list vars

## State Management

- Create state classes by subclassing `rx.State`
- Define state vars with type annotations:

  ```python
  class AppState(rx.State):
      count: int = 0
      items: list[str] = ["Apple", "Banana"]
  ```

- State changes must be handled through event handlers in the state class:

  ```python
  @rx.event
  async def increment(self):
      self.count += 1
  ```

- Event handlers can take arguments when needed:

  ```python
  @rx.event
  async def increment(self, amount: int):
      self.count += amount
  ```

- Connect components to event handlers via event triggers:

  ```python
  rx.button("Increment", on_click=AppState.increment)
  rx.button("Add 5", on_click=lambda: AppState.increment(5))
  ```

- Prefer asynchronous event handlers
- You CAN use any Python code or libraries within event handlers

## Component Best Practices

- Break UI into smaller, reusable components
- Use `rx.el` namespace for HTML elements (e.g., `rx.el.div()`)
- Style components with CSS properties as props

## Python Coding Standards

- Follow PEP 8 style guide for Python code
- Use type hints for method arguments, return types, and variables
- Use specific types (e.g., `dict[str, str]` instead of `dict`)
- Use snake_case for variables, functions, and methods
- Use CamelCase for class names
- Use UPPER_CASE for constants
- Keep functions small and focused

## Best Practices

- Break functionality into separate building blocks
- Organize constants in dedicated modules
- Always specify error types in try-except blocks and include logging
- Don't call sync code from async functions (e.g. use `aiofiles.open()` instead of `open()`)

## Testing

- Use pytest for testing
- Run tests with `uv run pytest <optional test file or directory>`
- Structure tests in unit/ and integration/ directories
- Test one thing at a time with descriptive function names
- Parameterize tests to avoid repetition
- Mock external dependencies in unit tests
- Integration tests should have no mocked dependencies
- Run type checker with `uv run pyright <optional file or directory>`
