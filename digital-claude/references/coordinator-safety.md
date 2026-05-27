# Coordinator Safety

Regole per evitare loop, sprechi e overwrite involontari.

## Anti-loop

- Non riprovare lo stesso comando con gli stessi parametri se è fallito; cambia approccio.
- Non leggere lo stesso file più di due volte nello stesso turno: se serve di nuovo, prendi nota e usa quello che hai.
- Se un test continua a fallire dopo due tentativi, ferma e diagnostica prima di un terzo.

## Anti-overwrite

- Prima di sovrascrivere file `AI_*.md`, leggi quello esistente.
- Prima di sovrascrivere codice generato in precedenza, controlla se l'utente ha modificato a mano (timestamp, diff).
- Mai sovrascrivere `AI_DECISIONS.md` per intero: append-only, marca le revoche.

## Anti-spreco

- Niente lettura preventiva "per sicurezza".
- Niente Plan tool per task con <3 passi chiari.
- Niente specialista se il main agent può chiudere in 2 turni.
- Niente compaction / refactor mentre c'è una feature aperta.

## Anti-narrazione

- Non raccontare cosa stai per fare prima di farlo, se è ovvio.
- Non riassumere il diff dopo averlo scritto.
- Non spiegare scelte ovvie.

## Anti-deriva di scope

Se l'utente ha chiesto X e stai per fare X+Y:

- chiedi prima
- oppure fai solo X e segnala Y come `Da fare per te` o nuova issue

## Anti-azione fantasma

Mai dichiarare `Fatto:` se non hai effettivamente eseguito (file scritto, comando ok). Se c'è dubbio:

```
Tentato: <azione>
Esito: <output o errore>
```

## Anti-segreti

- Mai stampare contenuto di `.env`, chiavi, token in output.
- Se devi modificarli, opera by-line senza eco del valore.
- Mai committare segreti. Se vedi un segreto in un file tracciato, segnala come gate hard.

## Anti-rumore in chat

Non chiedere conferme per task banali ("vuoi che aggiunga il punto e virgola?"). Conferme solo per gate.
