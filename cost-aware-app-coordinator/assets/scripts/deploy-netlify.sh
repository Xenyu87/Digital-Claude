#!/usr/bin/env bash
# Deploy a Netlify (production).
# Prerequisiti: `npm i -g netlify-cli` + `netlify login` una sola volta.
# Eseguire dalla root del progetto.

set -e

if ! command -v netlify >/dev/null 2>&1; then
    echo "ERRORE: Netlify CLI non trovata. Installa con: npm i -g netlify-cli"
    exit 1
fi

echo "Build di prova in locale..."
npm run build

echo "Deploy a Netlify (production)..."
netlify deploy --prod

echo "Done. URL stampato sopra."
