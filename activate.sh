#!/bin/bash
# Run with: source activate.sh
# Required at the start of every new Git Bash terminal session

# Disable bash history expansion — required when .env contains ! characters
set +H

# Activate Python virtual environment
source .venv/Scripts/activate
set -a
source .env
set +a

# Export PYTHONPATH so all scripts can import from src/
# Without this, 'from src.features.build_features import ...' fails
export PYTHONPATH="${PWD}"

echo "✓ Virtual environment active"
echo "✓ Environment variables loaded"
echo "✓ PYTHONPATH = $PYTHONPATH"
echo "✓ SYNAPSE_SERVER = $SYNAPSE_SERVER"
echo "✓ PYTHONPATH = $PYTHONPATH"
