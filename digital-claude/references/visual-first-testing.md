# Visual-First Testing

Protocollo per testare app con un utente non programmatore. Niente stack trace, niente "guarda i log": l'utente apre il browser e descrive cosa vede.

## Principio

Type-check, build verde e test automatici verificano correttezza del codice, **non** correttezza della feature. L'app può compilare e fare la cosa sbagliata. L'utente è il giudice finale del comportamento visibile.

## Protocollo standard dopo una modifica UI

Dopo ogni modifica visibile, fornisci all'utente queste 4 cose:

```
URL da aprire: <es. http://localhost:3000/dashboard>
Cosa fare: <azione concreta in 1-3 step>
Cosa dovresti vedere: <descrizione attesa>
Cosa segnalarmi se sbagliato: <forme che il problema può prendere>
```

Esempio:

```
URL da aprire: http://localhost:3000/login
Cosa fare:
  1. inserisci una mail e password fittizie
  2. clicca "Accedi"
Cosa dovresti vedere: redirect a /dashboard con il tuo nome in alto a destra
Cosa segnalarmi se sbagliato:
  - "resto fermo su /login senza messaggio" → problema sessione
  - "vedo errore in pagina" → copia il testo dell'errore
  - "il nome non appare" → query profilo fallita
```

## Cosa l'utente NON deve fare

- non chiedergli di leggere stack trace o di "controllare la console JS"
- non chiedergli di fare richieste con curl
- non parlare di "props non passate", "useEffect", "rerender"

## Cosa fare quando l'utente dice "non funziona"

Sequenza in ordine:

1. **chiedi cosa vede** in 1 frase: "che cosa appare in pagina adesso?"
2. **chiedi cosa si aspettava**: "cosa dovrebbe apparire invece?"
3. **chiedi se c'è un messaggio in pagina** (errori 500, banner rossi, modal)
4. **solo dopo** chiedi "se hai voglia, apri DevTools (F12) → tab Console → screenshot di eventuali righe rosse"
5. se non si risolve, propongo di guardare insieme con uno screenshot o video breve

## Screenshot e Playwright

Per cambi UI a rischio medio/alto, fai uno screenshot tu stesso prima di consegnare:

- **Locale**: usa Playwright headless (`npx playwright screenshot http://localhost:3000 home.png`)
- **Già in produzione**: stesso comando con URL pubblico
- **Confronta** il prima/dopo se hai entrambi

Costo: setup di Playwright è ~2 minuti la prima volta. Poi è istantaneo.

Quando il setup non vale la pena (modifica banale): salta lo screenshot, basta il protocollo standard.

## Browser cross-check

Per pagine pubbliche o demo importanti, chiedi all'utente di aprire **anche da mobile**:

- DevTools → Toggle device toolbar → iPhone 12 / Android
- testi leggibili senza zoom?
- bottoni cliccabili senza centrare il dito?
- form usabili da pollice?

Anche qui: se l'utente dice "su mobile X non funziona", chiedi screenshot.

## Quando il visual non basta

Alcune cose non si vedono:

- email inviate (controlla tu via Resend dashboard)
- record creati su DB (Supabase Table Editor)
- ruoli/permessi (RLS Postgres) → testa con due utenti diversi
- cron/scheduled jobs → guarda log del provider

Per questi casi, dai all'utente istruzioni concrete tipo "vai su [resend.com/emails](https://resend.com/emails) e dimmi se vedi l'email partita".

## Output finale tipico

Dopo una modifica UI, chiusura tipica:

```
Fatto: <cosa è cambiato>
Verifica visiva: apri <url> e fai <azione>; dovresti vedere <X>.
Se vedi qualcosa di diverso, segnamelo descrivendo cosa vedi.
```
