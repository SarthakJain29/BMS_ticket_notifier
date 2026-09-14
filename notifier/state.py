"""Remembers shows already seen and ongoing failures between runs."""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class State:
    seen: dict[str, str] = field(default_factory=dict)  # show key -> first seen time
    failing_since: str | None = None
    failure_alerted: bool = False


def load(path: str) -> State | None:
    """Returns None on the first run, when no state file exists yet."""
    file = Path(path)
    if not file.exists():
        return None
    return State(**json.loads(file.read_text()))


def save(state: State, path: str) -> None:
    # Stable output, so the file only changes (and gets committed) when state really changes
    Path(path).write_text(json.dumps(asdict(state), indent=2, sort_keys=True) + "\n")
