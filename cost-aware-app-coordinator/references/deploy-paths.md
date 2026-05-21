# Deploy Paths

Tre percorsi tipici per mettere un'app online, scelti per facilità d'uso e costo. Script pronti in `assets/scripts/`.

## Vercel — siti e app Next.js

**Quando**: Stack A (Next.js), Stack B (siti statici se vuoi un solo provider).

**Costo**: 0€ Hobby plan (uso personale). Pro $20/mese se commerciale.

**Setup una volta**:
1. account su [vercel.com](https://vercel.com), connetti GitHub
2. installa CLI: `npm i -g vercel`
3. nel progetto: `vercel login`

**Deploy**: `bash assets/scripts/deploy-vercel.sh` oppure `vercel --prod`.

**Env vars**: dashboard Vercel → Project Settings → Environment Variables. Importanti: `RESEND_API_KEY`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, ecc.

## Netlify — siti statici

**Quando**: Stack B (Astro, blog, landing) se preferisci interface non Vercel.

**Costo**: 0€ Starter plan.

**Setup**:
1. [netlify.com](https://netlify.com), connetti GitHub
2. `npm i -g netlify-cli`, `netlify login`

**Deploy**: `bash assets/scripts/deploy-netlify.sh` oppure `netlify deploy --prod`.

## Railway — backend long-running

**Quando**: Stack C (bot, worker, server custom), o se serve un DB extra.

**Costo**: $5/mese Hobby plan (5$ in usage credits inclusi). Per uso leggero rientri quasi sempre.

**Setup**:
1. [railway.app](https://railway.app), connetti GitHub
2. `npm i -g @railway/cli`, `railway login`

**Deploy**: `bash assets/scripts/deploy-railway.sh` oppure `railway up`.

**Env vars**: dashboard Railway → Variables.

## Cloudflare Pages — siti statici economici

**Quando**: alternativa a Vercel/Netlify se hai dominio già su Cloudflare. Build minutes illimitati gratis.

**Costo**: 0€ tier free, soglie generose.

**Setup**: dashboard Cloudflare → Pages → Connect to Git.

**Deploy**: automatico ad ogni `git push`. Niente CLI necessaria.

## Quale scegliere

| Tipo app | Provider raccomandato | Backup |
| --- | --- | --- |
| Next.js full-stack | Vercel | — |
| Sito statico (Astro/blog) | Vercel o Cloudflare Pages | Netlify |
| Bot Telegram/Discord | Railway | Fly.io |
| Worker/scheduled jobs | Railway | Fly.io |

Per Stack A+C insieme: Vercel (frontend) + Railway (backend bot/worker). Sono indipendenti.

## Custom domain

Tutti e tre supportano dominio custom in pochi click + certificato HTTPS automatico. Costo dominio: ~10€/anno via Namecheap/Cloudflare/etc.

## Cose da non fare

- non mettere bot/worker su Vercel (le serverless function muoiono dopo 10s; il bot non resta acceso)
- non mettere DB sul filesystem dell'host (Railway/Vercel li resetta a ogni deploy): usa Supabase o Railway DB esterno
- non hard-codare API key nel codice: sempre `.env` locale + env vars sul provider
- non lasciare `git push` automatici se non hai testato: prima `npm run build` in locale
