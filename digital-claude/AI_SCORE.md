# AI_SCORE v1.0 — digital-claude behavioral fingerprint
# Partitura compatta: copre il 90% delle decisioni in ~40 righe (~300 token).
# SKILL.md = reference completo per edge case. Questo file non lo sostituisce — lo riassume.
# Usare nei brief a subagenti invece di incollare SKILL.md intero.
# Rigenerato dal drain quando checksum SKILL.md cambia.

## INIT
ANCHORS → RESUME → HANDOFF → REGISTER → CONTEXT
skip: STRUCT(solo↑contratti/moduli) · DEC(solo↑decisione passata) · README(solo↑fallback)

## FAST_PATH
1-3file + scope chiaro + no auth/data/migration/deploy → edit inline · uscita: Done:/Verify:
altrimenti → applica routing completo (sezioni sotto)

## ROUTE
explore/grep/find >2file      → Explore(haiku)           [Gate3: OBBLIGATORIO]
ops + budget:eco              → ops-runner(haiku)         [Gate4: OBBLIGATORIO]
modifica 1-3file + chiaro     → sonnet inline
modifica >3file               → code-implementer(sonnet)  [Gate2: OBBLIGATORIO]
bug + causa sconosciuta       → code-debugger(sonnet)
design/stack/architettura     → architect(opus)
audit/sicurezza               → code-reviewer(sonnet)
bug grave dopo 2 tentativi    → code-debugger→escalate opus

## GATES
G1: routing-hint.suggested_subagent presente → spawn SUBITO, no inline (eccetto fast_path)
G2: edit >3file → code-implementer OBBLIGATORIO · main non tocca file prod
G3: grep/find >2file → Explore OBBLIGATORIO · no bash grep inline
G4: ops+eco → ops-runner OBBLIGATORIO · no bash inline se output richiede parsing
G5: bypass-mode + azione rischiosa(rm/force-push/DROP/deploy) → bypass-guardian PRIMA

## MODEL
haiku: explore · ops · log · qa deterministici
sonnet: default modify · debug · review
opus: arch · design (solo se main=opus O risk gate)
tokens_residual < 20k → forza haiku sempre

## BUDGET
eco (default): letture minime · subagente solo se giustificato
balanced: letture mirate sui file impattati
max: letture estese · double-check · audit
@50% budget → riga di avviso · @80% → chiedi conferma prima di letture costose

## OUTPUT
Done: <azione concisa> / Verify: <come l'utente verifica>
+dettagli solo per: rischi · scelte non ovvie · blocchi · azioni utente necessarie
For_you: quando serve config/env/test/deploy/pagamento

## DRIFT (ogni 3 turni su task non banali)
0.0-0.3 → ON_TRACK · 0.3-0.6 → avvisa e chiedi · >0.6 → STOP proponi task2

## DONE (checklist mentale pre-chiusura)
side_effect applicati (build/restart/migration)? · verificato funzionante (non solo "dovrebbe")?
utente può usarlo adesso senza step extra? · HANDOFF aggiornato con file toccati?
poi: python scripts/update_ai_resume.py <project_root>
