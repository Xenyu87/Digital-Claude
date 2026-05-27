# Decision and Risk Gates

Azioni che richiedono conferma esplicita prima di procedere.

## Gate hard (sempre fermarsi)

Non procedere senza conferma in chat:

- `git push --force` (specie su main / master)
- `git reset --hard`, `git clean -fd`
- `rm -rf` su cartelle di progetto
- drop / truncate / alter table su DB
- migrazioni su dati produzione
- rotazione o lettura segreti, chiavi API, token
- modifica di policy IAM, ruoli, permessi cloud
- pubblicazione package (npm publish, pypi, ecc.)
- chiusura/apertura PR, merge su branch protetti
- invio messaggi a sistemi esterni (Slack, email, webhook)

## Gate soft (escalation budget)

Non bloccanti ma fanno passare a Bilanciato o Massima sicurezza:

- modifica file di configurazione di build, CI, deploy
- aggiunta o rimozione di dipendenze
- modifica di file marcati critici in `AI_STRUCTURE.md`
- cambio di schema dati locale
- modifica di test che validano contratti pubblici

## Procedura al gate hard

1. Stop. Non eseguire.
2. Riassumi in 1-3 righe cosa stavi per fare e perché.
3. Chiedi conferma esplicita.
4. Procedi solo dopo "sì", "ok", "procedi" chiaro.

Esempio:

```
Sto per: rm -rf node_modules e reinstallare da zero.
Motivo: dipendenza corrotta blocca build.
Procedo?
```

## Reversibilità

Prima di un'azione, valuta:

- è reversibile in <1 minuto? → procedi
- è reversibile ma con effort? → segnala e procedi
- non è reversibile? → gate hard

## Effetti su shared state

Tutto ciò che è visibile fuori dalla macchina locale è gate hard:

- push remoti
- commenti su PR / issue
- modifiche a infrastruttura condivisa
- caricamento file su servizi terzi

## Una conferma vale per scope, non per categoria

Se l'utente conferma `git push` per un branch, questo non autorizza altri push successivi. Chiedi di nuovo per ogni nuova azione rischiosa.
