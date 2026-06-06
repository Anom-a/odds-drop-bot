#!/bin/bash
set -e

# Ensure script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (e.g. sudo bash deploy.sh)"
  exit 1
fi

echo "Updating apt and installing dependencies..."
apt-get update
apt-get install -y python3 python3-venv python3-pip

echo "Creating /opt/odds-drop-bot directory..."
mkdir -p /opt/odds-drop-bot

echo "Creating virtualenv at /opt/odds-drop-bot/venv..."
python3 -m venv /opt/odds-drop-bot/venv

echo "Copying application files..."
cp *.py requirements.txt /opt/odds-drop-bot/

echo "Installing requirements..."
/opt/odds-drop-bot/venv/bin/pip install -r /opt/odds-drop-bot/requirements.txt

echo "Copying .env file to /opt/odds-drop-bot/.env..."
cp .env /opt/odds-drop-bot/.env
chmod 600 /opt/odds-drop-bot/.env

echo "Creating log directory at /var/log/odds-bot/..."
mkdir -p /var/log/odds-bot/
chmod 755 /var/log/odds-bot/

echo "Setting permissions for 'ubuntu' user..."
chown -R ubuntu:ubuntu /opt/odds-drop-bot
chown -R ubuntu:ubuntu /var/log/odds-bot/

echo "Deployment script completed!"
