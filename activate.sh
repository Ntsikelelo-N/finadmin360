#!/bin/bash
# Run this script every time you open a new terminal for this project:
#   source activate.sh

# Activate Python virtual environment
source .venv/Scripts/activate

# Load all .env variables into the shell session
set -a
source .env
set +a

echo "✓ Virtual environment active"
echo "✓ Environment variables loaded"
echo "✓ SYNAPSE_SERVER = $SYNAPSE_SERVER"
