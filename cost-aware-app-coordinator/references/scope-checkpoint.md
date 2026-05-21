# Scope Checkpoint

Protocollo per fermarsi e dividere il task quando lo scope è ambiguo, troppo ampio, o l'utente non ha esperienza tecnica. Protegge da "rabbit holes": ore di lavoro su qualcosa che poi non era quello che voleva.

## Quando attivare

Almeno uno dei seguenti:

- richiesta in <30 parole con verbi vaghi ("sistemami", "fammi funzionare", "aggiusta")
- più obiettivi nello stesso prompt ("crea X e poi metti anche Y e Z")
- l'utente ha dichiarato di non essere programmatore E il task richiede scelte tecniche
- stima del task > 2h o > 10 file impattati
- coinvolge auth, dati, pagamenti, deploy, integrazione esterna
- l'utente usa termini tecnici inconsistenti ("la pagina del db", "il login dell'API")

## Cosa fare

**Stop**. Non scrivere codice ancora. Fai un checkpoint in 3 mosse:

### 1. Rispecchia in italiano semplice

Riformula cosa hai capito, in 1-3 righe, senza gergo. Esempio:

```
Ho capito che vuoi: un sito dove i clienti prenotano un appuntamento e
ricevono email di conferma. Senza login. Per ora solo da computer.
È corretto?
```

### 2. Mostra le 2-3 scelte minime da fare adesso

Solo quelle che bloccano. Niente "vuoi Next.js o Astro" se non ha senso per l'utente. Esempio:

```
Per partire devo sapere:
1. Le email vanno a te o a un indirizzo specifico?
2. Bastano 5 orari fissi al giorno o serve calendario libero?
3. Per ora locale (sul tuo PC) o vuoi subito un link condivisibile?
```

Usa `AskUserQuestion` per i 2-3 punti, con 3-4 opzioni concrete ciascuno.

### 3. Dichiara il primo step (piccolo)

Dopo le risposte, dichiara cosa farai per primo, sempre piccolo:

```
Faccio per primo: pagina con il form (no email ancora, no salvataggio).
Lo vedrai in browser tra 10 minuti. Se è quello che immaginavi, andiamo
avanti col resto.
```

## Cosa NON fare

- non chiedere all'utente di "definire lo scope" (parolaccia tecnica, non aiuta)
- non elencare 10 scelte tecniche
- non procedere dichiarando "interpreto X" se l'utente non ha confermato
- non costruire la metà del progetto e poi chiedere "va bene?"
- non usare l'output `Da fare per te:` come scappatoia per evitare decisioni — ESEGUI dopo conferma

## Pattern di chiusura

Dopo i mini-step, ogni volta che chiudi un pezzo:

```
Fatto: <pezzo piccolo>
Verifica: <come l'utente controlla in browser/risultato visibile>

Prossimo pezzo (se va bene): <cosa segue>
```

Così l'utente sa sempre dove sei e cosa viene dopo.

## Soglia di escalation

Se dopo 2 checkpoint l'utente continua a essere vago, **non costruire**. Proponi:

```
Faccio fatica a inquadrare cosa vuoi. Ti aiuta se:
- ti mostro 2-3 esempi di siti/app simili?
- partiamo da una ricetta pronta (vedi recipes/) e tu mi dici cosa togliere?
```

## Anti-pattern

- "interpretazione creativa": l'agent indovina lo scope e procede senza conferma
- bandiera "Da fare per te" usata per scaricare 10 decisioni sull'utente in una volta
- sub-agent spawnati per task ambigui: amplificano il fraintendimento
- piano "agile" che diventa scope continuamente mobile: meglio una sola decisione chiara

## Quando NON fare checkpoint

- task piccolo classificato fast path (§0 SKILL.md): vai dritto
- l'utente ha già scritto un brief lungo e preciso (>200 parole, file/comandi specifici)
- continui un task aperto in `AI_HANDOFF.md` con scope già definito
