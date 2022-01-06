# HandledErrors are caught and their message printed without a stack trace
from typing import Optional


class HandledError(Exception):
    pass


class NoInstancesError(HandledError):
    def __init__(self, name: Optional[str] = None, name_match: Optional[str] = None):
        if name:
            pretty_name = "instance id {name}" if name.startswith("i-") else f"name {name}"
            msg = f"No instances with {pretty_name}"
        elif name_match:
            msg = f"No instances with name matching {name_match}"
        else:
            raise ValueError("Missing name or name_match")

        super(NoInstancesError, self).__init__(msg)
