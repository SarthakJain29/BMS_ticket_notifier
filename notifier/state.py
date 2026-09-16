"""Remembers shows already seen and venues already baselined between runs."""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class State:
    seen: dict[str, str] = field(default_factory=dict)  # show key -> first seen time
    venues: list[str] = field(default_factory=list)  # venue codes whose existing shows are recorded


def load(path: str) -> State:
    file = Path(path)
    if not file.exists():
        return State()
    data = json.loads(file.read_text())
    return State(seen=data.get("seen", {}), venues=data.get("venues", []))


def save(state: State, path: str) -> None:
    # Stable output, so the file only changes (and gets committed) when state really changes
    Path(path).write_text(json.dumps(asdict(state), indent=2, sort_keys=True) + "\n")
