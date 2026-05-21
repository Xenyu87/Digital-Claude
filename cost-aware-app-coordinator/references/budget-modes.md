# Budget Modes

Tre modalità che regolano quanto leggere, quanto pensare, quanto scrivere.

## Economico (default)

Quando: task chiari, modifiche locali, file noti.

- Lettura: solo file richiamati o citati nel prompt
- Pianificazione: implicita, niente Plan tool
- Output: 2-6 righe, formato `Fatto / Verifica`
- Specialisti: mai per default
- Niente spiegazioni non richieste

## Bilanciato

Quando: feature media, refactor su 2-5 file, fix con causa non ovvia.

- Lettura: file impattati + 1 livello di dipendenze
- Pianificazione: lista breve di passi
- Output: bullet sintetici, motiva solo le scelte non ovvie
- Specialisti: solo se il sotto-task è chiaramente fuori scope (es. QA in fase di rilascio)

## Massima sicurezza

Quando: cambio architetturale, sicurezza, dati produzione, migrazioni, release.

- Lettura: tutti i file critici impattati + audit cross-cutting
- Pianificazione: piano esplicito con gate
- Output: piano + diff annotato + checklist di verifica
- Specialisti: usare `code-reviewer` o agente Review/Audit, e QA prima del rilascio

## Escalation automatica

Esci da Economico verso Bilanciato o Massima sicurezza se incontri uno di:

- modifica a file marcati critici in `AI_STRUCTURE.md`
- modifica a configurazioni di build, CI, segreti, schema DB
- gate di rischio attivo (vedi `decision-risk-gates.md`)
- richiesta esplicita dell'utente

## De-escalation

Da Massima sicurezza torna a Bilanciato dopo che il rischio è chiuso. Non rimanere in modalità costosa per inerzia.

## Indicatori di spreco

Se ti accorgi di:

- aver letto file non usati nella decisione
- aver scritto più di 30 righe di output per un fix banale
- aver attivato uno specialista senza gate

→ registra in `AI_AGENT_LOG.md` e correggi il modo per il prossimo turno.
