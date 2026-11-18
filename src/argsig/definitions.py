import argparse
import inspect
import sys
import types
from collections.abc import Callable
from functools import wraps
from typing import (
    Annotated,
    Literal,
    Union,
    # ParamSpec,
    # TypeVar,
    get_args,
    get_origin,
    get_type_hints,
)

from .consts import *
from .parse import encode

# class RawHelpFormatter(argparse.HelpFormatter):
#     def _split_lines(self, text, width):
#         return [text]


# class ZArgumentParser(argparse.ArgumentParser):
#     pass


# 关键修复：必须显式继承 Generic[P, R]
class Function[**P, R]:
    def __init__(
        self,
        func: Callable[P, R],
        version: list[str] | str = "",
        *,
        depth=1,
        parser: argparse.ArgumentParser | None = None,
    ) -> None:
        # 把原函数的名称、文档字符串等元数据复制给实例，方便终端打印或调试
        wraps(func)(self)

        self._func = func
        self._depth = depth
        self.parser = (
            parser if parser else argparse.ArgumentParser(description=func.__doc__)
        )
        self._sub_parsers_dest_name = "__ARGSIG_SUBS_DEST__"
        self.subparsers = None
        self.subfunction: dict[str, Function] = {}

        self._register(version)

    def Argument(self, version: str = ""):
        def Arg_[**P2, R2](func: Callable[P2, R2]) -> Function[P2, R2]:
            assert self.parser
            if self.subparsers is None:
                self.subparsers = self.parser.add_subparsers(
                    dest=self._sub_parsers_dest_name
                )
            parser = self.subparsers.add_parser(func.__name__)
            f = Function(func, version, parser=parser, depth=self._depth + 1)
            self.subfunction[func.__name__] = f
            return f

        return Arg_

    def _register_parameter(self, parameter: inspect.Parameter):
        kinds = {
            inspect.Parameter.POSITIONAL_ONLY: "/",
            inspect.Parameter.POSITIONAL_OR_KEYWORD: "|",
            # inspect.Parameter.VAR_POSITIONAL
            inspect.Parameter.KEYWORD_ONLY: "*",
            # inspect.Parameter.VAR_KEYWORD
        }
        nms, kws = encode(
            parameter.name,
            parameter.annotation,
            parameter.default,
            kind=kinds[parameter.kind],  # type: ignore
        )
        self.parser.add_argument(*nms, **kws)

    def _register(self, v):

        sig = inspect.signature(self._func)
        # hints = get_type_hints(self._func, include_extras=True)
        parser = self.parser

        if isinstance(v, list):
            ...
            # tags, kwargs = self._parse_list_params(v)
            # parser.add_argument("-v", "--version", action="version", version=v)
        elif isinstance(v, str):
            parser.add_argument("-v", "--version", action="version", version=v)

        # parser.add_argument('-h', '--help', action='help',
        #                     default=argparse.SUPPRESS,
        #                     help='show this help message and exit')

        if not sig.parameters:
            return

        # types = []
        # for name, param in sig.parameters.ite ms():
        #     hint = hints.get(name)
        #     type_ = hint
        #     if get_origin(hint) is Annotated:
        #         type_, *_ = get_args(hint)
        #     types.append(type_)
        # maxtypelen = len(max(t.__name__ for t in types)) + 2

        for parameter in sig.parameters.values():
            self._register_parameter(parameter)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self._func(*args, **kwargs)

    def invoke(self) -> R:
        args = self.parser.parse_args(sys.argv[self._depth :])  # type: ignore
        kwargs = vars(args)
        if subcmd := kwargs.pop(self._sub_parsers_dest_name, None):
            child = self.subfunction[subcmd]
            return child.invoke()
        else:
            return self._func(**kwargs)  # type: ignore
