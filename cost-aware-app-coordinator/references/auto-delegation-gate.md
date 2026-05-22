# Auto-Delegation Gate

Regole di enforcement per evitare il drift "suggested→used": il main agent (anche Opus) non esegue inline task che appartengono a un subagent più economico.

## Quando attivare

### Gate 1 — routing-hint ha priorità

Condizione: il prompt contiene `<routing-hint>` con `suggested_subagent` non vuoto e `model: sonnet|haiku`.

Azione: spawna immediatamente `Agent(subagent_type=<suggested>, model=<suggested_model>)`. Il main non legge file, non esegue bash, non edita.

Eccezione: task banale conclamato (<2 file, <1 turno di lavoro, niente decisioni).

### Gate 2 — tetto Opus per modifica

Condizione: task richiede edit su >3 file.

Azione: delega obbligatoria a `code-implementer` (sonnet). Main agent fa solo:
1. piano di modifica (quale file, quale change)
2. dispatch a `code-implementer` con briefing autocontenuto
3. verifica del risultato (diff review, non re-esecuzione)

### Gate 3 — Haiku per esplorazione

Condizione: qualsiasi pattern tra questi — grep/find su >2 file, "leggi README/struttura del progetto", "dove sta X", "cosa fa il modulo Y".

Azione: `Explore` (haiku) sempre. Il main non esegue grep inline su più di 2 file.

### Gate 4 — ops + Economico

Condizione: categoria ops + budget Economico.

Azione: `ops-runner` (haiku) per systemctl/journalctl/cron/ss/df/lsof. Niente bash inline se l'output richiede parsing o correlazione tra più righe.

## Anti-pattern

- **Opus che fa 5 grep su 8 file invece di spawnare Explore**: brucia contesto prezioso, viola Gate 3. Costo reale: ~8× rispetto a haiku per lo stesso risultato.
- **Main agent che edita 6 file "perché ci vuole poco"**: viola Gate 2. Il problema non è il tempo, è il contesto accumulato e il rischio di regressione senza verifica indipendente.
- **Ignorare routing-hint perché "tanto so già cosa fare"**: viola Gate 1. Il hint è emesso dalla dashboard con dati reali di categoria; ignorarlo sistematicamente causa il drift 50% documentato nei dati.
- **ops-runner spawnato in budget Bilanciato per un comando banale**: overhead inutile — Gate 4 si attiva solo su Economico + ops. In Bilanciato, bash inline su 1 comando è accettabile.
- **Override silenzioso**: bypassare un gate senza dichiararlo nella risposta rende il drift invisibile e non correggibile.

## Esempio di flusso corretto

Task: "Aggiungi la colonna `last_login` alla tabella `users` e aggiorna l'endpoint `/api/users`."

```
Main (Opus):
  1. classifica: modifica app · budget Economico · 3 file stimati (migration, schema TS, handler)
  2. Gate 2: >3 file? No (3 ≤ 3) → borderline. Routing-hint presente? Sì: suggested=code-implementer, model=sonnet → Gate 1 attivo.
  3. Spawna: Agent(subagent_type="code-implementer", model="sonnet",
               prompt="Aggiungi colonna last_login (timestamp nullable) alla tabella users.
                       File da toccare: supabase/migrations/NNNN_add_last_login.sql,
                       types/database.ts (aggiorna UserRow), api/users/route.ts (aggiungi campo in SELECT).
                       Niente altri cambi. Rispondi con diff e comando di test.")
  4. Riceve risultato → verifica diff (lettura rapida 3 file)
  5. Conferma all'utente: "Fatto: migration + type + endpoint aggiornati. Verifica: npx supabase db push && curl /api/users"
```

Il main ha scritto 0 righe di codice di prodotto.

## Eccezioni legittime (quando va bene NON delegare)

- **Fast path 1-3 file con scope banale**: modifica già descritta completamente (es. "cambia il colore del bottone in #333"), nessuna decisione aperta. Costo delega > costo inline.
- **Override esplicito dell'utente**: "fallo tu", "non delegare", "rimani sul main". Indicare nella risposta: `[gate bypassato su richiesta utente]`.
- **Riproduzione bug 1-shot**: riprodurre un crash con un singolo comando bash (es. `curl -X POST ...`) — non c'è output da parsare, è una verifica atomica.
- **Lookup singolo fatto noto**: "qual è la porta di Supabase?" risponde il main in 1 riga; spawnare Explore sarebbe overhead puro.
- **Subagent già attivo nella sessione**: se `code-implementer` ha già il contesto da un turno precedente, riutilizzalo via `SendMessage` invece di spawnarne uno nuovo.
