# argsig

> A minimal decorator that builds `argparse` CLIs automatically from type annotations.

`argsig` lets you declare command-line arguments directly in your function signature via type annotations (`Annotated`), then generates an `argparse.ArgumentParser` for you — no more boilerplate `add_argument` calls.

## Installation

```bash
pip install argsig
```

## Quick Start

```python
from typing import Annotated
import argsig as arg

@arg.Arg
def greet(
    name: str,
    count: Annotated[int, ("-c",)] = 1,
    verbose: bool = False,
):
    """Print a greeting."""
    for _ in range(count):
        print(f"Hello, {name}!" if verbose else f"Hi, {name}")

if __name__ == "__main__":
    greet.run()
```

```bash
$ python demo.py Alice -c 3
Hi, Alice
Hi, Alice
Hi, Alice

$ python demo.py --help
usage: demo.py [-h] [-c COUNT] [--verbose | --no-verbose] name
```

## How It Works

`argsig` inspects the decorated function's signature and type annotations, then configures `argparse` accordingly:

| Signature | Generated argument |
| --- | --- |
| No default, non-`bool` | Positional argument |
| `bool` type | `--flag / --no-flag` switch |
| `list[T]` | `nargs="*"`, element type `T` |
| Positional with default | Automatically inferred `nargs="?"` |
| Keyword-only (after `*`) | `required` `--` option |

**Every parameter must have a type annotation**, otherwise a `TypeError` is raised.

## `Annotated` Metadata

Metadata inside `Annotated[T, ...]` controls the argparse option. Three forms are supported:

### Strings

| Value | Effect |
| --- | --- |
| `"-x"` / `"--xxx"` | Add a short/long option name |
| `"-"` | Auto-generate short option (first letter of param name, e.g. `-c`) |
| `"--"` | Auto-generate long option (e.g. `--count`) |
| `"HELP"` | Uppercase → `metavar`; lowercase → `help` text |

### Sets

`{"a", "b"}` → `choices`

### Tuples

`(nargs, *const)` form, controlling `nargs` and optional `const`:

| Tuple | Meaning |
| --- | --- |
| `("*",)` / `("+",)` / `("?",)` | Corresponding `nargs` value |
| `("?", const)` | `nargs="?"` with `const` |
| `(">",)` / `(">>",)` | `argparse.REMAINDER` / `argparse.PARSER` |
| `(3,)` | Integer `nargs` |

## Example

```python
from typing import Annotated
import argsig as arg

@arg.Argument("v0.1.0")
def foo(
    x0: Annotated[int, []],              # positional
    x1: Annotated[int, ["--", "-"]],     # optional (auto --x1 / -x)
    x2: Annotated[int, ["--x2", "-x"]],  # optional (explicit names)
    x3: Annotated[int, ["METAVAR"]],     # positional + metavar
    a: Annotated[list[int], ("*", 123), ["numbers to process"]],
    a1: Annotated[int, [{1, 2}, "must be 1 or 2"]],
    b: Annotated[bool, ["enable the switch"]],
    *,
    c: Annotated[str, ["help text", {1, 2}]] = "",
):
    """Usage notes."""
    print(f"a={a}, b={b}, c={c}")

if __name__ == "__main__":
    foo.run()
```

```bash
$ python demo.py --help
usage: demo.py [-h] [-v] [--x1 X1] [--x2 X] METAVAR [A ...] [{1,2}] [--b | --no-b] [-c C] X0

$ python demo.py 10 20 30 -- -1
```

## API

### `Arg`

```python
def Arg[**P, R](func: Callable[P, R]) -> Function[P, R]
```

Decorate a function directly:

```python
@Arg
def main(name: str): ...
```

### `Argument(version="")`

```python
def Argument(version: str = ""):
    ...
```

Decorator factory with a version string. When `version` is supplied, a `-v/--version` option is added:

```python
@Argument(version="1.0.0")
def main(name: str): ...
```

### `Function`

The decorated object:

- `func.parser` — the underlying `argparse.ArgumentParser`, open for further customization
- `func.run()` — parses `sys.argv` and calls the original function with keyword arguments
- `func(*args, **kwargs)` — calls the original function directly (no CLI parsing)

```python
@Arg
def add(a: int, b: int):
    return a + b

add(1, 2)     # direct call, returns 3
add.run()     # parse from command line
add.parser.print_help()
```

## Help Text

A custom `RawHelpFormatter` is used by default, which does not auto-wrap help text — handy for longer descriptions:

```python
x: Annotated[str, ("NAME", "A user name with a description long enough that it would otherwise be wrapped")]
```

## Metadata Cheat Sheet

| `Annotated` metadata | Corresponding `add_argument` |
| --- | --- |
| `"-x"` / `"--xxx"` | `*name_or_flags` |
| `"HELP"` (uppercase) | `metavar` |
| `"help"` (lowercase) | `help` |
| `{...}` | `choices` |
| `("*", "+", "?")` | `nargs` |
| `("?", const)` | `nargs` + `const` |
| `(">",)` / `(">>",)` | `nargs=REMAINDER` / `PARSER` |
| `(int,)` | integer `nargs` |
| `bool` type | `action=BooleanOptionalAction`, `default=False` |
| `list[T]` | `type=T`, `nargs="*"` |
| Parameter default | `default` |
| Keyword param without default | `required=True` |

## Limitations

- All parameters must be type-annotated (missing → `TypeError`)
- Positional parameters with defaults only support `nargs` of `None`, `"?"`, or `"*"`; other combinations raise `TypeError`
- `bool` parameters default to `False` (`BooleanOptionalAction` semantics)
- Requires Python 3.12+ (uses PEP 695 generic syntax `class Function[**P, R]`)

## License

MIT
