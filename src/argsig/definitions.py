import argparse

# import functools
import inspect
from collections.abc import Callable

# import sys
from functools import wraps
from typing import (
    Annotated,
    # Any,
    # Generic,
    ParamSpec,
    TypeVar,
    get_args,
    get_origin,
    get_type_hints,
)

# === 泛型装饰器部分 ===
P = ParamSpec("P")
R = TypeVar("R")


# 关键修复：必须显式继承 Generic[P, R]
class Function[**P, R]:
    def __init__(self, func: Callable[P, R], v="") -> None:
        self.func = func
        # 把原函数的名称、文档字符串等元数据复制给实例，方便终端打印或调试
        wraps(func)(self)

        self.register(v)

    def register(self, v):

        sig = inspect.signature(self.func)
        hints = get_type_hints(self.func, include_extras=True)
        self.parser = parser = argparse.ArgumentParser(description=self.func.__doc__)

        if v:
            parser.add_argument("-v", "--version", action="version", version=v)

        for name, param in sig.parameters.items():
            hint = hints.get(name)

            # 0. 基础配置
            names = [f"--{name.replace('_', '-')}"]
            # *name_or_flags: str,
            kwargs = {}
            #   type: _ActionType = ...,
            #   help: str | None = ...,
            #   default: Any = ...,
            #   choices: Iterable[Any] | None = ...,
            #   nargs: int | str | None = None,
            #   required: bool = ...,
            #   action: str | type[Action] = ...,
            #   version: str = ...,
            #   const: Any = ...,
            #   metavar: str | tuple[str, ...] | None = ...,
            #   dest: str | None = ...,
            type_ = hint
            metadata = []

            # 1. 拆解 Annotated
            if get_origin(hint) is Annotated:
                type_, *metadata = get_args(hint)
                # print(get_args(hint))

            if isinstance(type_, bool):
                ...
                # if param.default is True:
                #     # 用户写的是 flag: bool = True
                #     # 自动生成 --no-flag，传了变成 False
                #     names = [f"--no-{name.replace('_', '-')}"]
                #     kwargs["action"] = "store_false"
                # else:
                #     # 用户写的是 flag: bool = False（或者没写默认值）
                #     # 自动生成 --flag，传了变成 True
                #     kwargs["action"] = "store_true"
                #     kwargs["default"] = False
            else:
                kwargs["type"] = type_

            # 2. 自动推断（类型、列表、布尔）
            for m in metadata:
                if m in [""]:
                    continue

                if isinstance(m, str):
                    if len(m) == 1:
                        if m in ["*", "+", "?"]:
                            kwargs["nargs"] = m
                        if m == "~":
                            kwargs["nargs"] = None
                    else:
                        kwargs["help"] = m

                elif isinstance(m, int):
                    kwargs["nargs"] = m

                elif isinstance(m, list):
                    kwargs["choices"] = m

            # 3. 处理默认值和必填
            if param.default is not inspect.Parameter.empty:
                kwargs["default"] = param.default
            else:
                if not isinstance(type_, bool):
                    kwargs["required"] = True

            print(names, dict(sorted(kwargs.items())))

            # 4. 回调 argparse
            parser.add_argument(*names, **kwargs)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self.func(*args, **kwargs)

    def run(self):
        args = self.parser.parse_args()
        kwargs = vars(args)
        return self.func(**kwargs)  # type: ignore


def Arg[**P, R](func: Callable[P, R]) -> Function[P, R]:
    return Function(func)


def Argument(version: str = ""):
    def Arg_[**P, R](func: Callable[P, R]) -> Function[P, R]:
        return Function(func, version)

    return Arg_
