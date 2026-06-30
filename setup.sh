#!/usr/bin/env bash
# setup.sh — creates a Python 3.11 virtual environment and installs deps.
# Run with:  bash setup.sh

set -e

echo "🔍 Looking for Python 3.11 or 3.12..."

PYBIN=""
for candidate in python3.11 python3.12 python3.10; do
    if command -v "$candidate" &> /dev/null; then
        PYBIN="$candidate"
        break
    fi
done

if [ -z "$PYBIN" ]; then
    echo "❌ No compatible Python found (need 3.10, 3.11, or 3.12)."
    echo ""
    echo "Install Python 3.11 with:"
    echo "  macOS:   brew install python@3.11"
    echo "  Linux:   sudo apt install python3.11 python3.11-venv"
    echo "  Windows: https://www.python.org/downloads/release/python-3119/"
    exit 1
fi

echo "✅ Using $PYBIN ($($PYBIN --version))"

$PYBIN -m venv venv
echo "✅ Virtual environment created"

source venv/bin/activate 2>/dev/null || venv\\Scripts\\activate

pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ All dependencies installed!"
echo ""
echo "Next steps:"
echo "  1. Place superstore.csv in the data/ folder"
echo "  2. Run:  python data_cleaning.py"
echo "  3. Run:  streamlit run app.py"
