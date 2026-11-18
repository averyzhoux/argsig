import argparse
from enum import Enum
from types import EllipsisType
from typing import Any, Iterable, TypedDict

# class ParamVars(TypedDict, total=False):
#     action: str | type[argparse.Action] | EllipsisType
#     nargs: int | str | None
#     const: Any
#     default: Any
#     type: Any
#     choices: Iterable[Any] | None | EllipsisType
#     required: bool | EllipsisType
#     help: str | None | EllipsisType
#     metavar: str | tuple[str, ...] | None | EllipsisType
#     dest: str | None | EllipsisType
#     version: str | EllipsisType


class Identifier:
    def __init__(self, obj) -> None:
        self.obj = obj


class CustomAction(Identifier): ...


class Object:
    def __init__(self, name: str, help: str = "") -> None:
        self.name = name
        self.help = help

    def __repr__(self) -> str:
        return f"{self.name!r} {self.help}"


class Help(Identifier): ...


class MetaVar(Identifier): ...


class ConstVar(Identifier): ...


class Group(Identifier): ...


class Action(Enum):
    STORE = Object("STORE", "default action")
    CONST = STORE_CONST = Object("action='store_const'")
    COUNT = Object("COUNT", "action='count'")  # 重复出现时累加计数
    APPEND = Object("APPEND", "action='append'")  # 每次出现追加单个值
    EXTEND = Object("EXTEND", "action='extend'")  # 每次出现扩展多个值
    #
    MUTEX = Object("MUTEX", "add_mutually_exclusive_group()")  # 互斥组，非 action 取值
    APDCST = APPEND_CONST = Object("APPEND_CONST")  # 追加固定常量


# ---- 参数修饰：对应 add_argument(...) 的关键字参数 ----
REQUIRED = Object("REQUIRED", "required=True")  # 必填
DEPRECATED = Object("DEPRECATED", "deprecated=True")  # 已弃用
# SUPPRESS = Object("SUPPRESS", "argparse.SUPPRESS")  # 隐藏帮助信息
