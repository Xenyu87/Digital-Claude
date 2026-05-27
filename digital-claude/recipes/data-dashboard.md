# Ricetta: Dashboard dati

## Cosa fa

Cruscotto web con KPI in evidenza, grafici, tabelle filtrate. Legge dati da una fonte (DB, API, file CSV) e li visualizza. Tipico per: monitoraggio business, analytics, controllo metriche.

## Stack scelto e perché

- **Next.js 14** — base solida.
- **Supabase** se i dati nascono qui; altrimenti puoi collegare un DB esistente o caricare CSV.
- **Tremor** — libreria di componenti grafici fatti apposta per dashboard (cards, area chart, bar chart). Più veloce di Recharts a partire.
- **TanStack Table** se ti servono tabelle con filtri/ordinamento/paginazione.
- **Vercel** per hosting.

## Costo mensile stimato

- Vercel: 0€ tier free
- Supabase: 0€ fino a 500 MB
- **Se i dati sono molti (>1 GB)**: Supabase Pro $25/mese **oppure** sposta su Cloudflare D1 / Turso

**Totale**: 0€ per la maggioranza dei casi.

## Struttura iniziale

```
src/
├── app/
│   ├── page.tsx              # dashboard principale
│   ├── reports/[id]/page.tsx # report specifici
│   └── api/data/route.ts     # endpoint che fornisce dati aggregati
├── components/
│   ├── KpiCard.tsx
│   ├── TrendChart.tsx
│   └── DataTable.tsx
├── lib/
│   ├── supabase.ts
│   └── queries.ts            # query SQL/aggregazioni riutilizzabili
└── types/data.ts
```

## Primi passi

1. `npx create-next-app@latest mia-dashboard --typescript --tailwind --app`
2. `npm install @tremor/react @supabase/supabase-js`
3. crea Supabase project e una tabella di dati di esempio (es. `vendite` con `data, importo, prodotto`)
4. crea `lib/queries.ts` con 1-2 query (es. "totale per giorno", "top 5 prodotti")
5. nella `page.tsx` chiama le query e passa i risultati a `KpiCard` + `TrendChart`

Risultato dopo ~3 ore: 1 dashboard locale che mostra dati veri da Supabase.

## Come testare in browser

1. apri la dashboard locale
2. controlla che i numeri sui KPI matchino quelli che vedi nel Table Editor di Supabase
3. cambia un dato in Supabase → ricarica → si è aggiornato?
4. testa filtri (date, categoria) se ci sono

**Cosa segnalarmi:**
- "i numeri non corrispondono" (logica di aggregazione errata)
- "il grafico è vuoto" (probabilmente formato dati non allineato a Tremor)
- "lento a caricare" (manca caching, vediamo `unstable_cache` o ISR)

## Deploy

1. push su GitHub
2. Vercel + env vars Supabase
3. configura caching: `export const revalidate = 60` nelle pagine per non ricalcolare ad ogni visita

Vedi `references/deploy-paths.md`.

## Punti di personalizzazione

**Facili:**
- aggiungere KPI: una nuova `KpiCard` con la sua query
- cambiare colori grafici: prop `colors` di Tremor
- aggiungere filtri: state nel componente + query parametrizzata
- export PDF/Excel: libreria client-side (jsPDF, xlsx)

**Rischiosi:**
- cambiare fonte dati (es. da Supabase a BigQuery): cambia `lib/queries.ts` ma anche struttura tipi
- aggiungere multi-tenancy (più clienti, ognuno vede solo i suoi): tocca RLS e filtri ovunque

## Estensioni tipiche

- alert via email quando una metrica supera soglia
- scheduled reports settimanali (Resend + cron Vercel)
- accesso multi-utente con ruoli → diventa CRUD + dashboard
