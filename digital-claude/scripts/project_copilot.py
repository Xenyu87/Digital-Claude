#!/usr/bin/env python3
"""Give low-waste project guidance for frontend/backend/code work."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


EXCLUDED_DIRS = {".git", "node_modules", "dist", "build", "coverage", ".next", "android", "ios"}
STACK_MARKERS = {
    "React/Vite": ["vite.config.", "src/App.", "src/main."],
    "Next.js": ["next.config.", "app/page.", "pages/_app."],
    "Node/Express": ["server.js", "app.js", "src/routes", "src/controllers"],
    "Python": ["pyproject.toml", "requirements.txt", "app.py", "main.py"],
    "Docker": ["Dockerfile", "docker-compose.yml"],
}
AREA_KEYWORDS = {
    "frontend": ["frontend", "src/components", "src/pages", "app/", "pages/", ".tsx", ".jsx", ".css"],
    "backend": ["backend", "src/controllers", "src/routes", "src/services", "api/", "server"],
    "database": ["migration", "schema", "prisma", "models", "database", "db"],
    "tests": ["test", "__tests__", "spec", "playwright", "vitest", "jest"],
    "deploy": ["docker", "deploy", ".github/workflows", "nginx", "vercel"],
    "security": ["auth", "jwt", "session", "secret", ".env", "permission"],
}


def walk_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def detect_stack(root: Path, files: list[Path]) -> list[str]:
    rels = [path.relative_to(root).as_posix() for path in files]
    stack: list[str] = []
    for name, markers in STACK_MARKERS.items():
        if any(any(marker in rel for rel in rels) for marker in markers):
            stack.append(name)
    for package in [root / "package.json", root / "frontend" / "package.json", root / "backend" / "package.json"]:
        if package.exists():
            try:
                data = json.loads(package.read_text(encoding="utf-8"))
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                if "react" in deps and "React" not in stack:
                    stack.append("React")
                if "express" in deps and "Express" not in stack:
                    stack.append("Express")
                if "typescript" in deps and "TypeScript" not in stack:
                    stack.append("TypeScript")
            except (OSError, json.JSONDecodeError):
                pass
    return stack or ["stack non rilevato"]


def score_areas(root: Path, files: list[Path]) -> list[dict[str, object]]:
    scores = {area: 0 for area in AREA_KEYWORDS}
    for path in files:
        rel = path.relative_to(root).as_posix().lower()
        for area, keywords in AREA_KEYWORDS.items():
            if any(keyword in rel for keyword in keywords):
                scores[area] += 1
    return [{"area": area, "files": count} for area, count in sorted(scores.items(), key=lambda item: item[1], reverse=True) if count]


def app_type(stack: list[str], areas: list[dict[str, object]]) -> str:
    names = {str(item["area"]) for item in areas[:3]}
    stack_text = " ".join(stack).lower()
    if "frontend" in names and "backend" in names:
        return "full-stack app"
    if "react" in stack_text or "next" in stack_text:
        return "frontend/web app"
    if "express" in stack_text or "python" in stack_text:
        return "backend/API"
    return "software project"


def mode_recommendation(areas: list[dict[str, object]]) -> str:
    top = {str(item["area"]) for item in areas[:3]}
    if top & {"security", "database", "deploy"}:
        return "Bilanciato"
    return "Economico"


def guardrail_rule(path: str) -> str:
    lower = path.lower()
    if "package-lock.json" in lower or lower.endswith((".lock", "yarn.lock", "pnpm-lock.yaml")):
        return "Evita lettura completa: usa package.json o query mirate sul lockfile solo per dipendenze specifiche."
    if any(part in lower for part in ["/dist/", "/build/", "/coverage/", "/android/", "/ios/"]):
        return "Probabile output generato: non leggere salvo task esplicito su build/release."
    if lower.endswith((".json", ".md")):
        return "File ad alto costo: usa rg, heading o sezioni mirate invece di leggerlo intero."
    return "File grande: usa rg e letture per funzione/sezione, non una lettura completa."


def context_guardrails(large_text: list[dict[str, object]]) -> list[dict[str, object]]:
    guardrails: list[dict[str, object]] = []
    for item in large_text[:8]:
        path = str(item.get("path", ""))
        if not path:
            continue
        guardrails.append(
            {
                "target": path,
                "estimated_tokens": item.get("estimated_tokens", 0),
                "rule": guardrail_rule(path),
            }
        )
    return guardrails


def guardrail_prompt_lines(guardrails: list[dict[str, object]]) -> str:
    if not guardrails:
        return ""
    lines = ["Guardrail contesto specifici del progetto:"]
    for item in guardrails[:5]:
        lines.append(f"- {item.get('target', '')}: {item.get('rule', '')}")
    return "\n".join(lines) + "\n"


def prompts(root: Path, kind: str, guardrails: list[dict[str, object]]) -> dict[str, str]:
    base = (
        f"Progetto: {root}\n"
        "Usa AGENTS.md e AI_CONTEXT.md se presenti. Prima leggi solo routing/docs mirati, poi usa rg per trovare i file.\n"
        "Evita lockfile, build/dist, asset generati e letture complete di file grandi.\n"
        f"{guardrail_prompt_lines(guardrails)}"
    )
    return {
        "analysis": base + "Obiettivo: analizza la richiesta e dimmi il piano minimo, file probabili, rischi token e test utili prima di modificare.",
        "frontend": base + "Obiettivo: implementa la parte frontend seguendo stile esistente, stati UI, responsive, e verifica mirata.",
        "backend": base + "Obiettivo: implementa backend/API con validazione, errori chiari, contratti e test mirati.",
        "review": base + "Obiettivo: fai review pre-PR. Trova bug, regressioni, rischi sicurezza/dati, test mancanti e output breve.",
    }


def analyze(root: Path) -> dict[str, object]:
    root = root.resolve()
    files = walk_files(root)
    stack = detect_stack(root, files)
    areas = score_areas(root, files)
    risks = []
    large_text = sorted(
        [
            {"path": path.relative_to(root).as_posix(), "estimated_tokens": max(1, round(path.stat().st_size / 4))}
            for path in files
            if path.suffix.lower() in {".js", ".jsx", ".ts", ".tsx", ".md", ".json", ".py"} and path.stat().st_size >= 12000
        ],
        key=lambda item: int(item["estimated_tokens"]),
        reverse=True,
    )[:8]
    if large_text:
        risks.append("Use rg/sections for large files instead of full reads.")
    if not (root / "AGENTS.md").exists() or not (root / "AI_CONTEXT.md").exists():
        risks.append("Project context docs are incomplete.")
    likely_type = app_type(stack, areas)
    mode = mode_recommendation(areas)
    guardrails = context_guardrails(large_text)
    return {
        "root": str(root),
        "app_type": likely_type,
        "budget_mode": mode,
        "stack": stack,
        "dominant_areas": areas[:6],
        "context_risks": risks,
        "large_text_files": large_text,
        "context_guardrails": guardrails,
        "recommended_workflow": [
            "Read AGENTS.md and AI_CONTEXT.md first when present.",
            "Use rg to locate only the files for the requested feature.",
            "Implement the smallest vertical slice that proves frontend/backend contract.",
            "Run the narrowest meaningful test, then broaden only for auth/data/deploy risk.",
        ],
        "prompts": prompts(root, likely_type, guardrails),
    }


def print_text(result: dict[str, object]) -> None:
    print(f"Project: {result['root']}")
    print(f"Type: {result['app_type']}")
    print(f"Budget mode: {result['budget_mode']}")
    print("Stack:")
    for item in result["stack"]:
        print(f"- {item}")
    print("Dominant areas:")
    for item in result["dominant_areas"]:
        print(f"- {item['area']}: {item['files']} files")
    print("Context risks:")
    for item in result["context_risks"]:
        print(f"- {item}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = analyze(Path(args.path))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_text(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
