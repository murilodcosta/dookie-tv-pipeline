#!/bin/bash
# Oracle VPS (Ubuntu ARM64) Initial Setup Script for Dookie TV Pipeline
# Run this script via SSH on a fresh Ubuntu instance:
#   curl -sSL https://raw.githubusercontent.com/.../scripts/setup_vps.sh | bash
# or copy & execute locally on the VPS.

set -e

echo "🚀 [1/4] Updating system packages..."
sudo apt update && sudo apt upgrade -y

echo "📦 [2/4] Installing system prerequisites & FFmpeg..."
sudo apt install -y ca-certificates curl gnupg lsb-release git ffmpeg htop

echo "🐳 [3/4] Installing Docker & Docker Compose Plugin..."
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

echo "👤 [4/4] Adding current user ($USER) to docker group..."
sudo usermod -aG docker $USER

echo ""
echo "✅ VPS Setup completed successfully!"
echo "⚠️ Please log out and back in via SSH for docker group changes to take effect."
