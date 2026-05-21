#!/usr/bin/env bash
# Deploy a Railway (production).
# Prerequisiti: `npm i -g @railway/cli` + `railway login` + `railway link` al progetto una sola volta.
# Eseguire dalla root del progetto.

set -e

if ! command -v railway >/dev/null 2>&1; then
    echo "ERRORE: Railway CLI non trovata. Installa con: npm i -g @railway/cli"
    exit 1
fi

echo "Deploy a Railway..."
railway up

echo "Done. Stato del servizio nella dashboard Railway."
