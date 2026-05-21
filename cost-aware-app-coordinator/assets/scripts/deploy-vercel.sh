#!/usr/bin/env bash
# Deploy a Vercel (production).
# Prerequisiti: `npm i -g vercel` + `vercel login` una sola volta.
# Eseguire dalla root del progetto.

set -e

if ! command -v vercel >/dev/null 2>&1; then
    echo "ERRORE: Vercel CLI non trovata. Installa con: npm i -g vercel"
    exit 1
fi

echo "Build di prova in locale..."
npm run build

echo "Deploy a Vercel (production)..."
vercel --prod

echo "Done. URL stampato sopra."
