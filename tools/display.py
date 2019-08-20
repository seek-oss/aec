from typing import Dict, List, Any


def as_table(dicts: List[Dict[str, Any]], keys: List[str] = None) -> List[List[str]]:
    """
    Converts a list of dictionaries to a nested list, ordered by specified keys

    :param keys: ordered list of keys to include in each row, or None to use the keys for the first dict
    :param dicts: list of dictionaries
    :return:
    """
    if keys is None:
        keys = list(dicts[0].keys())
    return [keys] + [[str(d.get(f, "")) if d.get(f, "") is not None else None for f in keys] for d in dicts]


def pretty(table: List[List[str]]) -> str:
    """
    Formats a table as a pretty string for printing

    :param table:
    :return:
    """
    padding = 2
    col_width = [0] * len(table[0])
    for row in table:
        for idx, col in enumerate(row):
            if col is not None and len(col) > col_width[idx]:
                col_width[idx] = len(col)

    return "\n".join(
        ["".join(["".join((col if col is not None else "").ljust(col_width[idx] + padding)
                          for idx, col in enumerate(row))]) for row in table])
