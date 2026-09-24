"""
Vocabulary provider loading botanicals, base oils, therapeutic tags, actions,
and Polish demographic data.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import yaml


@dataclass
class Vocabulary:
    bases: list[dict[str, Any]]
    ingredients: list[dict[str, Any]]
    tags: list[dict[str, Any]]
    actions: list[dict[str, Any]]
    cities: list[dict[str, Any]]
    first_names_female: list[str]
    first_names_male: list[str]
    last_names: list[str]


def load_vocabulary(path: Path | str = "seeds/base_data.yaml") -> Vocabulary:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Vocabulary seed file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return Vocabulary(
        bases=data.get("bases", []),
        ingredients=data.get("ingredients", []),
        tags=data.get("tags", []),
        actions=data.get("actions", []),
        cities=data.get("cities", []),
        first_names_female=data.get("names", {}).get("first_names_female", []),
        first_names_male=data.get("names", {}).get("first_names_male", []),
        last_names=data.get("names", {}).get("last_names", []),
    )
