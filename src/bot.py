import re
from typing import Optional, Tuple

from .data_loader import KnowledgeBase, Entry
from .intent_embed import IntentEmbeddingMatcher


class AuenBot:
    def __init__(self, kb: KnowledgeBase):
        self.kb = kb
        self.intent_matcher = IntentEmbeddingMatcher()

    def _key_from_question(self, text: str) -> Optional[str]:
        t = text.lower()

        patterns = [
            (r"\bwie groß\b|\bwelche größe\b|\bgröße hat\b", "Größe"),
            (r"\bwie schwer\b|\bwelches gewicht\b|\bgewicht hat\b", "Gewicht"),
            (r"\bwo lebt\b|\bwo kommt\b|\blebensraum\b|\bhabitat\b", "Habitat"),
            (r"\bwas frisst\b|\bnahrung\b|\bwovon ernährt\b", "Nahrung"),
            (r"\bfortpflanzung\b|\bwie pflanzt\b|\bvermehr", "Fortpflanzung"),
            (r"\berkennungsmerkmale\b|\bworan erkenn", "Erkennungsmerkmale"),
            (r"\bverhalten\b|\bwie verhält\b", "Verhalten"),
            (r"\büberwinter", "Überwinterung"),
            (r"\bfeinde\b", "Feinde"),
        ]

        import re
        for pat, key in patterns:
            if re.search(pat, t):
                return key
        return None

    
    
    def _extract_name_and_key(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        import re

        # 1) Key aus typischen Fragen ableiten (wie groß/wo lebt/was frisst/...)
        key = self._key_from_question(text)

        # 2) Namen rausziehen: häufig steht der Name am Ende
        #    Entferne Fragefloskeln am Anfang, damit Name besser matcht
        cleaned = re.sub(
            r"^(wie|welche|was|wo|woran|wovon|wann)\b.*?\b(ist|hat|sind|lebt|frisst)?\b",
            "",
            text.strip(),
            flags=re.IGNORECASE,
        ).strip(" ?!,:;-")

        # Wenn das zu aggressiv war, fallback: Originaltext ohne Satzzeichen
        if len(cleaned) < 3:
            cleaned = re.sub(r"[?!,:;]+$", "", text).strip()

         # 3) Falls noch ein "der/die/des" drin ist, nimm den rechten Teil als Name
        m = re.search(r"\b(der|die|des)\b\s+(?P<name>.+)$", cleaned, flags=re.IGNORECASE)
        if m:
            name = m.group("name").strip(" ?!,:;-")
            return name, key

        return cleaned, key


    def answer(self, user_text: str) -> str:
        # 1) Task-Intents nur für "kurze" Nachrichten (Hi, Tschüss, Danke...)
        hit = self.intent_matcher.match(user_text, min_score=0.72)  # etwas strenger

        if hit:
            text_lower = user_text.strip().lower()
            is_short = len(text_lower.split()) <= 4
            looks_like_question = "?" in user_text or any(w in text_lower for w in ["wie", "wo", "was", "welche", "woran"])

            # Nur antworten, wenn es nicht nach einer Fachfrage aussieht
            if is_short and not looks_like_question:
                return hit["utter"]


        # 2) Wissensfragen zu Tieren/Pflanzen
        name_guess, key_guess = self._extract_name_and_key(user_text)

        # Wenn wir irgendwo einen Namen rausbekommen: versuchen Entry zu finden
        entry: Optional[Entry] = None
        if name_guess:
            entry = self.kb.find_by_name(name_guess)

        # Fallback: versuche direkt im gesamten Text einen Namen zu matchen
        if entry is None:
            entry = self.kb.find_by_name(user_text, score_cutoff=80)

        if entry is None:
            return (
                "Ich habe dazu noch keinen passenden Eintrag gefunden.\n"
                "Tipp: Frag z.B. „Habitat der Blauschwarzen Holzbiene“ oder „Erkennungsmerkmale Blauschwarze Holzbiene“."
            )

        # 3) Wenn ein Key vermutet wird: gib das Merkmal aus
        if key_guess:
            key = self.kb.guess_key(entry, key_guess)
            if key and key in entry.data and entry.data[key]:
                return f"**{entry.name}** ({entry.typ}) – **{key}**:\n{entry.data[key]}"
            else:
                possible = [k for k in self.kb.keys_for_type(entry.typ) if k in entry.data]
                possible = possible[:10]
                return (
                    f"Ich habe **{entry.name}** gefunden, aber das Merkmal „{key_guess}“ nicht sicher zuordnen können.\n"
                    f"Mögliche Merkmale sind z.B.: {', '.join(possible)}"
                )

        # 4) Sonst: kurze Zusammenfassung (Top-Felder)
        summary_keys = [k for k in ("Erkennungsmerkmale", "Habitat", "Größe", "Nahrung") if k in entry.data]
        lines = [f"**{entry.name}** ({entry.typ})"]
        for k in summary_keys:
            v = entry.data.get(k, "")
            if v:
                # Kurz anreißen
                short = v.strip()
                if len(short) > 220:
                    short = short[:220].rsplit(" ", 1)[0] + "…"
                lines.append(f"- **{k}**: {short}")
        lines.append("\nDu kannst mich auch nach einem konkreten Merkmal fragen, z.B. „Habitat der …“.")
        return "\n".join(lines)
