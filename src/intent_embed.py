import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from .config import TASK_LIST_PATH, PROJECT_ROOT
from .utils import normalize_text, strip_html


INDEX_PATH = PROJECT_ROOT / "intent_index.pkl"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def _parse_task_list(raw: Any) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    # raw ist bei dir eine Liste aus dicts: [{ "id": {...}}, {...}]
    for item in raw:
        if not isinstance(item, dict):
            continue
        for _id, payload in item.items():
            intent = payload.get("intent", "")
            utter = payload.get("utter", "")
            examples = payload.get("text", []) or []
            if not intent or not utter:
                continue
            for ex in examples:
                rows.append(
                    {
                        "intent": intent,
                        "utter": utter,
                        "example": ex,
                        "example_norm": normalize_text(ex),
                    }
                )
    return rows


def build_intent_index(force_rebuild: bool = False) -> None:
    """
    Baut einen lokalen Embedding-Index aus task_list.json.
    Wird automatisch neu gebaut, wenn die Datei noch nicht existiert.
    """
    if INDEX_PATH.exists() and not force_rebuild:
        return

    with open(TASK_LIST_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    rows = _parse_task_list(raw)
    texts = [r["example"] for r in rows]

    model = SentenceTransformer(MODEL_NAME)
    emb = model.encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=True)
    emb = np.asarray(emb, dtype=np.float32)

    payload = {"rows": rows, "embeddings": emb, "model": MODEL_NAME}
    with open(INDEX_PATH, "wb") as f:
        pickle.dump(payload, f)


class IntentEmbeddingMatcher:
    def __init__(self):
        build_intent_index()

        with open(INDEX_PATH, "rb") as f:
            payload = pickle.load(f)

        self.rows = payload["rows"]
        self.emb = payload["embeddings"]  # (N, D), normalized
        self.model_name = payload.get("model", MODEL_NAME)
        self.model = SentenceTransformer(self.model_name)

    def match(self, user_text: str, min_score: float = 0.60) -> Optional[Dict[str, Any]]:
        q = self.model.encode([user_text], normalize_embeddings=True)
        q = np.asarray(q, dtype=np.float32)[0]  # (D,)

        sims = self.emb @ q  # cosine similarity (weil normalisiert)
        best_i = int(np.argmax(sims))
        best_score = float(sims[best_i])

        if best_score < min_score:
            return None

        best = self.rows[best_i]
        return {
            "intent": best["intent"],
            "utter": strip_html(best["utter"]),
            "score": best_score,
            "matched_example": best["example"],
        }
