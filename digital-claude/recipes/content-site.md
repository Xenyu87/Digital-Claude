# Ricetta: Blog / sito contenuti

## Cosa fa

Sito di contenuti: blog, documentazione, portfolio, knowledge base. Articoli scritti come file Markdown, sito generato statico → velocissimo, costo zero, SEO-friendly.

## Stack scelto e perché

- **Astro** — fatto apposta per siti di contenuto. Più veloce di Next.js per pagine statiche, niente JavaScript inutile, ottimo SEO.
- **MDX** — Markdown + componenti React/Vue dentro gli articoli (callouts, embed, ecc.).
- **Tailwind Typography** — stile leggibile per articoli senza scrivere CSS.
- **Vercel o Netlify o Cloudflare Pages** — uno qualunque, sono gratis e veloci per siti statici.

## Costo mensile stimato

- Hosting (Vercel/Netlify/Cloudflare): 0€ pratico per un blog
- Dominio: ~10€/anno opzionale

**Totale**: 0€/mese.

## Struttura iniziale

```
src/
├── content/
│   ├── config.ts             # schema dei collection (post, autori)
│   └── posts/
│       ├── primo-post.md
│       └── secondo-post.mdx
├── pages/
│   ├── index.astro           # homepage con lista post
│   ├── about.astro
│   └── posts/[slug].astro    # template singolo post
├── layouts/
│   ├── Layout.astro
│   └── BlogLayout.astro
└── components/
    ├── PostCard.astro
    └── Tag.astro
```

## Primi passi

1. `npm create astro@latest mio-blog` → scegli template "Blog"
2. `npx astro add tailwind mdx`
3. installa typography: `npm install @tailwindcss/typography` e aggiungi in `tailwind.config.ts`
4. crea il primo post in `src/content/posts/primo-post.md` con frontmatter (title, date, tags)
5. `npm run dev` → apri `http://localhost:4321`

Risultato dopo ~1 ora: blog locale con un post visibile, lista in homepage.

## Come testare in browser

1. apri `http://localhost:4321`
2. clicca sul post → carica? il rendering del markdown è leggibile?
3. controlla `view-source` (Ctrl+U) → vedi solo HTML pulito? (è la prova che è statico)
4. prova mobile (DevTools → Toggle device): testi leggibili, immagini scalano?

**Cosa segnalarmi:**
- "le immagini non si vedono" (path probabilmente sbagliato; in Astro vanno spesso in `public/`)
- "il post non appare in homepage" (frontmatter sbagliato o `getCollection` non legge la cartella giusta)
- "il sito è lento" (raro per Astro, ma controllo immagini non ottimizzate)

## Deploy

1. push su GitHub
2. importa su Vercel/Netlify/Cloudflare Pages (uno qualunque)
3. il sistema rileva Astro automaticamente, non serve configurare

Vedi `references/deploy-paths.md` per scegliere il provider.

## Punti di personalizzazione

**Facili:**
- aggiungere post: nuovo `.md` in `content/posts/`
- cambiare layout: modifica `Layout.astro` / `BlogLayout.astro`
- aggiungere pagine fisse (chi siamo, contatti): nuovo `.astro` in `pages/`
- cambiare font/colori: `tailwind.config.ts`
- attivare RSS: `@astrojs/rss` con 5 righe di codice

**Rischiosi:**
- aggiungere commenti dinamici (Disqus, Giscus): ok, ma valuta privacy
- aggiungere autenticazione/contenuti privati: cambia paradigma, valuta CRUD ricetta
- migrare da WordPress: serve mappare contenuto, può essere lungo

## Estensioni tipiche

- newsletter (Buttondown / Substack embed)
- ricerca full-text con Pagefind (gira nel browser, no server)
- analytics privacy-friendly: Plausible o Vercel Analytics
- multilingua: `astro-i18n` o struttura di cartelle
