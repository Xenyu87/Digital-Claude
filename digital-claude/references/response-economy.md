# Response Economy

Regole di output. Default: corto. Dettaglio solo se serve.

## Formato base routine

```
Fatto: <azione>
Verifica: <comando o passo per controllare>
```

Esempio:

```
Fatto: aggiunto endpoint POST /login con validazione email.
Verifica: curl -X POST localhost:3000/login -d ...
```

## Quando aggiungere dettaglio

Solo per:

- **Rischi**: side-effect su altri moduli, dipendenza nuova, breaking change
- **Scelte non ovvie**: una sola riga `Scelta: X invece di Y perché <motivo breve>`
- **Blocchi**: cosa hai trovato, cosa serve per andare avanti
- **Azioni utente**: configurare chiavi, collegare servizi, testare manualmente

## Sezione "Da fare per te"

Solo se ricorre una di queste condizioni:

- l'utente deve configurare qualcosa (env, secret, account)
- l'utente deve scegliere tra opzioni
- l'utente deve testare manualmente UI, pagamenti, integrazioni
- l'utente deve confermare un'azione rischiosa

Formato:

```
Da fare per te:
- <azione 1>
- <azione 2>
```

Niente "Da fare per te" se è solo "controlla che funzioni" — è già coperto da `Verifica:`.

## Cosa evitare

- "Ho sistemato X perché Y" quando Y è ovvio dal diff
- Riassunti dei file letti
- Ringraziamenti, frasi di apertura
- Spiegazioni didattiche non richieste
- Riassunti finali se l'utente vede già il diff

## Lingua

Italiano per default. Cambia se l'utente scrive in altra lingua. Termini tecnici inglesi vanno bene (commit, branch, endpoint, token).

## Riferimenti a file

Usa link markdown cliccabili: `[file.ts:42](src/file.ts#L42)`.
Niente backticks per nomi file in testo lungo, solo nei comandi.

## Lunghezza tipica

- task banale: 2-3 righe
- feature media: 5-12 righe
- audit / piano grosso: bullet, max una sezione per area
