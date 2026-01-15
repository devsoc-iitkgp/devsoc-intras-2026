#!/bin/bash

# Modal Llama Deployment Script
# This script helps deploy the Llama models to Modal

set -e

echo "=========================================="
echo "Modal Llama Deployment Script"
echo "=========================================="
echo ""

# Check if modal is installed
if ! command -v modal &> /dev/null; then
    echo "❌ Modal CLI not found. Installing..."
    pip install modal
else
    echo "✅ Modal CLI found"
fi

# Check if modal is authenticated
if ! modal token check &> /dev/null; then
    echo "❌ Modal not authenticated. Please authenticate:"
    modal token new
else
    echo "✅ Modal authenticated"
fi

echo ""
echo "=========================================="
echo "Deploying Modal App"
echo "=========================================="
echo ""

echo "ℹ️  Note: Using transformers pipeline - no HuggingFace token required!"
echo "   Models will be downloaded automatically from HuggingFace public repo"
echo ""

# Deploy the Modal app
echo "Deploying Llama models to Modal..."
modal deploy src/utils/modal_llama.py

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""

# Extract the Modal URL from deployment output
echo "To get your Modal URL, run:"
echo "  modal app list"
echo ""
echo "Look for: metakgp-llama"
echo ""
echo "The URL will be something like:"
echo "  https://your-workspace--metakgp-llama-fastapi-app.modal.run"
echo ""
echo "Add this URL to your .env file:"
echo "  MODAL_LLAMA_URL=https://your-workspace--metakgp-llama-fastapi-app.modal.run"
echo ""
echo "Then test the health endpoint:"
echo "  curl https://your-workspace--metakgp-llama-fastapi-app.modal.run/health"
echo ""
