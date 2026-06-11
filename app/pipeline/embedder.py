import math
import re
from collections import Counter


KeywordVector = dict[str, float]

_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]+|[\u4e00-\u9fff]+")


class KeywordEmbedder:
    """Deterministic keyword fallback, not a semantic embedding model."""

    def embed(self, text: str) -> KeywordVector:
        tokens = tokenize_text(text)
        if not tokens:
            return {}

        counts = Counter(tokens)
        norm = math.sqrt(sum(count * count for count in counts.values()))
        return {token: count / norm for token, count in counts.items()}


def tokenize_text(text: str) -> list[str]:
    tokens: list[str] = []

    for match in _TOKEN_PATTERN.finditer(text.lower()):
        value = match.group(0)
        if _is_cjk_sequence(value):
            tokens.extend(_cjk_tokens(value))
        else:
            tokens.append(value)

    return tokens

# 计算两个关键词向量之间的余弦相似度，值越接近1表示越相似，越接近0表示越不相似
def cosine_similarity(left: KeywordVector, right: KeywordVector) -> float:
    if not left or not right:
        return 0.0

    common_tokens = set(left).intersection(right)
    return sum(left[token] * right[token] for token in common_tokens)


def _is_cjk_sequence(value: str) -> bool:
    return all("\u4e00" <= char <= "\u9fff" for char in value)


def _cjk_tokens(value: str) -> list[str]:
    tokens = list(value)
    tokens.extend(value[index : index + 2] for index in range(len(value) - 1))
    return tokens
