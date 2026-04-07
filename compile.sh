#!/bin/bash
# Compile the Fractal Intelligence paper.
# Optionally runs prototype analysis first if tree.json exists.
set -e

cd "$(dirname "$0")"

# Run prototype analysis if data exists
if [ -f prototype/tree.json ]; then
    echo "=== Running prototype analysis ==="
    python3 prototype/analyze.py
    echo ""
fi

# Compile paper
echo "=== Compiling paper ==="
pdflatex -interaction=nonstopmode fractal-intelligence.tex > /dev/null
bibtex fractal-intelligence > /dev/null 2>&1 || true
pdflatex -interaction=nonstopmode fractal-intelligence.tex > /dev/null
pdflatex -interaction=nonstopmode fractal-intelligence.tex > /dev/null

echo "Done. Output: fractal-intelligence.pdf"
