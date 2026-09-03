#!/usr/bin/env bash

set -e

echo "=========================================================================="
echo "          CIVIX 2.0 — AUTOMATED CLOUD PROTOTYPE DEPLOYMENT"
echo "=========================================================================="

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed. Please install Docker & Docker Compose first."
    exit 1
fi

echo "[1/4] Building and launching production Docker containers..."
docker compose up -d --build

echo "[2/4] Waiting for PostgreSQL & Neo4j database initialization (15s)..."
sleep 15

echo "[3/4] Seeding 25 Delhi NCR CCTV cameras & demo world datasets..."
docker exec -i civix_backend python scratch/seed_25_cctv_cameras.py || true

echo "[4/4] Verifying health checks..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ || echo "500")

if [ "$HEALTH_STATUS" -eq 200 ]; then
    echo "=========================================================================="
    echo "  [SUCCESS] CIVIX 2.0 IS LIVE & RUNNING ON PORT 80!"
    echo "=========================================================================="
else
    echo "WARNING: Nginx returned HTTP $HEALTH_STATUS. Checking container logs..."
    docker compose logs --tail=20
fi
