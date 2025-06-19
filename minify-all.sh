#!/bin/bash

JS_FILES=(
  "static/theme-change.js"
  "static/chart.js"
  "static/daisyui.js"
  "static/daisyui-theme.js"
)

CSS_FILES=(
  "static/output.css"
)

# Minify and gzip JS files
for file in "${JS_FILES[@]}"; do
  min="${file%.js}.min.js"
  echo "Minifying $file → $min"
  terser "$file" -o "$min" -c -m
  gzip -k "$min"
done

# Just gzip CSS files
for file in "${CSS_FILES[@]}"; do
  echo "Gzipping $file"
  gzip -k "$file"
done

echo "✅ All files processed and gzipped."
