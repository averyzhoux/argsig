import argparse
import inspect
from typing import Annotated, List, Literal, Optional, Union

import pytest

from argsig.parse import parse_hint

EMPTY = inspect.Parameter.empty


# ============================================================
# 基础类型：empty / int / str
# ============================================================


@pytest.mark.parametrize(
    "annotation, expected",
    [
        (EMPTY, {"action": "store"}),
        (int, {"action": "store", "type": int}),
        (str, {"action": "store", "type": str}),
    ],
    ids=["empty", "int", "str"],
)
def test_basic_types(annotation, expected):
    assert parse_hint(annotation) == expected


# ============================================================
# bool：依赖 default
# ============================================================


@pytest.mark.parametrize(
    "default, expected_action",
    [(True, "store_false"), (False, "store_true")],
    ids=["default_true", "default_false"],
)
def test_bool_valid_default(default, expected_action):
    assert parse_hint(bool, default) == {"action": expected_action}


@pytest.mark.parametrize(
    "default",
    [EMPTY, None, 1, 0, "yes", [], object()],
    ids=["empty", "none", "int1", "int0", "str", "list", "object"],
)
def test_bool_invalid_default_raises(default):
    with pytest.raises(ValueError, match="布尔开关参数"):
        parse_hint(bool, default)


# ============================================================
# 裸 list
# ============================================================


def test_bare_list():
    assert parse_hint(list) == {"action": "store", "nargs": "*"}


# ============================================================
# list[T]
# ============================================================


@pytest.mark.parametrize(
    "annotation, expected",
    [
        (list[int], {"action": "store", "nargs": "*", "type": int}),
        (list[str], {"action": "store", "nargs": "*", "type": str}),
        (List[int], {"action": "store", "nargs": "*", "type": int}),
    ],
    ids=["builtin_int", "builtin_str", "typing_List_int"],
)
def test_list_of_basic(annotation, expected):
    assert parse_hint(annotation) == expected


def test_list_of_literal_str():
    kws = parse_hint(list[Literal["a", "b"]])
    assert kws["nargs"] == "*"
    assert kws["type"] is str
    assert set(kws["choices"]) == {"a", "b"}


def test_list_of_literal_int():
    kws = parse_hint(list[Literal[1, 2, 3]])
    assert kws["nargs"] == "*"
    assert kws["type"] is int
    assert set(kws["choices"]) == {1, 2, 3}


@pytest.mark.parametrize(
    "annotation",
    [list[float], list[bytes], list[list[int]]],
    ids=["float", "bytes", "nested"],
)
def test_list_of_unsupported_raises(annotation):
    with pytest.raises(TypeError, match="不支持的 List 注解"):
        parse_hint(annotation)


# ============================================================
# Literal
# ============================================================


def test_literal_str():
    kws = parse_hint(Literal["x", "y"])
    assert kws["type"] is str
    assert set(kws["choices"]) == {"x", "y"}


def test_literal_int():
    kws = parse_hint(Literal[1, 2, 3])
    assert kws["type"] is int
    assert set(kws["choices"]) == {1, 2, 3}


@pytest.mark.parametrize(
    "annotation",
    [Literal[True, False], Literal[1, "a"]],
    ids=["bool_candidates", "mixed_types"],
)
def test_literal_unsupported_raises(annotation):
    with pytest.raises(TypeError):
        parse_hint(annotation)


# ============================================================
# Union / Optional（PEP604 与 typing.Union 双份覆盖）
# ============================================================


def test_union_bool_none():
    kws = parse_hint(Union[bool, None], default=False)
    assert kws["action"] is argparse.BooleanOptionalAction


def test_pep604_bool_none():
    kws = parse_hint(bool | None, default=False)
    assert kws["action"] is argparse.BooleanOptionalAction


def test_union_int_none():
    assert parse_hint(Union[int, None]) == {"action": "store", "type": int}


def test_pep604_int_none():
    assert parse_hint(int | None) == {"action": "store", "type": int}


def test_union_str_none():
    assert parse_hint(Union[str, None]) == {"action": "store", "type": str}


def test_pep604_str_none():
    assert parse_hint(str | None) == {"action": "store", "type": str}


def test_optional_alias():
    assert parse_hint(Optional[int]) == {"action": "store", "type": int}


@pytest.mark.parametrize(
    "annotation",
    [Union[int, str], Union[float, None], int | str, int | float | None],
    ids=["int-str", "float-none", "pep604-int-str", "int-float-none"],
)
def test_union_unsupported_raises(annotation):
    with pytest.raises(TypeError, match="Union"):
        parse_hint(annotation)


# ============================================================
# Annotated
# ============================================================


def test_annotated_int_ignores_metadata():
    # 契约：metadata 被忽略，只取真实类型
    assert parse_hint(Annotated[int, "help=x"]) == {"action": "store", "type": int}


def test_annotated_bool_passes_default():
    """回归测试：Annotated 递归必须透传 default，否则 bool 分支会炸。"""
    kws = parse_hint(Annotated[bool, "meta"], default=True)
    assert kws["action"] == "store_false"


def test_annotated_nested_literal():
    kws = parse_hint(Annotated[Literal["a", "b"], "meta"])
    assert kws["type"] is str
    assert set(kws["choices"]) == {"a", "b"}


# ============================================================
# 不支持的裸类型
# ============================================================


@pytest.mark.parametrize(
    "annotation",
    [float, bytes, dict, tuple, set, type(None), object],
    ids=["float", "bytes", "dict", "tuple", "set", "none", "object"],
)
def test_unsupported_bare_types_raise(annotation):
    with pytest.raises(TypeError, match="不支持的类型注解"):
        parse_hint(annotation)


# ============================================================
# 集成：产出的 kws 真的能喂给 argparse
# ============================================================


def _build_parser(**kws):
    p = argparse.ArgumentParser()
    p.add_argument("--x", **kws)
    return p


def test_integration_int():
    p = _build_parser(**parse_hint(int))
    assert p.parse_args(["--x", "42"]).x == 42


def test_integration_literal():
    p = _build_parser(**parse_hint(Literal["a", "b"]))
    assert p.parse_args(["--x", "a"]).x == "a"
    with pytest.raises(SystemExit):
        p.parse_args(["--x", "c"])


def test_integration_list_int():
    p = _build_parser(**parse_hint(list[int]))
    assert p.parse_args(["--x", "1", "2", "3"]).x == [1, 2, 3]


def test_integration_bool_default_true():
    kws = parse_hint(bool, default=True)
    kws["default"] = True  # 模拟上层统一注入 default
    p = _build_parser(**kws)
    assert p.parse_args([]).x is True
    assert p.parse_args(["--x"]).x is False


def test_integration_bool_default_false():
    kws = parse_hint(bool, default=False)
    kws["default"] = False
    p = _build_parser(**kws)
    assert p.parse_args([]).x is False
    assert p.parse_args(["--x"]).x is True


def test_integration_optional_int():
    kws = parse_hint(int | None)
    kws["default"] = None
    p = _build_parser(**kws)
    assert p.parse_args([]).x is None
    assert p.parse_args(["--x", "5"]).x == 5


# 补 1：list[bool] 不应被当作 list[int]
@pytest.mark.parametrize(
    "annotation",
    [list[float], list[bytes], list[list[int]], list[bool]],
    ids=["float", "bytes", "nested", "bool"],
)
def test_list_of_unsupported_raises1(annotation):
    with pytest.raises(TypeError, match="不支持的 List 注解"):
        parse_hint(annotation)


# 补 2：list[Literal[非法]] 的异常要穿透出来
@pytest.mark.parametrize(
    "annotation",
    [list[Literal[True, False]], list[Literal[1, "a"]]],
    ids=["literal_bool", "literal_mixed"],
)
def test_list_of_illegal_literal_raises(annotation):
    with pytest.raises(TypeError):
        parse_hint(annotation)
