#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Optional

from engine.types import CodeRegistry

_THRESHOLD = 0.70


@dataclass
class MatchResult:
    boq_item: str
    code_id: Optional[str]
    score: float
    is_new: bool = False


def _normalize(text: str) -> str:
    text = re.sub(r"[ً-ٟ]", "", text)  # remove tashkeel
    return " ".join(text.lower().split())


def _token_overlap_score(query_tokens: list[str], candidate_tokens: list[str]) -> float:
    """Score based on word-level overlap.

    Requires minimum token length of 3 chars to avoid inflated scores from
    Arabic particles (و، ا، في) or English stopwords (a, an, of).
    """
    if not candidate_tokens or not query_tokens:
        return 0.0
    matches = sum(
        1 for q in query_tokens
        if len(q) >= 3 and any(q == c or (len(q) >= 4 and q in c) for c in candidate_tokens)
    )
    return min(matches / len(candidate_tokens), 1.0)


class BOQMatcher:
    """
    يطابق بنود جدول الكميات مع أكواد النظام باستخدام fuzzy matching.

    Usage:
        matcher = BOQMatcher(codes)
        results = matcher.match(["حفر بالميكنة", "خرسانة عادية"])
        # results: list[MatchResult]
    """

    def __init__(self, codes: CodeRegistry) -> None:
        self._codes = codes
        self._index = self._build_index()

    def _build_index(self) -> list[tuple[str, str, str, list[str], list[str]]]:
        index = []
        for code_id, data in self._codes.items():
            name_ar = _normalize(data.get("activity_name_ar", ""))
            name_en = _normalize(data.get("activity_name_en", ""))
            tokens_ar = name_ar.split()
            tokens_en = name_en.split()
            index.append((code_id, name_ar, name_en, tokens_ar, tokens_en))
        return index

    def _score(self, query: str, candidate: str) -> float:
        if not candidate:
            return 0.0

        # Bonus for substring match or token prefix match
        if query in candidate:
            return 1.0

        # Check if query words form a prefix of candidate
        query_tokens = query.split()
        candidate_tokens = candidate.split()
        if len(query_tokens) <= len(candidate_tokens):
            if all(candidate_tokens[i].startswith(q)
                   for i, q in enumerate(query_tokens)):
                # All query tokens match start of corresponding candidate tokens
                return 0.95

        return SequenceMatcher(None, query, candidate).ratio()

    def _best_match(self, item: str) -> tuple[Optional[str], float]:
        query = _normalize(item)
        if not query:
            return None, 0.0

        query_tokens = query.split()
        best_id: Optional[str] = None
        best_score = 0.0

        for code_id, name_ar, name_en, tokens_ar, tokens_en in self._index:
            # Try character-level matching first
            char_score = max(self._score(query, name_ar), self._score(query, name_en))

            # Try token-level matching as fallback
            token_score_ar = _token_overlap_score(query_tokens, tokens_ar)
            token_score_en = _token_overlap_score(query_tokens, tokens_en)

            # Use the best of all three
            score = max(char_score, token_score_ar, token_score_en)

            if score > best_score:
                best_score = score
                best_id = code_id

        if best_score < _THRESHOLD:
            return None, best_score
        return best_id, best_score

    def match(self, items: list[str]) -> list[MatchResult]:
        """
        يُرجع قائمة MatchResult لكل بند.
        code_id=None يعني البند مجهول (نسبة مطابقة < 70%).
        """
        results = []
        for item in items:
            code_id, score = self._best_match(item)
            results.append(MatchResult(boq_item=item, code_id=code_id, score=score))
        return results
