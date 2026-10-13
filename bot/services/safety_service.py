from dataclasses import dataclass


DANGER_KEYWORDS = (
    "убью",
    "убить",
    "угрожает",
    "угроза",
    "насилие",
    "избил",
    "ударил",
    "самоповреждение",
    "суицид",
    "покончить",
    "преследует",
    "сталкинг",
    "заставляет",
    "принуждает",
    "шантаж",
)

MANIPULATION_KEYWORDS = (
    "заставить",
    "манипулировать",
    "отомстить",
    "проучить",
    "контролировать",
    "проверить телефон",
    "вызвать ревность",
    "давить",
    "унизить",
    "шантажировать",
)


@dataclass(frozen=True)
class SafetyCheck:
    level: str | None
    message: str | None


def check_relationship_safety(text: str) -> SafetyCheck:
    normalized = text.lower()

    if any(keyword in normalized for keyword in DANGER_KEYWORDS):
        return SafetyCheck(
            level="danger",
            message=(
                "Мне важно, чтобы ты был(а) в безопасности. Если есть угроза жизни, насилие, "
                "преследование или принуждение, лучше не оставаться с этим одному: обратись "
                "в экстренные службы своей страны, к близким людям или в кризисную службу. "
                "Сейчас главное — безопасность, дистанция от опасного человека и поддержка."
            ),
        )

    if any(keyword in normalized for keyword in MANIPULATION_KEYWORDS):
        return SafetyCheck(
            level="manipulation",
            message=(
                "Я не помогу с давлением, местью, контролем или унижением партнера. "
                "Но могу помочь сформулировать спокойный честный разговор, просьбу или границу, "
                "чтобы отношения не стали токсичными."
            ),
        )

    return SafetyCheck(level=None, message=None)

