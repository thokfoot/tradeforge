from __future__ import annotations

from modules.education.lessons import LANGUAGES, LESSONS
from modules.education.store import EducationStore

VALID_LANGS = set(LANGUAGES)


class EducationService:
    def __init__(self, store: EducationStore):
        self._store = store

    def languages(self) -> list[str]:
        return list(LANGUAGES)

    def list_lessons(self, lang: str = "hinglish") -> list[dict]:
        lang = self._lang(lang)
        return [
            {
                "id": lesson["id"],
                "level": lesson["level"],
                "minutes": lesson["minutes"],
                "tags": lesson["tags"],
                "title": lesson["title"].get(lang, lesson["title"]["en"]),
            }
            for lesson in LESSONS
        ]

    def lesson(self, lesson_id: str, lang: str = "hinglish") -> dict | None:
        lang = self._lang(lang)
        for lesson in LESSONS:
            if lesson["id"] == lesson_id:
                return {
                    "id": lesson["id"],
                    "level": lesson["level"],
                    "minutes": lesson["minutes"],
                    "title": lesson["title"].get(lang, lesson["title"]["en"]),
                    "sections": [
                        {
                            "title": section["title"].get(lang, section["title"]["en"]),
                            "body": section["body"].get(lang, section["body"]["en"]),
                        }
                        for section in lesson["sections"]
                    ],
                }
        return None

    def mark_completed(self, user_id: str, lesson_id: str) -> list[str]:
        return self._store.mark(user_id, lesson_id)

    def completed(self, user_id: str) -> list[str]:
        return self._store.completed(user_id)

    @staticmethod
    def _lang(lang: str) -> str:
        return lang if lang in VALID_LANGS else "hinglish"
