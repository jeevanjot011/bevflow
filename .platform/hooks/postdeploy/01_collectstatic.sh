#!/bin/bash
set -e
echo "[postdeploy] Building Lambda package..."

# paths (adjust if your project layout differs)
APP_DIR="/var/app/current"
LAMBDA_SRC="$APP_DIR/bevflow/aws/lambda"
ZIP_OUT="/tmp/BevFlowOrderProcessor.zip"

cd "$LAMBDA_SRC"

# Create a clean build folder
BUILD_DIR=$(mktemp -d)
pip install -r requirements.txt -t "$BUILD_DIR" --upgrade
# copy handler
cp order_processor.py "$BUILD_DIR/"

# zip contents
cd "$BUILD_DIR"
zip -r "$ZIP_OUT" .
echo "[postdeploy] Lambda package created at $ZIP_OUT"
# keep $ZIP_OUT for next script
