# test_parse_infoma.py
import pytest

from argsig.parse import parse_infoma, Help, MetaVar


# ---------- 辅助类：Help / MetaVar 的最小假设 ----------
# 若真实定义不同，请按实际导入。这里只依赖 .obj 属性。


# ---------- 基础测试 ----------

class TestLongFlag:
    def test_double_dash_expands_to_long_name(self):
        kws, nms = parse_infoma("my_arg", ["--"])
        assert nms == ["--my-arg"]
        assert kws == {}

    def test_double_dash_uses_xname_with_underscores_replaced(self):
        kws, nms = parse_infoma("foo_bar_baz", ["--"])
        assert nms == ["--foo-bar-baz"]

    def test_explicit_long_flag_passes_through(self):
        kws, nms = parse_infoma("my_arg", ["--explicit"])
        assert nms == ["--explicit"]


class TestShortFlag:
    def test_single_dash_expands_to_first_char(self):
        kws, nms = parse_infoma("verbose", ["-"])
        assert nms == ["-v"]

    def test_single_dash_after_underscore_replacement(self):
        # name "x_name" -> xname "x-name" -> xname[0] == "x"
        kws, nms = parse_infoma("x_name", ["-"])
        assert nms == ["-x"]

    def test_explicit_short_flag_passes_through(self):
        kws, nms = parse_infoma("my_arg", ["-q"])
        assert nms == ["-q"]


class TestPlainString:
    def test_uppercase_string_becomes_metavar(self):
        kws, nms = parse_infoma("arg", ["FILE"])
        assert kws == {"metavar": "FILE"}
        assert nms == []

    def test_non_uppercase_string_becomes_help(self):
        kws, nms = parse_infoma("arg", ["some help text"])
        assert kws == {"help": "some help text"}

    def test_mixed_case_is_help(self):
        kws, nms = parse_infoma("arg", ["File"])
        assert kws["help"] == "File"
        assert "metavar" not in kws

    def test_help_with_special_chars(self):
        kws, _ = parse_infoma("arg", ["help: value=42"])
        assert kws["help"] == "help: value=42"


class TestTupleMetavar:
    def test_uppercase_tuple_becomes_metavar(self):
        kws, _ = parse_infoma("arg", [("A", "B")])
        assert kws["metavar"] == ("A", "B")

    def test_single_element_uppercase_tuple(self):
        kws, _ = parse_infoma("arg", [("ONLY",)])
        assert kws["metavar"] == ("ONLY",)

    def test_empty_tuple_raises_type_error(self):
        with pytest.raises(TypeError, match="Invalid metavar tuple"):
            parse_infoma("arg", [()])

    def test_tuple_with_lowercase_raises(self):
        with pytest.raises(TypeError, match="Invalid metavar tuple"):
            parse_infoma("arg", [("A", "b")])

    def test_tuple_with_non_string_raises(self):
        with pytest.raises(TypeError, match="Invalid metavar tuple"):
            parse_infoma("arg", [("A", 1)])


class TestHelpAndMetaVarObjects:
    def test_help_object_sets_help(self):
        kws, _ = parse_infoma("arg", [Help("do something")])
        assert kws["help"] == "do something"

    def test_metavar_object_sets_metavar(self):
        kws, _ = parse_infoma("arg", [MetaVar("PATH")])
        assert kws["metavar"] == "PATH"


class TestInvalidTypes:
    def test_int_raises_type_error(self):
        with pytest.raises(TypeError, match="Unsupported infoma item"):
            parse_infoma("arg", [123])

    def test_list_raises_type_error(self):
        with pytest.raises(TypeError, match="Unsupported infoma item"):
            parse_infoma("arg", [["A"]])

    def test_none_raises_type_error(self):
        with pytest.raises(TypeError, match="Unsupported infoma item"):
            parse_infoma("arg", [None])


# ---------- 组合 & 顺序相关 ----------

class TestCombined:
    def test_flag_and_help_and_metavar_together(self):
        kws, nms = parse_infoma("input_file", ["--", "FILE", "input path"])
        assert nms == ["--input-file"]
        assert kws == {"metavar": "FILE", "help": "input path"}

    def test_short_and_long_flags_together(self):
        kws, nms = parse_infoma("verbose", ["-", "--"])
        assert nms == ["-v", "--verbose"]

    def test_order_preserved_in_nms(self):
        _, nms = parse_infoma("x", ["-a", "--", "-b"])
        assert nms == ["-a", "--x", "-b"]

    def test_later_help_overwrites_earlier(self):
        kws, _ = parse_infoma("arg", ["first", "second"])
        assert kws["help"] == "second"

    def test_help_object_overwrites_string_help(self):
        kws, _ = parse_infoma("arg", ["plain text", Help("from object")])
        assert kws["help"] == "from object"

    def test_empty_infoma_returns_empty(self):
        kws, nms = parse_infoma("arg", [])
        assert kws == {}
        assert nms == []

    def test_metavar_string_then_object_overwrites(self):
        kws, _ = parse_infoma("arg", ["OLD", MetaVar("NEW")])
        assert kws["metavar"] == "NEW"


# ---------- xname 转换 ----------

class TestXName:
    def test_underscores_replaced_in_long_flag(self):
        _, nms = parse_infoma("a_b_c", ["--"])
        assert nms == ["--a-b-c"]

    def test_name_without_underscore_unchanged(self):
        _, nms = parse_infoma("plain", ["--"])
        assert nms == ["--plain"]

    def test_multiple_underscores(self):
        _, nms = parse_infoma("a__b", ["--"])
        assert nms == ["--a--b"]

    def test_short_uses_original_first_char_when_no_leading_underscore(self):
        _, nms = parse_infoma("hello_world", ["-"])
        assert nms == ["-h"]


# ---------- 边界/已知行为 ----------

class TestEdgeCases:
    def test_empty_name_short_flag_raises_index_error(self):
        # 现实现未做保护，记录该行为
        with pytest.raises(IndexError):
            parse_infoma("", ["-"])

    def test_leading_underscore_short_flag_yields_double_dash(self):
        # name "_x" -> xname "-x" -> xname[0] "-" -> "--"
        _, nms = parse_infoma("_x", ["-"])
        assert nms == ["--"]

    def test_tuple_all_uppercase_checked_item_by_item(self):
        # 任意一项不大写即失败
        with pytest.raises(TypeError):
            parse_infoma("arg", [("ABC", "ABC", "abc")])
