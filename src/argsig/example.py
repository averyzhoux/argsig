from typing import Annotated

import argsig as arg


# === 测试区 ===
@arg.Argument("v0.1.0")
def foo(
    x0: Annotated[int, []],  # 位置参数
    x1: Annotated[int, ["--", "-"]],  # 可选参数 简化
    x2: Annotated[int, ["--x2", "-x"]],  # 可选参数
    x3: Annotated[int, ["METAVAR X Y"]],
    x4: Annotated[int, ["--", "-"]],
    a: Annotated[list[int],  ["这里是help信息"]], # ("*", 123),
    a1: Annotated[int, [[1, 2], "这里是help信息", "*"]],
    b: Annotated[bool, ["这里是help信息"]],
    *,
    c: Annotated[str, ["这里是help信息", [1, 2], 2, "?", {}]] = "",
    # name_or_flags: Annotated[type, nargs, list[choices], "这里是help信息", const] = default,
) -> bool:
    """使用说明"""
    print(f"执行了 foo: a={a}, b={b}")
    # foo
    return True

    # ok  - *name_or_flags: str,
    # ok  -- metavar: str | tuple[str, ...] | None = ...,
    # ok  - type: _ActionType = ...,
    # ok  - help: str | None = ...,
    # ok  - default: Any = ...,
    # ok  - choices: Iterable[Any] | None = ...,
    # ok  - nargs: int | str | None = None,
    # ok  - required: bool = ...,
    #  action: str | type[Action] = ...,
    # ok  - version: str = ...,
    #  - const: Any = ...,
    #  - dest: str | None = ...,


# 测试
# foo(1, "a")
# foo("a", 1)
foo.run()
