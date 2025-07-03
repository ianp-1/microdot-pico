#!/bin/bash

# Build and Deploy Script for MicroPython Pico W
# 
# This script compiles Python files to .mpy bytecode for faster loading
# and smaller file sizes on the Pico W.
#
# Requirements:
#   - mpy-cross: Install with 'pip install mpy-cross' or download from
#     https://github.com/micropython/micropython/releases
#   - terser: Install with 'npm install -g terser'
#   - html-minifier-terser: Install with 'npm install -g html-minifier-terser'
#   - mpremote: Install with 'pip install mpremote'

SRC_DIR="/Users/ianpang/microdot-pico/src"
BUILD_DIR="/Users/ianpang/microdot-pico/build"
STATIC_SRC="$SRC_DIR/static"
STATIC_BUILD="$BUILD_DIR/static"
TEMPLATES_SRC="$SRC_DIR/templates"
TEMPLATES_BUILD="$BUILD_DIR/templates"
TAILWIND_BIN="$BUILD_DIR/tailwindcss"
TAILWIND_SRC="/Users/ianpang/Downloads/tailwindcss"

# Check for required tools
echo "🔍 Checking required tools..."
if ! command -v mpy-cross >/dev/null 2>&1; then
    echo "⚠️  Warning: mpy-cross not found!"
    echo "   Install with: pip install mpy-cross"
    echo "   Python files will be copied as .py instead of compiled to .mpy"
    echo ""
fi

if ! command -v terser >/dev/null 2>&1; then
    echo "❌ Error: terser not found!"
    echo "   Install with: npm install -g terser"
    exit 1
fi

if ! command -v html-minifier-terser >/dev/null 2>&1; then
    echo "❌ Error: html-minifier-terser not found!"
    echo "   Install with: npm install -g html-minifier-terser"
    exit 1
fi

if ! command -v mpremote >/dev/null 2>&1; then
    echo "❌ Error: mpremote not found!"
    echo "   Install with: pip install mpremote"
    exit 1
fi

echo "🧼 Cleaning build dir..."
rm -rf "$BUILD_DIR"
mkdir -p "$STATIC_BUILD" "$TEMPLATES_BUILD"

echo "📁 Copying static files and templates..."
cp -r "$STATIC_SRC/"* "$STATIC_BUILD/"
cp -r "$TEMPLATES_SRC/"* "$TEMPLATES_BUILD/"
cp "$SRC_DIR/wifi_config.json" "$BUILD_DIR/"

echo "🔧 Compiling Python files to .mpy..."
# Create directory structure in build
mkdir -p "$BUILD_DIR/lib" "$BUILD_DIR/model" "$BUILD_DIR/app"

# Function to compile .py files to .mpy
compile_py_files() {
    local src_dir="$1"
    local dest_dir="$2"
    
    find "$src_dir" -name "*.py" | while read -r py_file; do
        # Get relative path from source directory
        rel_path="${py_file#$src_dir/}"
        dest_file="$dest_dir/${rel_path%.py}.mpy"
        dest_dirname=$(dirname "$dest_file")
        
        # Create destination directory if it doesn't exist
        mkdir -p "$dest_dirname"
        
        # Compile to .mpy
        if command -v mpy-cross >/dev/null 2>&1; then
            echo "  Compiling: $rel_path -> ${rel_path%.py}.mpy"
            mpy-cross "$py_file" -o "$dest_file"
        else
            echo "  Warning: mpy-cross not found, copying .py file instead: $rel_path"
            cp "$py_file" "$dest_dirname/"
        fi
    done
    
    # Copy __init__.py files as they're needed for package structure
    find "$src_dir" -name "__init__.py" | while read -r init_file; do
        rel_path="${init_file#$src_dir/}"
        dest_file="$dest_dir/$rel_path"
        dest_dirname=$(dirname "$dest_file")
        mkdir -p "$dest_dirname"
        cp "$init_file" "$dest_file"
    done
}

# Compile all Python modules
compile_py_files "$SRC_DIR/lib" "$BUILD_DIR/lib"
compile_py_files "$SRC_DIR/model" "$BUILD_DIR/model"
compile_py_files "$SRC_DIR/app" "$BUILD_DIR/app"

# Handle main.py separately (entry point)
if command -v mpy-cross >/dev/null 2>&1; then
    echo "  Compiling: main.py -> main.mpy"
    mpy-cross "$SRC_DIR/main.py" -o "$BUILD_DIR/main.mpy"
else
    echo "  Warning: mpy-cross not found, copying main.py instead"
    cp "$SRC_DIR/main.py" "$BUILD_DIR/"
fi

# Step 2: Copy and use tailwind binary
cp "$TAILWIND_SRC" "$TAILWIND_BIN"
chmod +x "$TAILWIND_BIN"

echo "🎨 Building CSS..."
"$TAILWIND_BIN" -i "$STATIC_BUILD/styling/input.css" -o "$STATIC_BUILD/styling/output.css" --minify
rm -f "$TAILWIND_BIN"

# Step 3: Minify and compress all JS files in static/ and static/scripts/
echo "📦 Minifying and compressing JS..."
find "$STATIC_BUILD" -type f -name '*.js' | while read -r js; do
  min="${js%.js}.min.js"

  # Minify using terser
  terser "$js" -o "$min" -c -m

  # Compress the minified file with gzip
  gzip -f "$min"

  # Rename .min.js.gz to .js.gz (for Microdot serving compatibility)
  mv "${min}.gz" "${js}.gz"

  # Remove original files
  rm -f "$js" "$min"
done

# Step 4: Compress CSS with gzip
echo "🗜️ Compressing CSS..."
gzip -f "$STATIC_BUILD/styling/output.css"
rm -f "$STATIC_BUILD/styling/output.css" "$STATIC_BUILD/styling/input.css"

# Step 5: Minify + compress HTML
echo "📄 Minifying and compressing HTML..."
for html in "$TEMPLATES_BUILD/"*.html; do
  min="${html%.html}.min.html"
  html-minifier-terser "$html" \
    --collapse-whitespace \
    --remove-comments \
    --remove-redundant-attributes \
    --use-short-doctype \
    --remove-empty-attributes \
    --remove-optional-tags \
    --minify-js true \
    --minify-css true \
    --remove-attribute-quotes \
    --collapse-boolean-attributes \
    --sort-attributes \
    --sort-class-name \
    -o "$min"

  gzip -f "$min"
  rm -f "$html"
done

# Step 6: Upload to Pico W
echo "📡 Uploading optimized build to Pico W..."
mpremote connect tty.usbmodem* fs cp -r "$BUILD_DIR" :

echo "✅ Done! Project built with compiled .mpy files and uploaded to Pico W."
