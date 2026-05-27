# Ricetta: Landing page con form contatti

## Cosa fa

Sito vetrina con una o più sezioni (hero, features, pricing, FAQ, contatti). Il form contatti invia email all'utente quando qualcuno compila. Tutto pronto per Google Analytics o simili.

## Stack scelto e perché

- **Next.js 14 (App Router)** — framework moderno, gestisce sia pagine statiche che API in un unico progetto. Non serve gestire un server.
- **Tailwind CSS** — modificare il design cambiando classi nelle stringhe, niente file CSS separati. Più veloce per iterare.
- **Resend** per le email — API semplice (1 chiave), 3000 email/mese gratis. Alternativa: SendGrid, Postmark.
- **Vercel** per l'hosting — deploy con `git push`, certificato HTTPS automatico, dominio custom incluso.

## Costo mensile stimato

- Vercel: 0€ fino a 100 GB di traffico/mese (in pratica: migliaia di visitatori)
- Resend: 0€ fino a 3000 email/mese
- Dominio: ~10€/anno se vuoi `tuomarchio.com` invece di `tuoprogetto.vercel.app`

**Totale realistico**: 0€/mese + ~10€/anno per il dominio.

## Struttura iniziale

```
src/
├── app/
│   ├── page.tsx              # homepage (hero, features, contatti)
│   ├── layout.tsx            # header + footer comuni
│   └── api/contact/route.ts  # endpoint che invia l'email
├── components/
│   ├── Hero.tsx
│   ├── Features.tsx
│   └── ContactForm.tsx
└── lib/
    └── email.ts              # client Resend
```

## Primi passi

1. `npx create-next-app@latest mio-sito --typescript --tailwind --app`
2. crea account su [resend.com](https://resend.com), copia la API key in `.env.local` come `RESEND_API_KEY=...`
3. `npm install resend`
4. crea `src/app/api/contact/route.ts` con un POST che riceve `{nome, email, messaggio}` e chiama Resend
5. `npm run dev` → apri `http://localhost:3000`

Risultato dopo 1 ora: sito locale che funziona, form che invia email a te.

## Come testare in browser

1. apri `http://localhost:3000`
2. compila il form con dati finti
3. controlla la tua casella mail: arriva l'email?
4. se non arriva → guarda il terminale dove gira `npm run dev`, di solito c'è un errore visibile

**Cosa segnalarmi se non funziona:**
- "il form non si invia" (problema frontend)
- "il form si invia ma l'email non arriva" (problema Resend o spam)
- "vedo errore 500" (problema codice — copiami il messaggio dal terminale)

## Deploy

1. crea repo GitHub, fai `git push`
2. vai su [vercel.com](https://vercel.com), "Import Git Repository"
3. aggiungi `RESEND_API_KEY` nelle Environment Variables di Vercel
4. clicca Deploy

Online in ~3 minuti. URL provvisorio: `mio-sito.vercel.app`. Per dominio custom: Settings → Domains.

## Punti di personalizzazione

**Facili (modifichi quando vuoi):**
- testi e immagini in `Hero.tsx`, `Features.tsx`
- colori e font: `tailwind.config.ts` + `globals.css`
- aggiungere sezioni nuove: nuovo componente in `components/` e import in `page.tsx`
- destinatario dell'email: variabile in `route.ts`
- aggiungere campi al form: modifica `ContactForm.tsx` e `route.ts` di pari passo

**Più rischiosi (chiedi conferma prima):**
- cambiare framework (Next.js → altro)
- aggiungere autenticazione (cambia struttura)
- integrare pagamenti (Stripe) — diventa un'altra ricetta

## Estensioni tipiche

- form con Calendly embed → ricetta separata se diventa core
- newsletter con Resend Audiences → aggiungi un endpoint
- analytics con Vercel Analytics o Plausible (gratis fino a soglie)
- dark mode → Tailwind ha pattern pronto
