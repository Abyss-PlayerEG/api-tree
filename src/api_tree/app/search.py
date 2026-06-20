import re


def is_regex_search(search: str) -> bool:
    return search.startswith("$:{") and search.endswith("}")


def extract_regex_pattern(search: str) -> str:
    return search[3:-1]


def match_search(text: str, search: str) -> bool:
    if is_regex_search(search):
        pattern = extract_regex_pattern(search)
        try:
            return bool(re.search(pattern, text, re.IGNORECASE))
        except re.error:
            return False
    return search in text
