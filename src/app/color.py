"""ANSI terminal color constants."""


class Color:
    """ANSI escape codes for terminal colors."""

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
        """Get color code for HTTP method."""
        return Color._METHOD_COLORS.get(m, Color.RESET)
