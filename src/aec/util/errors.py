from __future__ import annotations

# HandledErrors are caught and their message printed without a stack trace


class HandledError(Exception):
    pass


class NoInstancesError(HandledError):
    def __init__(self, name: str | list[str] | None = None, name_match: str | None = None):
        if isinstance(name, str):
            name = [name]
        if name:
            pretty_names = [f"instance id {n}" if n.startswith("i-") else f"name {n}" for n in name]
            msg = f"No instances with {', '.join(pretty_names)}"
        elif name_match:
            msg = f"No instances with name matching {name_match}"
        else:
            raise ValueError("Missing name or name_match")

        super().__init__(msg)
