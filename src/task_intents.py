import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from rapidfuzz import fuzz, process

from .config import TASK_LIST_PATH
from .utils import normalize_text, strip_html

@dataclass
class TaskIntent:
    intent: str
    utter: str
    examples: List[str]

class TaskIntentMatcher:
    def __init__(self, intents: List[TaskIntent]):
        self.intents = intents
        self._example_to_intent: Dict[str, TaskIntent] = {}
        examples_flat: List[str] = []
        for it in intents:
            for ex in it.examples:
                nx = normalize_text(ex)
                self._example_to_intent[nx] = it
                examples_flat.append(ex)
        self._examples_flat = examples_flat

    @staticmethod
    def _parse_task_list(raw) -> List[TaskIntent]:
        
        intents: List[TaskIntent] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            
            for _id, payload in item.items():
                intent = payload.get("intent", "")
                utter = payload.get("utter", "")
                examples = payload.get("text", []) or []
                if intent and utter and examples:
                    intents.append(TaskIntent(intent=intent, utter=utter, examples=examples))
        return intents

    @classmethod
    def load(cls) -> "TaskIntentMatcher":
        with open(TASK_LIST_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        intents = cls._parse_task_list(raw)
        return cls(intents)

    def match(self, user_text: str, score_cutoff: int = 92) -> Optional[Tuple[str, str]]:
        
        match = process.extractOne(
            user_text, self._examples_flat, scorer=fuzz.WRatio, score_cutoff=score_cutoff
        )
        if not match:
            return None
        example, score, _ = match
        it = self._example_to_intent[normalize_text(example)]
        return it.intent, strip_html(it.utter)
