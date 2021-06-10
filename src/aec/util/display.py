from __future__ import annotations

import csv
import enum
import json
import sys
from typing import Any, Dict, List, Optional, Sequence, cast

from rich import box
from rich.console import Console
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


def pretty_print(result: List[Dict[str, Any]] | Dict | str | None, output_format: OutputFormat) -> None:
    """print table/json, instead of showing a dict, or list of dicts."""

    console = Console()

    if isinstance(result, list):
        if not result:
            console.print("No results")
            return

        if output_format == OutputFormat.table:
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

        elif output_format == OutputFormat.csv:
            writer = csv.DictWriter(sys.stdout, fieldnames=list(result[0].keys()))

            writer.writeheader()
            for r in result:
                writer.writerow(r)

    elif isinstance(result, dict):
        print(json.dumps(result, default=str))
    elif not result:
        print("Done ✨")
    else:
        print(result)
