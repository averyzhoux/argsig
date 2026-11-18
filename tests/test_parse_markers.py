"""test_parse_markers.py — parse_markers 的完整单元测试（匹配真实实现）。

实现约定（与本测试对齐）：
- parse_markers(markers) -> (kws, lbls)
  * kws  ：传给 argparse.add_argument 的关键字参数
  * lbls ：{"group": Group|None, "action": Action|None}，供调用方处理语义
- 输入先行规范化：str → (str,)；然后按 Object / Action / CustomAction / tuple 分派。
- Group 实例写入 lbls["group"]。
- Action.APDCST / Action.MUTEX 写入 lbls["action"]（不写 kws）。
- 元组 (Action.STORE_CONST, value) → kws["action"]="store_const" + kws["const"]=value。
- 元组 (<symbol>|<int>|<decimal-str>[, const]) → kws["nargs"]、可选 kws["const"]。
- 裸 Action.CONST / Action.STORE_CONST 落入 else → TypeError。
- 未知 Object → ValueError。
- 元组长度 > 2 → ValueError。
"""

from __future__ import annotations

import argparse

import pytest

from argsig.parse import parse_markers
from argsig.consts import (
    Action,
    CustomAction,
    DEPRECATED,
    Group,
    Object,
    REQUIRED,
)


def _parse(markers):
    """把 (kws, lbls) 拆成两个断言友好的值。"""
    return parse_markers(markers)


def kws_of(markers):
    return _parse(markers)[0]


def lbls_of(markers):
    return _parse(markers)[1]


# ============================================================
# 1. 正常路径：Object 标记
# ============================================================

class TestObjectMarkers:
    def test_deprecated(self):
        assert kws_of({DEPRECATED}) == {"deprecated": True}

    def test_required(self):
        assert kws_of({REQUIRED}) == {"required": True}

    def test_both(self):
        assert kws_of({DEPRECATED, REQUIRED}) == {
            "deprecated": True,
            "required": True,
        }

    def test_empty(self):
        kws, lbls = parse_markers(set())
        assert kws == {}
        assert lbls == {"group": None, "action": None}

    def test_object_does_not_touch_lbls(self):
        _, lbls = parse_markers({DEPRECATED, REQUIRED})
        assert lbls == {"group": None, "action": None}


# ============================================================
# 2. 正常路径：Action 标记
# ============================================================

class TestActionMarkers:
    def test_store_is_default_noop(self):
        kws, lbls = parse_markers({Action.STORE})
        assert kws == {}
        assert lbls == {"group": None, "action": None}

    def test_count(self):
        assert kws_of({Action.COUNT}) == {"action": "count"}

    def test_append(self):
        assert kws_of({Action.APPEND}) == {"action": "append"}

    def test_extend(self):
        assert kws_of({Action.EXTEND}) == {"action": "extend"}

    def test_apdcst_writes_lbls_not_kws(self):
        # 关键契约：APDCST 只进 lbls，不进 kws
        kws, lbls = parse_markers({Action.APDCST})
        assert kws == {}
        assert lbls["action"] is Action.APDCST

    def test_mutex_writes_lbls_not_kws(self):
        kws, lbls = parse_markers({Action.MUTEX})
        assert kws == {}
        assert lbls["action"] is Action.MUTEX

    def test_apdcst_is_append_const_alias(self):
        assert Action.APDCST is Action.APPEND_CONST

    def test_const_is_store_const_alias(self):
        assert Action.CONST is Action.STORE_CONST


# ============================================================
# 3. 正常路径：CustomAction
# ============================================================

class TestCustomAction:
    def test_writes_obj(self):
        sentinel = object()
        assert kws_of({CustomAction(sentinel)}) == {"action": sentinel}

    def test_with_deprecated(self):
        sentinel = object()
        kws = kws_of({CustomAction(sentinel), DEPRECATED})
        assert kws == {"action": sentinel, "deprecated": True}


# ============================================================
# 4. 正常路径：tuple 标记
# ============================================================

class TestTupleMarkers:
    def test_store_const_with_value(self):
        assert kws_of({(Action.STORE_CONST, 42)}) == {
            "action": "store_const",
            "const": 42,
        }

    def test_const_alias_with_value(self):
        # Action.CONST is Action.STORE_CONST，同样命中 store_const 分支
        assert kws_of({(Action.CONST, "x")}) == {
            "action": "store_const",
            "const": "x",
        }

    @pytest.mark.parametrize("nargs", ["*", "+", "?", "..."])
    def test_nargs_symbolic(self, nargs):
        assert kws_of({(nargs,)}) == {"nargs": nargs}

    @pytest.mark.parametrize("nargs", [1, 2, 3, 10])
    def test_nargs_int(self, nargs):
        assert kws_of({(nargs,)}) == {"nargs": nargs}

    @pytest.mark.parametrize("s, expected", [("1", 1), ("2", 2), ("10", 10)])
    def test_nargs_decimal_string(self, s, expected):
        assert kws_of({(s,)}) == {"nargs": expected}

    @pytest.mark.parametrize("nargs", ["*", "+", "?", "..."])
    def test_nargs_symbolic_with_const(self, nargs):
        assert kws_of({(nargs, "default_val")}) == {
            "nargs": nargs,
            "const": "default_val",
        }

    def test_nargs_int_with_const(self):
        assert kws_of({(2, "picked")}) == {"nargs": 2, "const": "picked"}

    def test_fullwidth_digit_string(self):
        # "１２３".isdecimal() True，int() 可解析为 123
        assert kws_of({("１２３",)}) == {"nargs": 123}


# ============================================================
# 5. 正常路径：裸字符串规范化
# ============================================================

class TestStrNormalization:
    """裸字符串先被包成 (s,)，再走 tuple 分支。"""

    def test_bare_star(self):
        assert kws_of({"*"}) == {"nargs": "*"}

    def test_bare_plus(self):
        assert kws_of({"+"}) == {"nargs": "+"}

    def test_bare_question_mark(self):
        assert kws_of({"?"}) == {"nargs": "?"}

    def test_bare_dots(self):
        assert kws_of({"..."}) == {"nargs": "..."}

    def test_bare_decimal(self):
        assert kws_of({"3"}) == {"nargs": 3}


# ============================================================
# 6. 正常路径：Group
# ============================================================

class TestGroupMarkers:
    def test_group_writes_lbls(self):
        g = Group("g1")
        kws, lbls = parse_markers({g})
        assert kws == {}
        assert lbls["group"] is g


# ============================================================
# 7. 混合输入
# ============================================================

class TestMixed:
    def test_multiple_categories(self):
        kws, lbls = parse_markers({DEPRECATED, Action.COUNT, REQUIRED})
        assert kws == {"deprecated": True, "required": True, "action": "count"}
        assert lbls == {"group": None, "action": None}

    def test_action_and_nargs(self):
        assert kws_of({Action.APPEND, ("2",)}) == {
            "action": "append",
            "nargs": 2,
        }

    def test_store_const_with_required(self):
        assert kws_of({(Action.CONST, "on"), REQUIRED}) == {
            "action": "store_const",
            "const": "on",
            "required": True,
        }

    def test_group_and_action_in_lbls(self):
        g = Group("g")
        _, lbls = parse_markers({g, Action.APDCST})
        assert lbls["group"] is g
        assert lbls["action"] is Action.APDCST


# ============================================================
# 8. 输入类型兼容
# ============================================================

class TestInputTypes:
    def test_accepts_list_input(self):
        assert kws_of([Action.COUNT]) == {"action": "count"}

    def test_accepts_tuple_input(self):
        assert kws_of((Action.APPEND,)) == {"action": "append"}

    def test_accepts_generator_input(self):
        # set 推导 / 集合构造依赖 iterable，generator 也可
        assert kws_of((a for a in [Action.EXTEND])) == {"action": "extend"}

    def test_set_iteration_is_deterministic_for_dict_content(self):
        # 集合顺序不定但字典内容相同
        a = kws_of({DEPRECATED, Action.COUNT})
        b = kws_of({Action.COUNT, DEPRECATED})
        assert a == b


# ============================================================
# 9. 错误路径
# ============================================================

class TestErrors:
    def test_unknown_object(self):
        with pytest.raises(ValueError, match="未知 Object 标记"):
            parse_markers({Object("UNKNOWN")})

    def test_unknown_type(self):
        with pytest.raises(TypeError, match="无法识别的标记"):
            parse_markers({12345})

    def test_empty_tuple(self):
        with pytest.raises(ValueError, match="标记元组不能为空"):
            parse_markers({()})

    def test_bad_nargs_string(self):
        with pytest.raises(ValueError, match="无法解析的 nargs 字符串标记"):
            parse_markers({("abc",)})

    def test_zero_nargs_string_rejected(self):
        with pytest.raises(ValueError, match="无法解析的 nargs 字符串标记"):
            parse_markers({("0",)})

    def test_superscript_rejected(self):
        # "²".isdigit() True 但 .isdecimal() False，进入错误分支
        with pytest.raises(ValueError, match="无法解析的 nargs 字符串标记"):
            parse_markers({("²",)})

    def test_negative_int_nargs_rejected(self):
        with pytest.raises(ValueError, match="无法解析的标记元组首元素"):
            parse_markers({(-1,)})

    def test_zero_int_nargs_rejected(self):
        with pytest.raises(ValueError, match="无法解析的标记元组首元素"):
            parse_markers({(0,)})

    def test_bool_rejected(self):
        # True 是 int 子类，但 type(t) is int 排除它
        with pytest.raises(ValueError, match="无法解析的标记元组首元素"):
            parse_markers({(True,)})

    def test_bad_tuple_first_element(self):
        with pytest.raises(ValueError, match="无法解析的标记元组首元素"):
            parse_markers({(object(),)})

    def test_bare_const_action_rejected(self):
        # 裸 Action.CONST 落入 Action 分支 else（未被单独处理）
        with pytest.raises(TypeError, match="未处理的 Action 标记"):
            parse_markers({Action.CONST})

    def test_bare_store_const_action_rejected(self):
        with pytest.raises(TypeError, match="未处理的 Action 标记"):
            parse_markers({Action.STORE_CONST})


# ============================================================
# 10. 刻意设计边界（契约固化）
# ============================================================

class TestIntendedDesignEdges:
    """这些不是 bug，是刻意设计。固化契约，防止未来回归。"""

    def test_tuple_extra_elements_rejected(self):
        with pytest.raises(ValueError, match="标记元组最多 2 个元素"):
            parse_markers({(Action.CONST, 42, "ignored", 999)})

    def test_tuple_three_elements_rejected(self):
        with pytest.raises(ValueError, match="标记元组最多 2 个元素"):
            parse_markers({("*", "const_val", "extra")})

    def test_last_write_wins_for_action(self):
        # kws["action"] 被多来源写时后写覆盖；set 顺序不定 → 结果是其中之一
        kws = kws_of({Action.APPEND, Action.COUNT})
        assert kws["action"] in ("append", "count")

    def test_last_write_wins_for_nargs(self):
        kws = kws_of({("*",), ("+",)})
        assert kws["nargs"] in ("*", "+")

    def test_custom_action_overrides_or_is_overridden(self):
        sentinel = object()
        kws = kws_of({CustomAction(sentinel), Action.COUNT})
        assert kws["action"] in (sentinel, "count")

    def test_store_does_not_override_other_action(self):
        # STORE 是 no-op，不写键；与 COUNT 共存时只有 COUNT 生效
        assert kws_of({Action.STORE, Action.COUNT}) == {"action": "count"}

    def test_apdcst_and_mutex_in_lbls_when_both(self):
        # APDCST 与 MUTEX 都写 lbls["action"]，后者覆盖前者（顺序不定，只断言其一）
        _, lbls = parse_markers({Action.APDCST, Action.MUTEX})
        assert lbls["action"] in (Action.APDCST, Action.MUTEX)

    def test_group_and_action_independent_labels(self):
        g = Group("g")
        _, lbls = parse_markers({g, Action.APDCST})
        assert lbls == {"group": g, "action": Action.APDCST}


# ============================================================
# 11. 与 argparse 的集成冒烟测试
# ============================================================

class TestArgparseIntegration:
    def test_count_integration(self):
        parser = argparse.ArgumentParser()
        kws, _ = parse_markers({Action.COUNT})
        parser.add_argument("--verbose", **kws)

        assert parser.parse_args(["--verbose", "--verbose"]).verbose == 2
        assert parser.parse_args([]).verbose is None

    def test_store_const_integration(self):
        parser = argparse.ArgumentParser()
        kws, _ = parse_markers({(Action.CONST, "on")})
        parser.add_argument("--flag", **kws)

        assert parser.parse_args(["--flag"]).flag == "on"
        assert parser.parse_args([]).flag is None

    def test_nargs_integration(self):
        parser = argparse.ArgumentParser()
        kws, _ = parse_markers({(2,)})
        parser.add_argument("--pair", **kws)

        assert parser.parse_args(["--pair", "a", "b"]).pair == ["a", "b"]

    def test_question_mark_nargs_integration(self):
        parser = argparse.ArgumentParser()
        kws, _ = parse_markers({("?", "auto")})
        parser.add_argument("--color", default=None, **kws)

        assert parser.parse_args([]).color is None
        assert parser.parse_args(["--color"]).color == "auto"
        assert parser.parse_args(["--color", "red"]).color == "red"

    def test_star_nargs_integration(self):
        parser = argparse.ArgumentParser()
        kws, _ = parse_markers({("*",)})
        parser.add_argument("--items", **kws)

        assert parser.parse_args([]).items is None
        assert parser.parse_args(["--items", "a", "b", "c"]).items == ["a", "b", "c"]

    def test_deprecated_not_a_kwarg_for_argparse(self):
        # deprecated 是 argsig 自有语义 → 调用方需剥离
        kws, _ = parse_markers({DEPRECATED, Action.COUNT})
        assert "deprecated" in kws

        argparse_kws = {k: v for k, v in kws.items() if k != "deprecated"}
        parser = argparse.ArgumentParser()
        parser.add_argument("--x", **argparse_kws)
        assert parser.parse_args(["--x", "--x"]).x == 2

    def test_required_is_a_kwarg_for_argparse(self):
        parser = argparse.ArgumentParser()
        kws, _ = parse_markers({REQUIRED})
        parser.add_argument("--name", **kws)

        with pytest.raises(SystemExit):
            parser.parse_args([])
        assert parser.parse_args(["--name", "x"]).name == "x"

    def test_lbls_only_markers_do_not_affect_argparse(self):
        # APDCST / Group 只进 lbls；把它们剥掉后 kws 为空也能 add_argument
        g = Group("g")
        kws, lbls = parse_markers({Action.APDCST, g})
        assert kws == {}
        assert lbls["action"] is Action.APDCST and lbls["group"] is g

        parser = argparse.ArgumentParser()
        parser.add_argument("--y", **kws)  # 无 action / nargs → 走默认 store
        assert parser.parse_args(["--y", "1"]).y == "1"
