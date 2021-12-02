from __future__ import annotations

import csv
import enum
import json
import sys
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, cast

from rich import box
from rich.console import Console
from rich.live import Live
from rich.table import Table


class OutputFormat(enum.Enum):
    table = "table"
    csv = "csv"


def as_table(dicts: Sequence[Dict[str, Any]], keys: Optional[List[str]] = None) -> List[List[Optional[str]]]:
    """
    Converts a list of dictionaries to a list of lists (table), ordered by specified keys.

    :param dicts: list of dictionaries
    :param keys: ordered list of keys to include in each row, or None to use the keys from the first dict
    :return: list of lists, with None values if there's no value for a key
    """
    if not dicts:
        return []

    if keys is None:
        keys = list(dicts[0].keys())
    return [keys] + [[str(d.get(f, "")) if d.get(f, "") else None for f in keys] for d in dicts]  # type: ignore


def as_strings(values: Iterable[Any]) -> List[str]:
    return [str(v) if v else "" for v in values]


def pretty_print(
    result: List[Dict[str, Any]] | Iterator[Dict[str, Any]] | Dict | str | None,
    output_format: OutputFormat,
) -> None:
    """print results as table/csv/json."""

    console = Console()

    if isinstance(result, list) and not result:
        console.print("No results")
        return

    elif isinstance(result, list) and output_format == OutputFormat.table:
        rows = as_table(result)
        column_names = cast(List[str], rows[0])
        table = Table(box=box.SIMPLE)
        for c in column_names:
            if c in ["CommandId"]:
                table.add_column(c, no_wrap=True)
            else:
                table.add_column(c)

        for r in rows[1:]:
            table.add_row(*r)

        console.print(table)

    elif isinstance(result, list) and output_format == OutputFormat.csv:
        writer = csv.DictWriter(sys.stdout, fieldnames=list(result[0].keys()))

        writer.writeheader()
        for r in result:
            writer.writerow(r)

    elif isinstance(result, Iterator) and output_format == OutputFormat.table:
        first = next(result)
        table = Table(box=box.SIMPLE)
        for c in first.keys():
            table.add_column(c)

        table.add_row(*as_strings(first.values()))

        with Live(table, refresh_per_second=1):
            for row in result:
                table.add_row(*as_strings(row.values()))

    elif isinstance(result, Iterator) and output_format == OutputFormat.csv:
        writer = csv.writer(sys.stdout)
        first = next(result)
        writer.writerow(first.keys())
        writer.writerow(first.values())
        for row in result:
            writer.writerow(row.values())

    elif isinstance(result, dict):
        print(json.dumps(result, default=str))

    elif not result:
        print("Done ✨")

    else:
        print(result)
