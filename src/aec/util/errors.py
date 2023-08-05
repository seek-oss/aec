from __future__ import annotations

# HandledErrors are caught and their message printed without a stack trace


class HandledError(Exception):
    pass


class NoInstancesError(HandledError):
    def __init__(self, name: str | None = None, name_match: str | None = None):
        if name:
            pretty_name = "instance id {name}" if name.startswith("i-") else f"name {name}"
            msg = f"No instances with {pretty_name}"
        elif name_match:
            msg = f"No instances with name matching {name_match}"
        else:
            raise ValueError("Missing name or name_match")

        super().__init__(msg)
