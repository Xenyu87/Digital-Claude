# Default Stacks

Quando l'utente non ha vincoli tecnici espliciti, scegli da questa lista invece di chiedere ogni volta. Tre combinazioni che funzionano per >80% dei casi non-programmer.

## Stack A — Web full-stack senza server

**Quando**: app web con login, dati, qualche pagina dinamica. Default per "voglio un'app che gestisce X".

- **Next.js 14** (App Router, TypeScript)
- **Supabase** (DB Postgres + auth + storage + realtime)
- **Tailwind + shadcn/ui** (design)
- **Vercel** (hosting frontend)
- **Resend** (email)

Costo: 0€/mese fino a soglie alte. Pro: $25 Supabase + $20 Vercel = $45 quando l'app cresce.

Niente server da gestire. Tutto cliccabile da dashboard web.

## Stack B — Sito di contenuti

**Quando**: blog, portfolio, documentazione, marketing site, landing page senza app.

- **Astro** + MDX
- **Tailwind + Tailwind Typography**
- **Vercel / Netlify / Cloudflare Pages** (uno qualsiasi)

Costo: 0€/mese. Velocissimo, SEO-friendly, niente JavaScript inutile.

## Stack C — Backend long-running

**Quando**: bot, scheduled jobs, processi che devono restare accesi (cron, listener webhook).

- **Node.js + TypeScript**
- **Telegraf / discord.js / Express** (a seconda)
- **Supabase** se serve persistenza
- **Railway** o **Fly.io** (hosting per processi continui — Vercel non serve qui)

Costo: ~$5/mese su Railway tier base.

## Cosa serve per scegliere

Quando l'utente descrive l'app, mappa su:

- ha **pagine + login + dati gestiti**? → Stack A
- è un **sito di contenuti** (post, articoli, info)? → Stack B
- è un **processo che gira da solo** (bot, alert, automazione)? → Stack C
- combinazioni: spesso A + C insieme (app web + bot di notifiche)

## Quando NON applicare il default

- l'utente ha già una preferenza espressa (es. "voglio Vue")
- esiste già un progetto con altro stack: continuare lì
- requisito specifico (es. mobile nativo, gaming, processing video) → richiede valutazione separata

## Anti-pattern

- chiedere all'utente "quale framework preferisci?" senza prima capire cosa vuole fare
- proporre 5 alternative ("o Next o Remix o Astro o..."): dà rumore
- combinare pezzi non testati insieme per "fare qualcosa di unico" — non è il momento, prima fai funzionare il default

Le ricette in `recipes/` usano questi stack come base.
