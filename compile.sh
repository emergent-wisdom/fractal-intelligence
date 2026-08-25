#!/bin/bash
# Compile the Fractal Intelligence paper.
set -e

cd "$(dirname "$0")"

# Compile paper
echo "=== Compiling paper ==="
pdflatex -interaction=nonstopmode fractal-intelligence.tex > /dev/null
bibtex fractal-intelligence > /dev/null 2>&1 || true
pdflatex -interaction=nonstopmode fractal-intelligence.tex > /dev/null
pdflatex -interaction=nonstopmode fractal-intelligence.tex > /dev/null

echo "Done. Output: fractal-intelligence.pdf"
