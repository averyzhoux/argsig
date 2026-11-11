import argparse
import inspect
import sys
from collections.abc import Callable
from functools import wraps
from typing import (
    Annotated,
    Literal,
    ParamSpec,
    TypeVar,
    get_args,
    get_origin,
    get_type_hints,
)

# === 泛型装饰器部分 ===
P = ParamSpec("P")
R = TypeVar("R")

P2 = ParamSpec("P2")
R2 = TypeVar("R2")


class RawHelpFormatter(argparse.HelpFormatter):
    def _split_lines(self, text, width):
        return [text]


class ZArgumentParser(argparse.ArgumentParser):
    pass


# 关键修复：必须显式继承 Generic[P, R]
class Function[**P, R]:
    def __init__(
        self,
        func: Callable[P, R],
        v="",
        *,
        depth=1,
        parser: argparse.ArgumentParser | None = None,
    ) -> None:
        self.func = func
        self.depth = depth
        self.parser = parser
        # 把原函数的名称、文档字符串等元数据复制给实例，方便终端打印或调试
        wraps(func)(self)
        self._sub_parsers_dest_name = "__ARGSIG_SUBS_DEST__"

        if self.parser is None:
            self.parser = argparse.ArgumentParser(
                description=self.func.__doc__,
                formatter_class=RawHelpFormatter,
            )
        self.subparsers = None
        self.subs: dict[str, Function] = {}
        self.register(v)

    # def Arg[**P, R](func: Callable[P, R]) -> "Function[P, R]":
    #     return Function(func)

    def Argument(self, version: str = ""):
        def Arg_[**P2, R2](func: Callable[P2, R2]) -> Function[P2, R2]:
            assert self.parser
            if self.subparsers is None:
                self.subparsers = self.parser.add_subparsers(
                    dest=self._sub_parsers_dest_name
                )
            parser = self.subparsers.add_parser(func.__name__)
            f = Function(func, version, parser=parser, depth=self.depth + 1)
            self.subs[func.__name__] = f
            return f

        return Arg_

    def register(self, v):

        sig = inspect.signature(self.func)
        hints = get_type_hints(self.func, include_extras=True)
        parser = self.parser
        assert parser

        if v:
            parser.add_argument("-v", "--version", action="version", version=v)

        if not sig.parameters:
            return

        types = []
        for name, param in sig.parameters.items():
            hint = hints.get(name)
            type_ = hint
            if get_origin(hint) is Annotated:
                type_, *_ = get_args(hint)
            types.append(type_)
        maxtypelen = len(max(t.__name__ for t in types)) + 2

        for name, param in sig.parameters.items():
            hint = hints.get(name)

            if not hint:
                raise TypeError

            # 0. 基础配置
            xname = name.replace("_", "-")
            names = []
            # *name_or_flags: str,
            kwargs = {}
            kwargs["help"] = ""
            kwargs["nargs"] = None
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
            metadatas = []

            # 1. 拆解 Annotated
            if get_origin(hint) is Annotated:
                type_, *metadatas = get_args(hint)

            if type_ is bool:
                kwargs["action"] = argparse.BooleanOptionalAction
                kwargs["default"] = False
                kwargs.pop("nargs", None)
            elif get_origin(type_) is list:
                (inner,) = get_args(type_)
                kwargs["type"] = inner
                kwargs.setdefault("nargs", "*")  # list 默认 *
                if get_origin(inner) is Literal:
                    choices = get_args(inner)
                    a, *_ = {type(c) for c in choices}
                    assert not _
                    kwargs["type"] = a
                    kwargs["choices"] = choices
            elif type_ is list:
                # 裸 list，没有内层类型，给兜底
                kwargs["type"] = str  # 或干脆不设 type
                kwargs.setdefault("nargs", "*")
            elif get_origin(type_) is Literal:
                choices = get_args(type_)
                a, *_ = {type(c) for c in choices}
                assert not _
                type_ = a
                kwargs["type"] = a
                kwargs["choices"] = choices
            else:
                kwargs["type"] = type_

            kwargs["help"] += type_.__name__.ljust(maxtypelen)

            for metadata in metadatas:
                if isinstance(metadata, tuple):
                    nargs, *const = metadata
                    if nargs in ["*", "+", "?"]:
                        kwargs["nargs"] = nargs

                        if nargs == "?" and const:
                            kwargs["const"] = const[0]
                    elif v := {
                        ">": argparse.REMAINDER,
                        ">>": argparse.PARSER,
                    }.get(nargs):
                        kwargs["nargs"] = v
                    else:
                        assert isinstance(nargs, int)
                        kwargs["nargs"] = nargs

                if isinstance(metadata, list | set):
                    # 2. 自动推断（类型、列表、布尔）
                    for m in metadata:
                        if m in [""]:
                            continue

                        if isinstance(m, str):
                            # 处理 name_or_flags
                            if m.startswith("-"):
                                if m.startswith("--"):
                                    if m == "--":
                                        names.append(f"--{xname}")
                                    else:
                                        names.append(m)
                                else:
                                    if m == "-":
                                        names.append(f"-{xname[0]}")
                                    else:
                                        names.append(m)

                            # 处理 nargs
                            else:
                                if m.isupper():
                                    kwargs["metavar"] = m
                                else:
                                    kwargs["help"] += m

                        elif isinstance(m, tuple) and all(
                            isinstance(_, str) and _.isupper() for _ in m
                        ):
                            kwargs["metavar"] = m

            # 处理位置参数
            is_positioned = False
            if not names:
                if type_ is bool:
                    names.append(f"--{xname}")
                else:
                    is_positioned = True
                    names.append(name)

            # 3. 处理默认值和必填
            if is_positioned:
                if param.default is not inspect.Parameter.empty:
                    if kwargs["nargs"] in ["*", "?"]:
                        pass
                    elif kwargs["nargs"] is None:
                        kwargs["nargs"] = "?"
                    else:
                        raise TypeError(
                            f"位置参数 {name!r} 的 nargs={kwargs['nargs']!r} 不支持默认值"
                        )
                    kwargs["default"] = param.default

            else:
                if param.default is not inspect.Parameter.empty:
                    kwargs["default"] = param.default
                else:
                    if not type_ is bool:
                        kwargs["required"] = True

            # print(names, dict(sorted(kwargs.items())))

            # 4. 回调 argparse
            parser.add_argument(*names, **kwargs)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self.func(*args, **kwargs)

    def run(self) -> R:
        args = self.parser.parse_args(sys.argv[self.depth :])  # type: ignore
        kwargs = vars(args)
        if subcmd := kwargs.pop(self._sub_parsers_dest_name, None):
            child = self.subs[subcmd]
            return child.run()
        else:
            return self.func(**kwargs)  # type: ignore


def Arg[**P, R](func: Callable[P, R]) -> Function[P, R]:
    return Function(func)


def Argument(version: str = ""):
    def Arg_[**P, R](func: Callable[P, R]) -> Function[P, R]:
        return Function(func, version)

    return Arg_
