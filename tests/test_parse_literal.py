# test_parse_literal.py
from enum import IntEnum
from typing import Annotated, Literal, Optional, Union

import pytest

# 假设 parse_literal 在模块 parse_module 里
from argsig.parse import parse_literal

# ---------- 正常路径 ----------


class TestValid:
    def test_single_int(self):
        typ, args = parse_literal(Literal[1])
        assert typ is int
        assert args == (1,)

    def test_multi_int(self):
        typ, args = parse_literal(Literal[1, 2, 3])
        assert typ is int
        assert args == (1, 2, 3)

    def test_single_str(self):
        typ, args = parse_literal(Literal["a"])
        assert typ is str
        assert args == ("a",)

    def test_multi_str(self):
        typ, args = parse_literal(Literal["a", "b", "c"])
        assert typ is str
        assert args == ("a", "b", "c")

    def test_negative_int(self):
        typ, args = parse_literal(Literal[-1, 0])
        assert typ is int
        assert args == (-1, 0)

    def test_empty_str_candidate(self):
        typ, args = parse_literal(Literal[""])
        assert typ is str
        assert args == ("",)

    def test_literal_alias(self):
        from typing import Literal as L

        T = L[1, 2]
        typ, args = parse_literal(T)
        assert typ is int
        assert args == (1, 2)

    def test_duplicate_values_merged_by_typing(self):
        # typing 会去重，get_args 返回去重后的
        typ, args = parse_literal(Literal[1, 1, 2])
        assert typ is int
        assert args == (1, 2)


# ---------- 非 Literal ----------


class TestNotLiteral:
    @pytest.mark.parametrize(
        "bad",
        [
            int,
            str,
            list,
            None,
            Optional[int],
            Union[int, str],
            list[int],
        ],
    )
    def test_rejects_non_literal(self, bad):
        with pytest.raises(TypeError, match="期望 Literal"):
            parse_literal(bad)


# ---------- bool 拒绝 ----------


class TestBoolRejected:
    def test_only_true(self):
        with pytest.raises(TypeError, match="不支持 bool"):
            parse_literal(Literal[True])

    def test_only_false(self):
        with pytest.raises(TypeError, match="不支持 bool"):
            parse_literal(Literal[False])

    def test_true_false(self):
        with pytest.raises(TypeError, match="不支持 bool"):
            parse_literal(Literal[True, False])

    def test_bool_mixed_with_int(self):
        with pytest.raises(TypeError, match="不支持 bool"):
            parse_literal(Literal[1, True])

    def test_bool_mixed_with_str(self):
        with pytest.raises(TypeError, match="不支持 bool"):
            parse_literal(Literal["a", False])


# ---------- 混类型 / 不支持的类型 ----------


class TestUnsupportedTypes:
    def test_int_and_str_mixed(self):
        with pytest.raises(TypeError, match="不受支持或不统一"):
            parse_literal(Literal[1, "a"])

    def test_float(self):
        with pytest.raises(TypeError, match="不受支持或不统一"):
            parse_literal(Literal[1.5])

    def test_bytes(self):
        with pytest.raises(TypeError, match="不受支持或不统一"):
            parse_literal(Literal[b"x"])

    def test_none(self):
        with pytest.raises(TypeError, match="不受支持或不统一"):
            parse_literal(Literal[None])

    def test_mixed_none_and_int(self):
        with pytest.raises(TypeError, match="不受支持或不统一"):
            parse_literal(Literal[1, None])

    def test_enum_member(self):
        class C(IntEnum):
            A = 1

        # 若设计上要拒 IntEnum，则期望报错；否则改成断言收下
        with pytest.raises(TypeError, match="不受支持或不统一"):
            parse_literal(Literal[C.A])


# ---------- Annotated 包裹 - ---------


class TestAnnotated:
    def test_annotated_literal_rejected(self):
        # docstring 声明只接受裸 Literal
        with pytest.raises(TypeError, match="期望 Literal"):
            parse_literal(Annotated[Literal[1], "meta"])


# ---------- 空 Literal ----------


class TestEmpty:
    def test_empty_literal(self):
        with pytest.raises((ValueError, TypeError)):
            parse_literal(Literal[()])
