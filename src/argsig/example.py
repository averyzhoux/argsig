from typing import Annotated, Literal

import argsig


@argsig.Argument("v0.1.1")
def foo(
    # x0: Annotated[int, []],  # 位置参数
    # yy: Annotated[int, ["--", "-"]],  # 可选参数 简化
    # x2: Annotated[int, ["--x2", "-x"]],  # 可选参数
    # x3: Annotated[int, ["METAVAR X Y"]],
    # zz: Annotated[int, ["--", "-"]],
    # a: Annotated[list[Literal[1, 2]], ("*", 123), [("A", "B"), "这里是help信息"]],
    # a1: Annotated[Literal[1, 2], ["--", "这里是help信息"]],
    # b: Annotated[bool, ["这里是help信息"]],
    # *,
    # c: Annotated[str, ["这里是help信息", {1, 2}, 2, {}]] = "",
    # # name_or_flags: Annotated[type, nargs, list[choices], "这里是help信息", const] = default,
) -> bool:
    """使用说明"""
    print('foo')
    # print(f"执行了 foo: a={a}, b={b}")
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


@foo.Argument("v0.1.0")
def subfoo() -> None:
    print('sub foo')


# 测试
# foo(1, "a")
# foo("a", 1)
foo.run()
subfoo.run()
