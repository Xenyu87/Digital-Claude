#!/usr/bin/env python3
"""
In-flight scope drift detector.
Calculates deviation between original brief and work-in-progress.
"""

import re
from typing import Tuple, Dict, Any, List

def estimate_files_from_brief(brief: str) -> int:
    """Euristica: estrae numero di file attesi dal brief."""
    pattern = r'\b(modifica|cambia|aggiungi|togli|aggiorna|refactor|crea|scrivi|implementa|fix|correggi)\s+([a-zàèéìòù\w\s]+?)(?:\s+e\s+|\s*,|\s+o\s+|$)'
    matches = re.findall(pattern, brief, re.IGNORECASE)
    count = len(matches)
    # Margine di sicurezza: +1 file
    return max(count + 1, 1)

def detect_category_shift(original: str, detected: str) -> float:
    """Ritorna 1.0 se categoria è cambiata, 0.0 altrimenti."""
    return 0.0 if original == detected else 1.0

def calculate_token_burn_ratio(tokens_spent: int, tokens_budget: int, progress: float = 0.5) -> float:
    """
    Calcola se il burning rate è normale.
    progress: frazione di task completato (0-1), default 0.5 = metà strada

    Rapporto atteso: tokens_spent / (tokens_budget * progress)
    Se > 1.5, il token burn è accelerato (anomalia).
    """
    if tokens_budget == 0:
        return 0.0
    expected_spend = tokens_budget * progress
    if expected_spend == 0:
        return 0.0
    ratio = tokens_spent / expected_spend
    # Normalizza a 0-1: ratio 0.5 → 0, ratio 1.5 → 1.0, ratio 3.0 → 1.0 (capping)
    return min(max(ratio - 0.5, 0) / 1.0, 1.0)

def predict_scope_creep(files_expected: int, files_actual: int, progress: float) -> float:
    """
    Predictive: estrapola il trend file toccati al completamento.
    Se a progress X% hai già Y% dei file, calcola probabilità di scope creep.

    Esempio: a 40% del task hai già 70% dei file toccati → trend di divergenza.

    Returns: 0.0 (ok) a 1.0 (molto probabile scope creep)
    """
    if progress <= 0 or files_expected == 0:
        return 0.0

    # Files che ti aspetti a questo progress
    expected_files_at_progress = max(1, int(files_expected * progress))

    # Quanto sei avanti
    overburn = max(0, files_actual - expected_files_at_progress)

    # Estrapola: se continui con questo ritmo, quanti file alla fine?
    if progress > 0:
        files_projected = files_actual / progress
    else:
        files_projected = files_expected

    # Divergenza fra proiezione e atteso
    divergence = (files_projected - files_expected) / max(files_expected, 1)

    # Normalizza a 0-1
    creep_probability = min(max(divergence * 0.5, 0), 1.0)  # 0.5 = damping

    return creep_probability

def detect_opportunistic_refactor(brief: str, recent_work: str) -> Tuple[bool, str]:
    """
    Riconosce se il lavoro contiene refactor/cleanup non richiesto dal brief.

    Patterns rilevati:
    - "refactor", "cleanup", "reorganize", "improve", "beautify"
    - "removed dead code", "simplified", "optimized"
    - File con estensioni CSS/color/theme rinominate
    - Commenti di "while we're at it" o "might as well"

    Returns: (is_refactor: bool, pattern_detected: str)
    """
    refactor_keywords = [
        r'\brefactor\b', r'\bcleanup\b', r'\breorganiz\w*\b',
        r'\bimprov\w+ (code|style|structure)\b',
        r'\bremov\w+ dead code\b', r'\bsimplifi\w*\b',
        r'\boptimiz\w*\b', r'\brewr\w*\b',
        r'\bbeautif\w*\b', r'\bpolish\b',
        r"while we.?re at it", r'might as well',
        r'\bDRY\b', r"don.?t repeat yourself"
    ]

    combined_text = f"{brief} {recent_work}".lower()
    for pattern in refactor_keywords:
        if re.search(pattern, combined_text, re.IGNORECASE):
            return True, pattern

    return False, ""

def phrase_semantic_divergence(brief: str, recent_work: str) -> float:
    """
    Simplice TF-IDF: quanto le parole chiave del brief mancano nel recente lavoro?
    Ritorna 0.0 (allineato) a 1.0 (divergente).
    """
    if not brief or not recent_work:
        return 0.0

    # Estrai parole chiave (lunghezza > 3, no stop words)
    stop_words = {'che', 'del', 'per', 'con', 'una', 'uno', 'sul', 'alla', 'sono', 'fare', 'fatto'}
    brief_words = set(w.lower() for w in re.findall(r'\b\w+\b', brief) if len(w) > 3 and w.lower() not in stop_words)
    work_words = set(w.lower() for w in re.findall(r'\b\w+\b', recent_work) if len(w) > 3 and w.lower() not in stop_words)

    if not brief_words:
        return 0.0

    overlap = len(brief_words & work_words)
    coverage = overlap / len(brief_words)

    # Se copertura <50%, significa divergenza
    divergence = max(0.5 - coverage, 0) / 0.5
    return min(divergence, 1.0)

def calculate_drift_score(
    brief_original: str,
    files_expected: int = None,
    files_actual: int = 0,
    category_original: str = "modifica",
    category_detected: str = "modifica",
    tokens_spent: int = 0,
    tokens_budget: int = 200000,
    recent_work_summary: str = "",
    progress: float = 0.5
) -> Tuple[float, Dict[str, Any]]:
    """
    Calcola drift score (0.0-1.0) fra brief e work-in-progress.

    Args:
        brief_original: primo prompt utente
        files_expected: numero file attesi (se None, stima da brief)
        files_actual: numero file toccati finora
        category_original: categoria iniziale (ops, modifica, audit, ecc.)
        category_detected: categoria rilevata nel lavoro corrente
        tokens_spent: token spesi finora
        tokens_budget: token budget per la categoria
        recent_work_summary: riassunto ultimi turni
        progress: frazione di task completato (0-1)

    Returns:
        (score: float, details: dict)
    """

    if files_expected is None:
        files_expected = estimate_files_from_brief(brief_original)

    # Componenti
    files_divergence = abs(files_actual - files_expected) / max(files_expected, 1)
    category_shift = detect_category_shift(category_original, category_detected)
    token_burn = calculate_token_burn_ratio(tokens_spent, tokens_budget, progress)
    semantic = phrase_semantic_divergence(brief_original, recent_work_summary)
    creep_probability = predict_scope_creep(files_expected, files_actual, progress)
    is_refactor, refactor_pattern = detect_opportunistic_refactor(brief_original, recent_work_summary)

    # Drift score finale (weighted sum)
    # Aggiunge predizione: accelera l'avviso se il trend è brutto
    score = (
        0.35 * min(files_divergence, 1.0) +
        0.25 * category_shift +
        0.15 * token_burn +
        0.1 * semantic +
        0.15 * creep_probability  # ← NUOVO: predictive component
    )

    # Determina severity
    if score >= 0.6:
        severity = "hard_divergence"
    elif score >= 0.3:
        severity = "warning"
    else:
        severity = "on_track"

    # Primary reason
    reasons = []
    if files_divergence > 0.3:
        reasons.append(f"files_divergence ({files_actual} vs {files_expected})")
    if category_shift > 0.5:
        reasons.append(f"category_shift ({category_original} → {category_detected})")
    if token_burn > 0.3:
        reasons.append(f"token_burn_accelerated ({token_burn:.1%})")
    if semantic > 0.3:
        reasons.append("semantic_divergence")
    if is_refactor:
        reasons.append(f"opportunistic_refactor ({refactor_pattern})")

    reason = " + ".join(reasons) if reasons else "on_scope"

    details = {
        "score": round(score, 2),
        "severity": severity,
        "reason": reason,
        "files_expected": files_expected,
        "files_actual": files_actual,
        "files_divergence": round(files_divergence, 2),
        "category_shift": bool(category_shift),
        "token_burn_ratio": round(token_burn, 2),
        "semantic_divergence": round(semantic, 2),
        "scope_creep_probability": round(creep_probability, 2),
        "opportunistic_refactor": is_refactor,
        "refactor_pattern": refactor_pattern if is_refactor else None,
    }

    return score, details

def format_drift_alert(score: float, details: Dict[str, Any], brief: str) -> str:
    """Formatta messaggio di alert per il coordinatore."""
    severity = details["severity"]

    if severity == "on_track":
        return f"✅ ON_TRACK (score {details['score']:.2f})"

    elif severity == "warning":
        msg = f"""⚠️ SCOPE DRIFT RILEVATO (score {details['score']:.2f})

Il brief era: "{brief[:80]}..."
Lavoro compiuto: {details['files_actual']} file (attesi {details['files_expected']})
Motivo principale: {details['reason']}

Continuo lo stesso compito? [y/n]"""
        return msg

    else:  # hard_divergence
        msg = f"""🛑 DIVERGENZA SERIA DAL BRIEF (score {details['score']:.2f})

Il brief originale era: "{brief[:80]}..."
Quello che sto facendo non corrisponde più.

Opzioni:
  1. Continua comunque (accetti token bruciati off-scope)
  2. Ferma questo task e apri uno nuovo per il resto

Cosa scelgo? [1/2]"""
        return msg

if __name__ == "__main__":
    # Test
    brief = "Aggiungi pulsante logout e refresh layout"
    score, details = calculate_drift_score(
        brief_original=brief,
        files_actual=5,
        tokens_spent=120000,
        tokens_budget=200000,
        recent_work_summary="Refactor header, add logout button, change sidebar color, new CSS file",
        progress=0.6
    )
    print(f"Score: {score:.2f}")
    print(f"Details: {details}")
    print(f"\nAlert:\n{format_drift_alert(score, details, brief)}")
