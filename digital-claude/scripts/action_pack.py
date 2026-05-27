#!/usr/bin/env python3
"""Build practical action packs and expert prompts for a monitored project."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_activity_analyzer import read_sessions, score
from pr_readiness_check import audit as pr_audit
from project_copilot import analyze
from project_docs_audit import audit as docs_audit


ACTION_PACK_SESSION_LIMIT = 25


def guardrail_text(guardrails: list[dict[str, object]]) -> str:
    if not guardrails:
        return ""
    lines = ["Guardrail contesto da rispettare:"]
    for item in guardrails[:5]:
        lines.append(f"- {item.get('target', '')}: {item.get('rule', '')}")
    return "\n".join(lines) + "\n"


def expert_prompt(project: Path, expert: str, guardrails: list[dict[str, object]] | None = None) -> str:
    base = (
        f"Progetto: {project.resolve()}\n"
        "Usa AGENTS.md e AI_CONTEXT.md se presenti. Non leggere file grandi interi: usa rg e sezioni mirate.\n"
        f"{guardrail_text(guardrails or [])}"
    )
    goals = {
        "Context optimizer": "Trova i 5 sprechi principali di contesto/token e proponi regole pratiche per evitarli.",
        "Frontend/UX expert": "Analizza o implementa la UI con attenzione a workflow, stati, responsive e coerenza visiva.",
        "Backend/API contract expert": "Controlla contratti API, validazione, errori, autorizzazioni e test backend minimi.",
        "QA/Test expert": "Definisci test minimi ad alto valore e verifica rischi di regressione.",
        "Security/auth expert": "Cerca rischi auth, segreti, permessi, sessioni, input non validati e dati sensibili.",
        "Data/migration expert": "Controlla schema, migrazioni, consistenza dati, rollback e query rischiose.",
        "DevOps/release expert": "Controlla build, env, deploy, Docker/CI e comandi di rilascio sicuri.",
        "Context/documentation maintainer": "Aggiorna solo docs utili al routing AI, evitando duplicati e riassunti lunghi.",
    }
    return base + "Ruolo: " + expert + "\nObiettivo: " + goals.get(expert, "Fai una review mirata e breve nel tuo dominio.") + "\nOutput: rischi, file da leggere, piano minimo, test consigliati."


def superplan_prompt(project: Path) -> str:
    return (
        f"Progetto: {project.resolve()}\n"
        "Crea un Superplan prima di implementare.\n"
        "Includi: obiettivo, utenti, workflow principali, pagine/sezioni, backend/API, dati, permessi, rischi, milestone, test minimi e cosa riusare dall'esistente.\n"
        "Non duplicare funzionalita esistenti: prima cerca routing/docs mirati e usa rg per verificare componenti/API gia presenti.\n"
        "Output breve ma operativo, con ordine di implementazione consigliato."
    )


def warning_tasks(pr: dict[str, object], docs: dict[str, object], copilot: dict[str, object]) -> list[dict[str, str]]:
    tasks: list[dict[str, str]] = []
    if pr.get("untracked"):
        tasks.append(
            {
                "priority": "alta",
                "task": "Rivedi file non tracciati",
                "why": "Evita di lasciare fuori test, componenti o modifiche necessarie dalla PR.",
                "prompt": "Controlla i file non tracciati, dimmi quali vanno inclusi e quali ignorati, senza cancellare nulla.",
            }
        )
    if pr.get("risky_files"):
        tasks.append(
            {
                "priority": "alta",
                "task": "Controlla file rischiosi/generati",
                "why": "Lockfile, build, env o asset generati possono creare rumore o rischi.",
                "prompt": "Analizza solo i file rischiosi cambiati e proponi cosa tenere, ignorare o verificare.",
            }
        )
    if docs.get("recommended_create"):
        tasks.append(
            {
                "priority": "media",
                "task": "Completa contesto AI minimo",
                "why": "Riduce riletture e istruzioni ripetute nelle prossime chat.",
                "prompt": "Crea solo i file AI minimi consigliati, evitando duplicati con docs esistenti.",
            }
        )
    if copilot.get("context_guardrails"):
        tasks.append(
            {
                "priority": "media",
                "task": "Applica guardrail file grandi",
                "why": "Abbassa consumo token evitando letture complete inutili.",
                "prompt": "Usa i Context Guardrails del progetto e leggi solo sezioni mirate con rg.",
            }
        )
    return tasks[:5]


def build_actions(project: Path) -> dict[str, object]:
    project = project.resolve()
    copilot = analyze(project)
    pr = pr_audit(project)
    docs = docs_audit(project)
    guardrails = copilot.get("context_guardrails", [])
    agent = score(read_sessions(ACTION_PACK_SESSION_LIMIT), str(project))
    experts = agent.get("suggested_experts", [])
    top_expert = experts[0]["expert"] if experts else "Context optimizer"
    actions = [
        {
            "name": "Superplan",
            "when": "Prima di creare app/software, rebuild o sezioni grandi.",
            "prompt": superplan_prompt(project),
        },
        {
            "name": "Analisi Economica",
            "when": "Prima di una feature o se non sai dove mettere mano.",
            "prompt": copilot["prompts"]["analysis"],
        },
        {
            "name": "Vertical Slice Full-stack",
            "when": "Quando frontend e backend devono cambiare insieme.",
            "prompt": (
                f"Progetto: {project}\n"
                "Leggi routing AI e trova con rg solo endpoint/componenti coinvolti.\n"
                "Implementa la minima fetta verticale frontend+backend, mantieni il contratto chiaro, poi proponi un test mirato."
            ),
        },
        {
            "name": "Review Pre-PR",
            "when": "Prima di commit/PR o quando ci sono file non tracciati.",
            "prompt": copilot["prompts"]["review"],
        },
        {
            "name": "Context Guardrails",
            "when": "Prima di aprire file grandi, lockfile, log o docs lunghi.",
            "prompt": (
                f"Progetto: {project}\n"
                f"{guardrail_text(guardrails if isinstance(guardrails, list) else [])}"
                "Applica questi guardrail: trova i file con rg, leggi solo sezioni mirate e segnala quando serve davvero una lettura completa."
            ),
        },
        {
            "name": f"Esperto Prioritario: {top_expert}",
            "when": "Quando vuoi spendere token in modo mirato sul rischio dominante.",
            "prompt": expert_prompt(project, str(top_expert), guardrails if isinstance(guardrails, list) else []),
        },
    ]
    expert_prompts = [
        {
            "expert": item["expert"],
            "reason": item["reason"],
            "prompt": expert_prompt(project, str(item["expert"]), guardrails if isinstance(guardrails, list) else []),
        }
        for item in experts[:6]
        if isinstance(item, dict)
    ]
    return {
        "root": str(project),
        "recommended_mode": copilot.get("budget_mode", ""),
        "primary_expert": top_expert,
        "warning_tasks": warning_tasks(pr, docs, copilot),
        "actions": actions,
        "expert_prompts": expert_prompts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = build_actions(Path(args.path))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Project: {result['root']}")
        print(f"Mode: {result['recommended_mode']}")
        print(f"Primary expert: {result['primary_expert']}")
        print("Actions:")
        for item in result["actions"]:
            print(f"- {item['name']}: {item['when']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
