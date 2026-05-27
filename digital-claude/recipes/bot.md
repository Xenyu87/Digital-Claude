# Ricetta: Bot Telegram / Discord

## Cosa fa

Bot che risponde a comandi, manda notifiche, fa azioni programmate. Tipico per: notifiche di sistema, automazioni personali, comunità Discord, alert da fonti esterne.

## Stack scelto e perché

- **Node.js + TypeScript** — runtime semplice, scrittura asincrona naturale.
- **Telegraf** (Telegram) o **discord.js** (Discord) — librerie ufficiali-de-facto, ben documentate.
- **Railway** per hosting — il bot deve essere **sempre acceso** (a differenza di un sito statico). Railway è la via più semplice per processi long-running. Alternativa: Fly.io.
- **Supabase** se il bot deve ricordare cose tra messaggi (utenti, preferenze).

## Costo mensile stimato

- Railway: ~5€/mese (Hobby plan, $5 in usage credits inclusi). Più hai bot, più consumi.
- Telegram bot: 0€ (Telegram non fa pagare i bot)
- Discord bot: 0€
- Supabase (se serve): 0€ tier free

**Totale**: ~5€/mese se il bot è semplice.

## Struttura iniziale

```
src/
├── index.ts              # entry point, avvia il bot
├── commands/
│   ├── start.ts
│   ├── help.ts
│   └── ping.ts
├── handlers/
│   ├── messageHandler.ts
│   └── errorHandler.ts
├── services/
│   └── notifier.ts       # invia messaggi su trigger esterni
└── lib/
    └── config.ts         # leggi env vars
```

## Primi passi (Telegram)

1. parla con [@BotFather](https://t.me/BotFather) su Telegram → `/newbot` → ottieni token
2. `mkdir mio-bot && cd mio-bot && npm init -y && npm install telegraf dotenv typescript @types/node`
3. `npx tsc --init`
4. crea `.env` con `BOT_TOKEN=...` (NON committare!)
5. crea `src/index.ts`:
   ```ts
   import { Telegraf } from "telegraf";
   import "dotenv/config";
   const bot = new Telegraf(process.env.BOT_TOKEN!);
   bot.start(ctx => ctx.reply("Ciao!"));
   bot.command("ping", ctx => ctx.reply("pong"));
   bot.launch();
   ```
6. `npx ts-node src/index.ts` → cerca il bot su Telegram, scrivigli `/start`

Risultato dopo ~1 ora: bot locale che risponde a `/start` e `/ping`.

## Come testare

1. avvia bot in locale (`ts-node`)
2. su Telegram/Discord, scrivi al bot → risponde?
3. testa ogni comando uno per uno
4. testa errori: cosa succede se mandi qualcosa di non previsto?

**Cosa segnalarmi:**
- "il bot non risponde" → controllа se è acceso il processo locale, e che il token sia corretto
- "risponde ma ignora certi comandi" → handler probabilmente non registrato
- "crash quando provo X" → copiami l'errore dal terminale

## Deploy

1. push su GitHub
2. su [railway.app](https://railway.app), "New Project" → "Deploy from GitHub repo"
3. Variables → `BOT_TOKEN`
4. Settings → cambia start command in `npm run start` (o quello che hai)
5. Deploy

Bot online 24/7. Per Discord stesso flusso, token diverso.

Vedi `references/deploy-paths.md` per dettagli su Railway.

## Punti di personalizzazione

**Facili:**
- aggiungere comandi: nuovo file in `commands/` + register in `index.ts`
- aggiungere risposte casuali, immagini, GIF
- inviare notifiche a un canale: `bot.telegram.sendMessage(CHAT_ID, "alert!")`
- programmare task: `node-cron` con expression cron

**Rischiosi:**
- bot multi-utente con sessioni: serve persistenza (Supabase) e gestione stati
- pagamenti (Telegram Payments): scope diverso, paywall
- moderazione automatica con AI: integrazione Claude API, attento ai costi

## Estensioni tipiche

- integrazione webhook esterni (es. Stripe, GitHub) → bot manda alert
- comando `/dailydigest` con cron giornaliero
- bottoni inline e menu interattivi (sia Telegram che Discord li supportano)
- bot Claude-API come backend per risposte conversazionali (occhio ai costi)
