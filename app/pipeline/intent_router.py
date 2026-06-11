from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from re import Pattern
from typing import Literal

from pydantic import BaseModel, Field


RouteName = Literal["structured_only", "document_only", "hybrid", "fallback"]


class RouteDecision(BaseModel):
    intent: str
    route: RouteName
    required_slots: list[str] = Field(default_factory=list)
    slots: dict[str, str] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: str | None = None


@dataclass(frozen=True)
class IntentRule:
    intent: str
    route: RouteName
    keywords: tuple[str, ...]
    required_slots: tuple[str, ...] = ()
    any_slot: tuple[str, ...] = ()
    confidence: float = 0.8
    reason: str | None = None

    def matches(self, query: str, slots: Mapping[str, str]) -> bool:
        normalized_query = normalize_query(query)
        keyword_matched = any(keyword.lower() in normalized_query for keyword in self.keywords)
        slot_matched = not self.any_slot or any(slots.get(slot_name) for slot_name in self.any_slot)
        return keyword_matched and slot_matched


class RuleBasedIntentRouter:
    def __init__(
        self,
        rules: Iterable[IntentRule],
        slot_patterns: Mapping[str, Iterable[Pattern[str]]] | None = None,
        slot_normalizers: Mapping[str, Callable[[str], str]] | None = None,
    ) -> None:
        self.rules = list(rules)
        self.slot_patterns = {
            slot_name: tuple(patterns)
            for slot_name, patterns in (slot_patterns or {}).items()
        }
        self.slot_normalizers = dict(slot_normalizers or {})

    def route(self, query: str) -> RouteDecision:
        slots = self.extract_slots(query)
        for rule in self.rules:
            if rule.matches(query=query, slots=slots):
                return RouteDecision(
                    intent=rule.intent,
                    route=rule.route,
                    required_slots=list(rule.required_slots),
                    slots=slots,
                    confidence=rule.confidence,
                    reason=rule.reason,
                )

        return RouteDecision(
            intent="unknown",
            route="fallback",
            required_slots=[],
            slots=slots,
            confidence=0.0,
            reason="no_intent_matched",
        )

    def extract_slots(self, query: str) -> dict[str, str]:
        slots: dict[str, str] = {}
        for slot_name, patterns in self.slot_patterns.items():
            for pattern in patterns:
                match = pattern.search(query)
                if match:
                    raw_value = match.group("value") if "value" in match.groupdict() else match.group(0)
                    normalizer = self.slot_normalizers.get(slot_name)
                    slots[slot_name] = normalizer(raw_value) if normalizer else raw_value
                    break
        return slots


def normalize_query(query: str) -> str:
    return " ".join(query.strip().lower().split())
