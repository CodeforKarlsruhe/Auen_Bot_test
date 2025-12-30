import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from rapidfuzz import fuzz, process

from .config import ANIMALS_PLANTS_PATH, ANIMAL_KEYS_PATH, PLANT_KEYS_PATH
from .utils import normalize_text

@dataclass
class Entry:
    name: str
    typ: str  # "Tier" oder "Pflanze"
    data: Dict[str, Any]

class KnowledgeBase:
    def __init__(self, entries: List[Entry], animal_keys: List[str], plant_keys: List[str]):
        self.entries = entries
        self.animal_keys = animal_keys
        self.plant_keys = plant_keys

        # Lookup-Index: Name -> Entry (normalisiert)
        self._name_index = {normalize_text(e.name): e for e in entries}
        self._names = [e.name for e in entries]

    @staticmethod
    def load_json(path) -> Any:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def load(cls) -> "KnowledgeBase":
        raw_entries = cls.load_json(ANIMALS_PLANTS_PATH)
        animal_keys = cls.load_json(ANIMAL_KEYS_PATH)
        plant_keys = cls.load_json(PLANT_KEYS_PATH)

        entries: List[Entry] = []
        for obj in raw_entries:
            name = obj.get("Name") or obj.get("name") or ""
            typ = obj.get("Typ") or obj.get("typ") or ""
            if not name or not typ:
                # Skip unvollständige Datensätze
                continue
            entries.append(Entry(name=name, typ=typ, data=obj))

        return cls(entries=entries, animal_keys=animal_keys, plant_keys=plant_keys)

    def keys_for_type(self, typ: str) -> List[str]:
        t = normalize_text(typ)
        if "tier" in t:
            return self.animal_keys
        if "pflanze" in t:
            return self.plant_keys
        # fallback: union
        return sorted(set(self.animal_keys) | set(self.plant_keys))

    def find_by_name(self, name_query: str, score_cutoff: int = 75) -> Optional[Entry]:
        # Exakt
        nq = normalize_text(name_query)
        if nq in self._name_index:
            return self._name_index[nq]

        # Fuzzy
        match = process.extractOne(
            name_query, self._names, scorer=fuzz.WRatio, score_cutoff=score_cutoff
        )
        if not match:
            return None
        best_name, score, _ = match
        return self._name_index[normalize_text(best_name)]

    def guess_key(self, entry: Entry, key_query: str, score_cutoff: int = 70) -> Optional[str]:
        available_keys = [k for k in entry.data.keys() if k not in ("Name", "Typ")]
        
        allowed = [k for k in self.keys_for_type(entry.typ) if k in entry.data] or available_keys

        match = process.extractOne(
            key_query, allowed, scorer=fuzz.WRatio, score_cutoff=score_cutoff
        )
        if not match:
            return None
        return match[0]
