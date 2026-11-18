from .definitions import *


def main() -> None:
    print("Hello from argsig!")


def Amber[**P, R](func: Callable[P, R]) -> Function[P, R]:
    """将普通函数包裹为支持 CLI 的 Function 对象。

    'Amber' 寓意琥珀包裹古生物：它完整保留原函数的参数签名（**P）和返回类型（R），
    在赋予其命令行（CLI）能力的同时，不改变它在 Python 代码中的调用方式和类型提示。
    """
    return Function(func)


def Argument(version: str = "", parser=None):
    """具备更多自定义选项的装饰器"""

    def Arg_[**P, R](func: Callable[P, R]) -> Function[P, R]:
        return Function(func, version, parser=parser)

    return Arg_
