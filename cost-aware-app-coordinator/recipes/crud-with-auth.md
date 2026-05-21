# Ricetta: CRUD con auth (admin tool)

## Cosa fa

Strumento dove tu (e altri utenti autorizzati) fate login e gestite dei dati: lista, crea, modifica, elimina. Tipico per gestionali interni, admin di un'app, registri.

## Stack scelto e perché

- **Next.js 14 (App Router)** — pagine + API in unico progetto.
- **Supabase** — fa **3 cose insieme** senza che tu gestisca un server:
  - database PostgreSQL
  - autenticazione (login email/password, Google, ecc.)
  - sicurezza a livello di righe ("Row Level Security": chi vede cosa)
- **Tailwind CSS + shadcn/ui** — componenti già fatti (tabelle, form, modal) da copiare.
- **Vercel** per hosting frontend.

## Costo mensile stimato

- Vercel: 0€ tier free
- Supabase: 0€ fino a 500 MB DB e 50.000 utenti attivi/mese (più che sufficiente per uso interno)
- Dominio: ~10€/anno opzionale

**Totale**: 0€/mese fino a soglie alte. Pro: $25/mese se diventa serio.

## Struttura iniziale

```
src/
├── app/
│   ├── page.tsx                  # redirect a /login o /dashboard
│   ├── login/page.tsx
│   ├── dashboard/
│   │   ├── page.tsx              # lista record
│   │   ├── new/page.tsx          # form crea
│   │   └── [id]/page.tsx         # modifica/elimina
│   └── api/                      # opzionale (Supabase fa quasi tutto da client)
├── components/ui/                # shadcn/ui (button, input, table)
├── lib/supabase.ts               # client Supabase
└── middleware.ts                 # protezione rotte
```

## Primi passi

1. `npx create-next-app@latest mio-admin --typescript --tailwind --app`
2. crea progetto su [supabase.com](https://supabase.com), copia URL e anon key in `.env.local`
3. `npm install @supabase/supabase-js @supabase/ssr`
4. nello SQL Editor di Supabase, crea la tabella (es. `clienti`) e abilita Row Level Security
5. `npx shadcn@latest init` poi `npx shadcn@latest add button input table card`
6. `npm run dev`

Risultato dopo ~2 ore: app locale con login funzionante e una tabella di base navigabile.

## Come testare in browser

1. registrati con un'email
2. login → ti porta al dashboard
3. crea un record nuovo → controllа in Supabase (Table Editor) che sia stato salvato
4. modifica → salva → ricarica pagina, è cambiato?
5. logout → la pagina dashboard ti deve respingere a /login

**Se qualcosa non torna, segnalami:**
- "fa login ma poi mi rimanda subito a login" (problema sessione)
- "vedo i dati ma non riesco a modificarli" (probabile problema RLS)
- "errore 401/403" (permessi sbagliati a livello DB)

## Deploy

1. push su GitHub
2. Vercel "Import Git Repository"
3. Environment Variables: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
4. Deploy

Vedi `references/deploy-paths.md` per script automatici.

## Punti di personalizzazione

**Facili:**
- aggiungere campi alla tabella (Supabase Table Editor → Add column)
- aggiungere nuove tabelle: copia il pattern dashboard per ognuna
- cambiare grafica: shadcn/ui ha temi
- aggiungere ruoli (admin/editor/viewer): campo `role` nel profilo + RLS che lo rispetta

**Rischiosi (chiedimi prima):**
- modifiche allo schema con dati già in produzione (richiede migrazione)
- cambiare provider auth (es. da Supabase Auth a Clerk)
- aggiungere pagamenti (Stripe) — diventa CRUD + billing, scope diverso

## Estensioni tipiche

- export CSV: 1 endpoint
- audit log: tabella `events` con trigger Postgres
- ricerca/filtri: Supabase ha full-text search built-in
- file upload (foto, PDF): Supabase Storage
