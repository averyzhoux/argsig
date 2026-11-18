import argparse
from typing import Annotated, Literal

import argsig as ars


class AppendConst[T](list):
    pass


class Count(int):
    pass


GX = ars.Group("group-1")


class CustomActionExample(argparse.Action):
    pass


# 三级标记，和css类似


@ars.Argument("v0.1.0", argparse.ArgumentParser())  # , makers={})  # 外部样式
def test_names_flags():

    def x(
        a: int,  # name
        b: Annotated[int, {ars.REQUIRED}, ["--"]],  # required
        d: Annotated[
            list,  # action=append_const
            {ars.Action.APDCST},  # 内部样式
            ["--a", "-a", "const-value", {ars.SUPPRESS}],  # 内联样式
            ["--b", "-b", "const-value"],
        ],
        n: Annotated[
            str,  # action=append_const
            {ars.Action.MUTEX, GX},
            ["--json", "json"],
            ["--yaml", "yaml"],
        ],
        z: Annotated[str, {("?", "const-value")}, []],
        i: Annotated[list, {"*"}, []],  # nargs='*'
        j: Annotated[list, {"+"}, []],  # nargs='+'
        k: Annotated[
            tuple, {"3", ars.DEPRECATED}, []
        ],  # nargs='3'，后面会转成 3 ，此处为了对其。
        ii: Annotated[list, {"..."}, []],  # REMAINDER
        e: Annotated[bool, []] = True,  # action=store_false
        l: Annotated[
            bool, {ars.CustomAction(CustomActionExample)}, []
        ] = True,  # action=store_false
        f: Annotated[bool, []] = False,  # action=store_true
        g: Annotated[bool | None, []] = None,  # action=BooleanOptionalAction
        h: Annotated[int, {ars.SUPPRESS}, []] = 0,  # action=count
        c: Annotated[  # name  dest
            Literal[1, 2, 3],  # type choices,
            [
                "--",  # flags
                "-",
                "--abc",
                "-c",
                ("A",),  # metavar
                "help",  # help
            ],
        ] = 1,  # default & no-required
    ): ...
