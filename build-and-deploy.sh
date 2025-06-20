#!/bin/bash

SRC_DIR="/Users/ianpang/microdot-pico/src"
BUILD_DIR="/Users/ianpang/microdot-pico/build"
STATIC_SRC="$SRC_DIR/static"
STATIC_BUILD="$BUILD_DIR/static"
TEMPLATES_SRC="$SRC_DIR/templates"
TEMPLATES_BUILD="$BUILD_DIR/templates"
TAILWIND_BIN="$BUILD_DIR/tailwindcss"
TAILWIND_SRC="/Users/ianpang/Downloads/tailwindcss"

echo "🧼 Cleaning build dir..."
rm -rf "$BUILD_DIR"
mkdir -p "$STATIC_BUILD" "$TEMPLATES_BUILD"

echo "📁 Copying source files to build dir..."
cp -r "$STATIC_SRC/"* "$STATIC_BUILD/"
cp -r "$TEMPLATES_SRC/"* "$TEMPLATES_BUILD/"
cp -r "$SRC_DIR/lib" "$BUILD_DIR/"
cp -r "$SRC_DIR/model" "$BUILD_DIR/"
cp "$SRC_DIR/main.py" "$BUILD_DIR/"

# Step 2: Copy and use tailwind binary
cp "$TAILWIND_SRC" "$TAILWIND_BIN"
chmod +x "$TAILWIND_BIN"

echo "🎨 Building CSS..."
"$TAILWIND_BIN" -i "$STATIC_BUILD/input.css" -o "$STATIC_BUILD/output.css" --minify
rm -f "$TAILWIND_BIN"

# Step 3: Minify and gzip all JS files in static/ and static/scripts/
echo "📦 Minifying and gzipping JS..."
find "$STATIC_BUILD" -type f -name '*.js' | while read -r js; do
  min="${js%.js}.min.js"

  # Minify using terser
  terser "$js" -o "$min" -c -m

  # Gzip the minified file
  gzip -f "$min"

  # Rename .min.js.gz to .js.gz (for Microdot serving compatibility)
  mv "${min}.gz" "${js}.gz"

  # Remove original files
  rm -f "$js" "$min"
done

# Step 4: Gzip CSS
echo "🎀 Gzipping CSS..."
gzip -f "$STATIC_BUILD/output.css"
rm -f "$STATIC_BUILD/output.css" "$STATIC_BUILD/input.css"

# Step 5: Minify + gzip HTML
echo "📄 Minifying and gzipping HTML..."
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
echo "📡 Uploading entire build/ to Pico W..."
mpremote connect tty.usbmodem* fs cp -r "$BUILD_DIR" :

echo "✅ Done! Project built and uploaded from clean build directory."
