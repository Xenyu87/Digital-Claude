# Ricette

Ricette di partenza per app comuni. Ognuna è uno **scheletro con scelte di default sensate**, non un boilerplate fisso. Ti dà:

- stack già scelto con motivazione comprensibile
- struttura iniziale e primi 3-5 file
- come testare in browser (visual-first)
- come metterla online (deploy)
- costo mensile stimato
- **punti di personalizzazione**: dove modifichi a piacere

Le ricette **guidano la skill, non te**: quando dici "voglio fare X", io riconosco il pattern, applico la ricetta, e poi tu decidi cosa cambiare.

## Quando usare una ricetta

La skill apre la ricetta giusta automaticamente quando il task corrisponde. Tu puoi anche chiederla esplicitamente: "usa la ricetta blog" oppure "voglio una landing page con form".

## Quando NON usare una ricetta

- progetto molto specifico che non rientra in nessun pattern
- l'utente ha già scelto uno stack diverso
- modifica di un'app esistente (in quel caso si segue il workflow normale)

## Ricette disponibili

| File | Cosa fa | Stack default | Costo/mese tipico |
| --- | --- | --- | --- |
| [landing-page.md](landing-page.md) | sito vetrina con form contatti che invia email | Next.js + Vercel + Resend | 0€ fino a 3000 email/mese |
| [crud-with-auth.md](crud-with-auth.md) | tool admin per gestire dati con login | Next.js + Supabase + Vercel | 0€ fino a 500 MB DB |
| [data-dashboard.md](data-dashboard.md) | cruscotto con KPI e grafici | Next.js + Supabase + Tremor + Vercel | 0€ tier free |
| [content-site.md](content-site.md) | blog o sito contenuti markdown | Astro + Vercel/Netlify | 0€ |
| [bot.md](bot.md) | bot Telegram/Discord per automazioni | Node.js + Railway | ~5€ |

## Struttura comune di una ricetta

Ogni file ricetta ha le stesse sezioni, in quest'ordine:

1. **Cosa fa** — cosa offre l'app finita
2. **Stack scelto e perché** — comprensibile a un non-programmer
3. **Costo mensile stimato** — tier free e quando si paga
4. **Struttura iniziale** — quali file e cartelle
5. **Primi passi** — comandi concreti per avere "qualcosa che gira" entro un'ora
6. **Come testare in browser** — visual-first
7. **Deploy** — come metterla online
8. **Punti di personalizzazione** — cosa cambi facilmente, cosa è più rischioso modificare

## Aggiungere una ricetta

Quando un pattern di app si ripete in 2-3 progetti diversi, vale la pena codificarlo come ricetta. Apri un file nuovo seguendo la struttura sopra, aggiungi una riga nella tabella, aggiornа [release-notes.md](../references/release-notes.md).
