"""
ANSI 终端颜色常量
ANSI terminal color constants.
"""


class Color:
    """
    终端 ANSI 转义码颜色定义
    ANSI escape codes for terminal colors.
    """

    RESET = "\033[0m"
    DIM = "\033[2m"
    BLUE = "\033[34m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    BOLD = "\033[1m"

    _METHOD_COLORS = {
        "GET": GREEN,
        "POST": BLUE,
        "PUT": YELLOW,
        "DELETE": RED,
        "PATCH": MAGENTA,
    }

    @staticmethod
    def method(m: str) -> str:
        """
        获取 HTTP 方法对应的颜色代码
        Get color code for HTTP method.
        """
        return Color._METHOD_COLORS.get(m, Color.RESET)
