import argparse
import inspect
import sys
import types
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import (
    Annotated,
    Any,
    Literal,
    Union,
    get_args,
    get_origin,
)

from .consts import *

MISSING = object()


@dataclass
class ParameterSpec:
    name: str  # Python 参数名，如 "output"
    flags: list[str]  # 传给 add_argument 的 name_or_flags，如 ["--out", "-o"]
    kwargs: dict  # add_argument 的其余关键字参数
    dest: str  # Namespace 里的键，通常等于 name
    positional: bool  # True=位置参数，False=可选参数
    group: Group | None = None       # 互斥组/参数组

    def add_to_parser(self): ...


def parse_markers(markers: set):
    kws = {}
    lbls: dict[str, object] = {"group": None, "action": None}

    markers = {(l,) if isinstance(l, str) else l for l in markers}

    for itm in markers:
        if isinstance(itm, Object):
            if itm is DEPRECATED:
                kws["deprecated"] = True
            elif itm is REQUIRED:
                kws["required"] = True
            else:
                raise ValueError(f"未知 Object 标记: {itm!r}")

        elif isinstance(itm, Group):
            lbls["group"] = itm
        elif isinstance(itm, Action):
            # if l in (Action.CONST, Action.STORE_CONST):
            #     kws["action"] = "store_const"

            if itm is Action.STORE:
                pass  # 默认 action，无需设置
            elif itm is Action.COUNT:
                kws["action"] = "count"
            elif itm is Action.APPEND:
                kws["action"] = "append"
            elif itm is Action.EXTEND:
                kws["action"] = "extend"

            elif itm is Action.APDCST:  # APPEND_CONST 是别名
                lbls["action"] = Action.APDCST
            elif itm is Action.MUTEX:  # APPEND_CONST 是别名
                lbls["action"] = Action.MUTEX

            else:
                raise TypeError(f"未处理的 Action 标记: {itm!r}")

        elif isinstance(itm, CustomAction):
            kws["action"] = itm.obj

        elif isinstance(itm, tuple):
            if not itm:
                raise ValueError(f"标记元组不能为空: {itm!r}")

            t = itm[0]

            if t is Action.STORE_CONST:
                kws["action"] = "store_const"
            elif type(t) is str:
                if t in ["?", "*", "+", "..."]:
                    kws["nargs"] = t

                elif t.isdecimal() and int(t) > 0:
                    kws["nargs"] = int(t)

                else:
                    raise ValueError(
                        f"无法解析的 nargs 字符串标记: {t!r}，"
                        f"应为 '*', '+', '...' 或正整数数字串"
                    )

            elif type(t) is int and t > 0:
                kws["nargs"] = t

            else:
                raise ValueError(
                    f"无法解析的标记元组首元素: {t!r}（类型 {type(t).__name__}），"
                    f"应为 Action、str 或正整数 int"
                )

            if len(itm) == 2:
                kws["const"] = itm[1]
            if len(itm) > 2:
                raise ValueError(f"标记元组最多 2 个元素: {itm!r}")

        else:
            raise TypeError(f"无法识别的标记: {itm!r}（类型 {type(itm).__name__}）")
    return kws, lbls


def parse_infoma(name, infoma: list):
    nms = []
    kws = {}
    xname = name.replace("_", "-")
    for m in infoma:
        if isinstance(m, str):
            # 处理 name_or_flags
            if m.startswith("-"):
                if m == "--":
                    nms.append(f"--{xname}")
                elif m == "-":
                    nms.append(f"-{xname[0]}")
                else:
                    nms.append(m)

            # 处理 nargs
            else:
                if m.isupper():
                    kws["metavar"] = m
                else:
                    kws["help"] = m

        elif isinstance(m, tuple):
            if m and all(isinstance(_, str) and _.isupper() for _ in m):
                kws["metavar"] = m
            else:
                raise TypeError(f"Invalid metavar tuple: {m!r}")

        elif isinstance(m, Help):
            kws["help"] = m.obj
        elif isinstance(m, MetaVar):
            kws["metavar"] = m.obj
        elif isinstance(m, ConstVar):
            kws["const"] = m.obj

        else:
            raise TypeError(f"Unsupported infoma item: {m!r}")
    return kws, nms


def parse_metadatas(name: str, metadatas: list[set | list]):

    if not metadatas:
        return {}, {}, []

    markers = set()
    infomas = []
    for m in metadatas:
        if type(m) is set:
            markers = m
            continue

        if type(m) is list:
            infomas.append(m)
            continue

        markers.add(m)

    kws, lbls = parse_markers(markers)
    return kws, lbls, [parse_infoma(name, i) for i in infomas]


def parse_literal(lit):
    """只接受裸 Literal；候选值必须全为纯 int 或全为纯 str。

    拒绝：
    - 非 Literal / 空 Literal
    - bool 候选值（含与 int 混用）
    - int 子类（IntEnum、numpy 整数等）
    - str 子类
    - 混类型、其他类型
    """

    if get_origin(lit) is not Literal:
        raise TypeError(f"期望 Literal[...]，得到 {lit!r}")

    args = get_args(lit)
    if not args:
        raise ValueError("Literal 不能为空")

    if any(a is True or a is False for a in args):
        raise TypeError(f"Literal 不支持 bool 候选值: {args!r}")
    elif all(type(a) is int for a in args):
        return int, args
    elif all(type(a) is str for a in args):
        return str, args
    else:
        raise TypeError(f"Literal 候选值类型不受支持或不统一: {args!r}")


def parse_hint(
    annotation: Any = inspect.Parameter.empty,
    default: Any = inspect.Parameter.empty,
    *,
    name: str = "?",
):
    # 返回 argparse.add_argument 的关键字参数：
    # 可能包含 action / type / choices / nargs

    _OPT = type(None)
    kws: dict[str, Any] = {"action": "store"}
    metadatas = []
    origin, args = get_origin(annotation), get_args(annotation)

    if annotation is inspect.Parameter.empty:
        pass

    elif annotation in (int, str):
        kws["type"] = annotation

    elif annotation is bool:
        if default is True:
            kws["action"] = "store_false"
        elif default is False:
            kws["action"] = "store_true"
        else:
            raise ValueError(f"布尔开关参数 {name} 必须显式设为 True 或 False")

    elif annotation is list:
        kws.setdefault("nargs", "*")

    elif origin is not None:
        if origin is Annotated:
            real_type, *metadatas = args
            _ret, *_ = parse_hint(real_type, default)
            kws.update(_ret)
        elif origin in (types.UnionType, Union):
            argset = frozenset(args)
            if argset == {bool, _OPT}:
                kws["action"] = argparse.BooleanOptionalAction
            elif argset == {int, _OPT}:
                kws["type"] = int
            elif argset == {str, _OPT}:
                kws["type"] = str
            else:
                raise TypeError(f"暂不支持的 Union 注解: {annotation!r}")

        elif origin is list:
            if len(args) != 1:
                raise TypeError(f"list 注解必须恰好一个类型参数: {annotation!r}")
            kws.setdefault("nargs", "*")
            _type = args[0]
            if _type in (int, str):
                kws["type"] = _type
            elif get_origin(_type) is Literal:
                kws["type"], kws["choices"] = parse_literal(_type)
            else:
                raise TypeError(f"不支持的 List 注解: {annotation!r}")

        elif origin is Literal:
            kws["type"], kws["choices"] = parse_literal(annotation)

        else:
            raise TypeError(f"不支持的类型注解: {annotation!r}")
    else:
        raise TypeError(f"不支持的类型注解: {annotation!r}")

    _kws, lbls, params = parse_metadatas(name, metadatas)
    kws.update(_kws)
    return kws, lbls, params


def encode(
    name: str,
    annotation: Any = inspect.Parameter.empty,
    default: Any = inspect.Parameter.empty,
    *,
    kind: Literal["/", "|", "*"] = "|",
):

    xname = name.replace("_", "-")
    nms = []
    kws, lbls, params = parse_hint(annotation, default, name=name)

    if g := lbls.get("group"):
        if not isinstance(g, Group):
            raise ValueError
        raise NotImplementedError
    else:
        if a := lbls.get("action"):
            if a in (Action.MUTEX, Action.APPEND_CONST):
                raise ValueError
            raise NotImplementedError
        else:
            if len(params) == 0:
                nms.extend([f"-{xname[0]}", f"--{xname}"])
            elif len(params) == 1:
                _kws, _nms = params[0]
                kws.update(_kws)
                nms.extend(_nms)
            else:
                raise ValueError

    if kind == "/":
        nms = [name]
    if kind == "*":
        nms = [n for n in nms if n != name]

    if default is not inspect.Parameter.empty:
        kws["default"] = default

    return nms, kws
