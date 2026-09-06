#!/bin/bash
# ==============================================================================
# CIVIX 2.0 — Oracle Cloud Infrastructure (OCI) Deployment Script
# ==============================================================================
# This script automates system dependencies, firewall rules, Docker Compose
# orchestration, and database seeding on an Oracle Cloud Compute VM.
# ==============================================================================

set -e

echo "🚀 [CIVIX 2.0] Starting Oracle Cloud Infrastructure (OCI) Automated Deployment..."

# 1. Update OS & Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "📦 [1/5] Installing Docker & Docker Compose..."
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg lsb-release iptables ufw
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo usermod -aG docker $USER
    echo "✅ Docker installed successfully."
else
    echo "✅ Docker is already installed."
fi

# 2. Configure Host Firewall (OCI OS iptables/ufw default rule update)
echo "🔒 [2/5] Opening Host Firewall Ports (80, 443, 8000)..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 8000/tcp
    sudo ufw allow 7687/tcp
fi

# Oracle Cloud Ubuntu images have strict iptables rules by default.
# Open inbound traffic for ports 80, 443, and 8000.
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT || true
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT || true
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT || true
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 7687 -j ACCEPT || true

if command -v netfilter-persistent &> /dev/null; then
    sudo netfilter-persistent save || true
fi
echo "✅ Firewall rules configured."

# 3. Pull latest changes from Git
echo "📥 [3/5] Syncing latest Git repository main branch..."
git pull origin main || echo "⚠️ Git pull skipped or working from local archive."

# 4. Launch Docker Compose Stack
echo "🐳 [4/5] Building and launching CIVIX 2.0 Docker stack..."
docker compose down --remove-orphans || true
docker compose up --build -d

# Wait for Postgres & Neo4j containers to pass health checks
echo "⏳ Waiting for PostgreSQL and Neo4j databases to initialize..."
sleep 15

# 5. Execute Automated Database Seeding & Access Setup Pipeline
echo "🌱 [5/5] Executing 12-Case Golden Universe Seeding Pipeline..."
docker exec -it civix_backend python database/seed_12case_universe.py
docker exec -it civix_backend python database/generate_all_visuals_fast.py
docker exec -it civix_backend python scratch/grant_all_case_access.py
docker exec -it civix_backend python scratch/cleanup_and_pin_cases.py

echo ""
echo "=========================================================================="
echo "      🎉 CIVIX 2.0 ORACLE CLOUD DEPLOYMENT COMPLETED SUCCESSFULLY!        "
echo "=========================================================================="
echo "  Frontend URL : http://$(curl -s ifconfig.me)"
echo "  API Docs URL : http://$(curl -s ifconfig.me):8000/docs"
echo "  Investigator : vikram.singh@civix.gov.in (Password: demo123)"
echo "=========================================================================="
