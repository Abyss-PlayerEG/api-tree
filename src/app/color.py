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

    @staticmethod
    def method(m: str) -> str:
        """Get color code for HTTP method."""
        return {
            "GET": Color.GREEN,
            "POST": Color.BLUE,
            "PUT": Color.YELLOW,
            "DELETE": Color.RED,
            "PATCH": Color.MAGENTA,
        }.get(m, Color.RESET)
