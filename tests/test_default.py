import pytest

from argsig.parse import encode

# name or flags：参数名。'foo' 是位置参数；'-f', '--foo' 是可选参数。
# action：参数出现时的处理动作。默认是 'store'。
# nargs：该参数消耗的命令行参数个数。
# default：参数未提供时的默认值。
# type：将命令行字符串转换为指定类型（如 int, float）。
# choices：限制参数值在一个允许的序列内。
# required：可选参数是否必须提供（仅对可选参数有效）。
# help：帮助信息。
# metavar：在帮助信息中显示的参数值名称。
# dest：解析结果中存储的属性名。


def test__name_or_flags():
    print()
    encode("name", int | None, 0, kind="/")
