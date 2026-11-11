# argsig

> **One object, two roles, and a more direct approach.**  
> A function and its CLI are no longer separate things.

`argsig` is a minimal, zero-dependency decorator that attaches a fully customizable CLI to your plain Python function — **without changing the function's calling semantics**. 

Have you ever written a perfect CLI script, only to realize you can't import it as a function because it's trapped inside `parser.parse_args()`? Or written a beautiful utility function, only to dread the boilerplate of wrapping it in `argparse` just to run it from the terminal? 

**`argsig` fixes the boundary.** Write the function once, and it seamlessly serves both as a pure, importable Python function and a powerful CLI entry point.

## Installation

```bash
pip install argsig
```

## One Object, Two Roles

```python
import argsig

@argsig.Arg
def add(a: int, b: int) -> int:
    return a + b

add(1, 2)      # Role 1: Plain function → 3 (IDE autocompletion works perfectly)
add.run()      # Role 2: CLI entry, parses sys.argv
add.parser     # The CLI projection, fully customizable
```
Unlike traditional CLI frameworks that hijack your function, `argsig` keeps it purely callable. Zero loss of freedom. Whatever you want to do, you can still do it. That is `argsig`.

---

## 🥊 How does it compare?

Every existing Python CLI library forces a compromise. `argsig` is built to eliminate them.

| Feature | Click / Typer | Tyro | `argparse` | **`argsig`** |
| :--- | :--- | :--- | :--- | :--- |
| **Original Function Callable** | ❌ (Replaced by Command) | ✅ | ❌ (Requires manual wrap) | ✅ **(`func(1, 2)` just works)** |
| **Zero Dependencies** | ❌ (Depends on Click) | ✅ | ✅ | ✅ **(Pure stdlib)** |
| **Type Hint Driven** | ⚠️ (Limited DSL) | ✅ | ❌ (Manual boilerplate) | ✅ **(PEP 593 Native)** |
| **Fine-grained argparse Control**| ❌ (Hidden) | ❌ (Extremely limited) | ✅ (All manual) | ✅ **(Via `Annotated`)** |
| **No Wrapper/Namespace** | ❌ | ❌ (Returns Dataclass) | ❌ | ✅ **(Executes cleanly)** |
| **Returns True Return Value** | ❌ | ❌ | ❌ | ✅ **(`return self.func(**kwargs)`)** |

### Why not Typer / Click?
They are great frameworks, but they **hijack** your function. Once decorated, your function becomes a `Command` object. You can no longer call `add(1, 2)` directly in your code without `CliRunner`. `argsig` lets the function stay a function.

### Why not Tyro?
Tyro is an extractor. It focuses on *not touching your code at all* (`tyro.cli(func)`), which results in a complete loss of fine-grained CLI control (like custom short flags or `metavars`), and it forces you to unpack Dataclass configurations. `argsig` gives you **maximum freedom** using `Annotated` and passes arguments directly to your function.

---

## Type Hints as CLI Arguments

`argsig` maps standard Python type hints directly to `argparse` behaviors. No custom DSL to learn.

| Signature | Generated Argument |
| --- | --- |
| No default, non-`bool` | Positional argument |
| `bool` | `--flag / --no-flag` switch (`BooleanOptionalAction`) |
| `list[T]` | `nargs="*"`, type `T` |
| Positional with default | Auto-inferred `nargs="?"` |
| Keyword-only (after `*`) | `required=True` |

### 🌟 The `Literal` Superpower

`Literal` is natively supported and mapped directly to `argparse.choices`. You get **perfect IDE autocompletion, static type safety, and CLI validation** all at once.

```python
from typing import Annotated, Literal
import argsig

@argsig.Arg
def train(
    # Automatically becomes choices=["fast", "slow"]
    mode: Literal["fast", "slow"] = "fast",
    
    # Combine `list` and `Literal` for the ultimate type safety!
    # In the function body, `targets` is a list of strings.
    # At the CLI, it requires exactly 2 choices from ["cpu", "gpu", "tpu"].
    targets: Annotated[list[Literal["cpu", "gpu", "tpu"]], (2,)]
):
    print(f"Training on {targets} in {mode} mode.")
```

Run from the terminal:
```bash
$ python train.py cpu tpu
Training on ['cpu', 'tpu'] in fast mode.

$ python train.py cpu ram
usage: train.py [-h] [--mode {fast,slow}] TARGETS [TARGETS ...]
train.py: error: argument targets: invalid choice: 'ram' (choose from 'cpu', 'gpu', 'tpu')
```

---

## Fine-Grained Control with `Annotated`

While type hints cover 90% of the use cases, you can use `Annotated` metadata to access the **full power of `argparse`**.

```python
from typing import Annotated
import argsig

@argsig.Argument(version="v0.1.0")
def main(
    files: Annotated[list[str], ("+",), ["Files to process"]],
    output: Annotated[str, ["--out", "-o", "OUTPUT"]], # Custom flags and metavar
    threshold: Annotated[int, ("?", 10)],             # nargs="?" and const=10
):
    """Process files."""
    ...
```

### Metadata Cheat Sheet

| Metadata inside `Annotated` | Effect |
| --- | --- |
| `"-x"` / `"--xxx"` | Add short/long option names |
| `"-"` | Auto-generate short option (e.g., `-f`) |
| `"--"` | Auto-generate long option (e.g., `--flag`) |
| `"HELP"` (Uppercase) | `metavar` |
| `"help"` (Lowercase) | `help` text |
| `{...}` (Set) | `choices` |
| `(nargs, *const)` (Tuple) | Set `nargs` (e.g., `"*"`, `"+"`, `"?"`, `2`) and optional `const` |
| `("A", "B")` (Tuple of uppercase) | Multiple `metavars` (e.g., for `nargs=2`) |
| `(">",)` / `(">>",)` | `argparse.REMAINDER` / `argparse.PARSER` |

---

## API Reference

### `@argsig.Arg`
Decorates a function directly.
```python
@argsig.Arg
def main(): ...
```

### `@argsig.Argument(version="")`
Decorates a function and automatically adds a `-v/--version` option.
```python
@argsig.Argument("1.0.0")
def main(): ...
```

### The `Function` Object
- `func.parser`: The underlying `argparse.ArgumentParser`. You can add custom arguments, subparsers, or change the formatter.
- `func.run()`: Parses `sys.argv`, calls the original function, and returns its raw return value.
- `func(*args, **kwargs)`: Directly calls the original function (bypassing CLI parsing). Fully understood by IDEs.

## Limitations

- Requires **Python 3.12+** (uses PEP 695 generic syntax `class Function[**P, R]`).
- All parameters must be type-annotated.
- Positional parameters with defaults only support `nargs` of `None`, `"?"`, or `"*"`.

## License

MIT
