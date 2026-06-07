#!/bin/bash
# Run with: source activate.sh
set +H
source .venv/Scripts/activate
set -a
source .env
set +a
export PYTHONPATH="${PWD}"
echo "✓ Virtual environment active"
echo "✓ SYNAPSE_SERVER = $SYNAPSE_SERVER"
echo "✓ PYTHONPATH = $PYTHONPATH"
