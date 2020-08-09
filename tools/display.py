import json
from typing import Any, Dict, List, Optional, Sequence


def as_table(dicts: Optional[Sequence[Dict[str, Any]]], keys: Optional[List[str]] = None) -> List[List[Optional[str]]]:
    """
    Converts a list of dictionaries to a nested list, ordered by specified keys.

    :param dicts: list of dictionaries
    :param keys: ordered list of keys to include in each row, or None to use the keys from the first dict
    :return:
    """
    if not dicts:
        return []

    if keys is None:
        keys = list(dicts[0].keys())
    return [keys] + [[str(d.get(f, "")) if d.get(f, "") else None for f in keys] for d in dicts]


def pretty_table(table: Optional[Sequence[Sequence[Optional[str]]]]) -> str:
    """
    Formats a table as a pretty string for printing.

    :param table:
    :return:
    """
    if not table:
        return ""

    padding = 2
    col_width = [0] * len(table[0])
    for row in table:
        for idx, col in enumerate(row):
            if col is not None and len(col) > col_width[idx]:
                col_width[idx] = len(col)

    return "\n".join(
        [
            "".join(
                [
                    "".join(
                        (col if col is not None else "").ljust(col_width[idx] + padding) for idx, col in enumerate(row)
                    )
                ]
            )
            for row in table
        ]
    )


def prettify(result):
    """prettify, instead of showing a dict, or list of dicts."""
    if isinstance(result, list):
        prettified = pretty_table(as_table(result))
        return prettified if prettified else "No results"
    elif isinstance(result, dict):
        return json.dumps(result, default=str)
    else:
        return result
