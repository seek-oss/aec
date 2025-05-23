from __future__ import annotations

import csv
import enum
import json
import sys
from collections.abc import Iterable, Iterator, Sequence
from typing import Any, cast

from rich import box
from rich.console import Console
from rich.live import Live
from rich.table import Table


class OutputFormat(enum.Enum):
    table = "table"
    csv = "csv"


def as_table(dicts: Sequence[dict[str, Any]], keys: list[str] | None = None) -> list[list[str | None]]:
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


def as_strings(values: Iterable[Any]) -> list[str]:
    return [str(v) if v else "" for v in values]


def pretty_print(
    result: list[dict[str, Any]] | Iterator[dict[str, Any]] | dict | str | None,
    output_format: OutputFormat = OutputFormat.table,
) -> None:
    """print results as table/csv/json."""

    console = Console()

    if isinstance(result, list) and not result:
        console.print("No results")
        return

    elif isinstance(result, list) and output_format == OutputFormat.table:
        rows = as_table(result)
        column_names = cast(list[str], rows[0])
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
        try:
            first = next(result)
        except StopIteration:
            console.print("No results")
            return

        table = Table(box=box.SIMPLE)
        for c in first:
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
