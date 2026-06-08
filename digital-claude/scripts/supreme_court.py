#!/usr/bin/env python3
"""
Supreme Court: deliberazione multi-agente per decisioni ambigue o rischiose.

3 sub-agenti con ruoli fissi deliberano in parallelo:
  - Propositore: argomenta a favore dell'azione
  - Critico:     cerca problemi, controindicazioni, alternative
  - Arbitro:     valuta impatto a lungo termine, vota in modo neutro

Voto di maggioranza → verdetto (approve/reject).
Il dissenso viene loggato come precedente in references/precedents.jsonl.

Uso:
  python3 supreme_court.py --question "Promuovo questa lezione in SKILL.md?" \
      --context "Lezione: non usare npm ci in CI senza lock file. Occorrenze: 6." \
      --dry-run

Exit code: 0 = approve, 1 = reject, 2 = errore
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from budget_guard import run_guarded  # type: ignore

SKILL_DIR = Path(__file__).parent.parent
PRECEDENTS_FILE = SKILL_DIR / "references" / "precedents.jsonl"
MODEL = "claude-haiku-4-5-20251001"
TIMEOUT = 45  # secondi per agente
BUDGET_PER_AGENT_CENTS = 5  # ~$0.05 per giudice, cap totale corte ~$0.15

ROLE_PROMPTS = {
    "propositore": (
        "Sei il Propositore nella Corte Suprema della skill. Il tuo ruolo: argomentare "
        "FORTEMENTE A FAVORE dell'azione proposta. Trova tutte le ragioni per cui va approvata. "
        "Sii diretto e conciso (max 5 righe). Concludi con 'VOTO: APPROVE'."
    ),
    "critico": (
        "Sei il Critico nella Corte Suprema della skill. Il tuo ruolo: trovare "
        "TUTTI I PROBLEMI E RISCHI dell'azione proposta. Considera edge case, regressioni, "
        "effetti collaterali. Sii diretto e conciso (max 5 righe). "
        "Se i rischi superano i benefici concludi 'VOTO: REJECT', altrimenti 'VOTO: APPROVE'."
    ),
    "arbitro": (
        "Sei l'Arbitro nella Corte Suprema della skill. Il tuo ruolo: valutare "
        "l'impatto A LUNGO TERMINE in modo neutro. Considera: questa decisione crea precedente? "
        "È reversibile? Migliora il sistema nel tempo? Sii diretto e conciso (max 5 righe). "
        "Concludi con 'VOTO: APPROVE' o 'VOTO: REJECT'."
    ),
}


def call_agent(role: str, question: str, context: str, results: dict, dry_run: bool) -> None:
    """Chiama un agente con il suo ruolo. Scrive in results[role]."""
    if dry_run:
        results[role] = {
            "reasoning": f"[DRY RUN] {role}: argomentazione simulata",
            "vote": "approve" if role != "critico" else "reject",
            "cost_usd": 0.0,
        }
        return

    prompt = (
        f"{ROLE_PROMPTS[role]}\n\n"
        f"DOMANDA: {question}\n\n"
        f"CONTESTO: {context}"
    )

    outcome = run_guarded(
        prompt,
        model=MODEL,
        budget_cents=BUDGET_PER_AGENT_CENTS,
        max_turns=3,
        timeout=TIMEOUT,
    )
    raw = outcome["text"]
    vote = "approve" if "VOTO: APPROVE" in raw.upper() else "reject"
    if outcome["killed"]:
        vote = "reject"
        raw = f"[circuit breaker: {outcome['reason']}] " + raw
    results[role] = {"reasoning": raw[:500], "vote": vote, "cost_usd": outcome.get("cost_usd")}


def deliberate(question: str, context: str, dry_run: bool = False) -> dict:
    """Lancia 3 agenti in parallelo, aggrega i voti, ritorna il verdetto."""
    results: dict = {}
    threads = []

    for role in ROLE_PROMPTS:
        t = threading.Thread(
            target=call_agent,
            args=(role, question, context, results, dry_run),
            daemon=True,
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=TIMEOUT + 5)

    votes = {role: data.get("vote", "reject") for role, data in results.items()}
    approve_count = sum(1 for v in votes.values() if v == "approve")
    reject_count = sum(1 for v in votes.values() if v == "reject")

    if approve_count > reject_count:
        verdict = "approve"
        majority_role = next(r for r, v in votes.items() if v == "approve")
    elif reject_count > approve_count:
        verdict = "reject"
        majority_role = next(r for r, v in votes.items() if v == "reject")
    else:
        # Pareggio 1-1-1: vince l'arbitro come tiebreaker
        verdict = votes.get("arbitro", "reject")
        majority_role = "arbitro (tiebreaker)"

    dissent = [r for r, v in votes.items() if v != verdict]

    return {
        "verdict": verdict,
        "votes": votes,
        "majority_role": majority_role,
        "dissent": dissent,
        "reasoning": {role: data.get("reasoning", "") for role, data in results.items()},
        "approve_count": approve_count,
        "reject_count": reject_count,
    }


def log_precedent(question: str, context: str, outcome: dict) -> None:
    """Logga il precedente in precedents.jsonl."""
    PRECEDENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "question": question[:200],
        "context": context[:300],
        "verdict": outcome["verdict"],
        "votes": outcome["votes"],
        "dissent": outcome["dissent"],
        "majority_reasoning": outcome["reasoning"].get(outcome.get("majority_role", "arbitro"), "")[:300],
    }
    with open(PRECEDENTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def find_precedents(question: str, limit: int = 3) -> list[dict]:
    """Cerca precedenti simili per keyword matching."""
    if not PRECEDENTS_FILE.exists():
        return []
    keywords = set(question.lower().split())
    results = []
    try:
        lines = PRECEDENTS_FILE.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines):
            try:
                entry = json.loads(line)
                q_words = set(entry.get("question", "").lower().split())
                overlap = len(keywords & q_words)
                if overlap >= 2:
                    results.append(entry)
                if len(results) >= limit:
                    break
            except Exception:
                continue
    except Exception:
        pass
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Supreme Court — deliberazione multi-agente")
    parser.add_argument("--question", required=True, help="Domanda da deliberare")
    parser.add_argument("--context", default="", help="Contesto aggiuntivo")
    parser.add_argument("--dry-run", action="store_true", help="Simula senza chiamare Claude")
    parser.add_argument("--show-precedents", action="store_true", help="Mostra precedenti simili prima di deliberare")
    args = parser.parse_args()

    if args.show_precedents:
        prec = find_precedents(args.question)
        if prec:
            print(f"\n📜 Precedenti simili ({len(prec)}):")
            for p in prec:
                print(f"  [{p['ts'][:10]}] {p['verdict'].upper()} — {p['question'][:80]}")
                if p.get("dissent"):
                    print(f"    Dissenso: {', '.join(p['dissent'])}")
        else:
            print("📜 Nessun precedente simile trovato.")

    print(f"\n⚖️  Corte convocata per: {args.question[:80]}")
    print("   Deliberazione in corso (3 agenti in parallelo)...")

    outcome = deliberate(args.question, args.context, dry_run=args.dry_run)

    print(f"\n📊 Voti: {outcome['approve_count']} approve / {outcome['reject_count']} reject")
    for role, vote in outcome["votes"].items():
        marker = "✅" if vote == "approve" else "❌"
        print(f"   {marker} {role.capitalize()}: {vote.upper()}")

    if outcome["dissent"]:
        print(f"   Dissenso registrato: {', '.join(outcome['dissent'])}")

    verdict_icon = "✅" if outcome["verdict"] == "approve" else "❌"
    print(f"\n{verdict_icon} VERDETTO: {outcome['verdict'].upper()}")

    if not args.dry_run:
        log_precedent(args.question, args.context, outcome)
        print(f"📜 Precedente loggato in {PRECEDENTS_FILE}")

    import sys
    sys.exit(0 if outcome["verdict"] == "approve" else 1)


if __name__ == "__main__":
    main()
