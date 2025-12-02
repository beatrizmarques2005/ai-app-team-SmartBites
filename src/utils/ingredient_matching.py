"""Ingredient matching utilities: fuzzy matching and synonym support."""
from difflib import get_close_matches
from typing import List, Optional
from .text_normalization import normalize_text

def expand_synonyms(name: str) -> List[str]:
    """Return possible synonyms for a name (including itself)."""
    name = normalize_text(name)
    synonyms = [name]
    for k, vals in _SYNONYMS.items():
        nk = normalize_text(k)
        # Match when the normalized key or any of its values correspond to the name
        val_norms = [normalize_text(v) for v in vals]
        if nk == name or nk in name or name in nk or name in val_norms or any(vn in name or name in vn for vn in val_norms):
            synonyms.append(nk)
            for v in vals:
                synonyms.append(normalize_text(v))
        # Also if the name matches a synonym value, include the key
        if normalize_text(name) in val_norms:
            synonyms.append(nk)
    return list(dict.fromkeys(synonyms))


def fuzzy_match(name: str, candidates: List[str], n: int = 3, cutoff: float = 0.6) -> List[str]:
    """Return a list of candidate matches for `name` using difflib."""
    if not name:
        return []
    norm = normalize_text(name)
    cand_norm = [normalize_text(c) for c in candidates]
    matches = get_close_matches(norm, cand_norm, n=n, cutoff=cutoff)
    # Map back to original candidates preserving order
    result = []
    for m in matches:
        for orig, cn in zip(candidates, cand_norm):
            if cn == m and orig not in result:
                result.append(orig)
                break
    return result


def best_match(name: str, candidates: List[str]) -> Optional[str]:
    matches = fuzzy_match(name, candidates, n=1, cutoff=0.5)
    return matches[0] if matches else None

