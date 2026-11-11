from typing import Annotated

import argsig as arg


# === 测试区 ===
@arg.Argument("v0.1.0")  # 这里写version 和 help
def foo(
    a: Annotated[int, [1, 2], "这里是help信息", "*"],
    b: Annotated[str, "这里是help信息", "?"],
    *,
    c: Annotated[str, "这里是help信息", [1, 2], 2] = "",
) -> bool:
    """使用说明"""
    print(f"执行了 foo: a={a}, b={b}")
    return True

    #  - *name_or_flags: str,
    #  - type: _ActionType = ...,
    #  - help: str | None = ...,
    #  - default: Any = ...,
    #  - choices: Iterable[Any] | None = ...,
    #  - nargs: int | str | None = None,
    #  - required: bool = ...,
    #  action: str | type[Action] = ...,
    #  - version: str = ...,


#   const: Any = ...,
#   metavar: str | tuple[str, ...] | None = ...,
#   dest: str | None = ...,

# 测试
foo(1, "a")
foo("a", 1)  # type: ignore
foo.run()
