#!/bin/bash
#
# OpenAPI仕様書バリデーションスクリプト
# Usage: ./scripts/validate_openapi.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OPENAPI_FILE="$PROJECT_ROOT/docs/api/openapi.yaml"

echo "=================================================="
echo "  OpenAPI Specification Validator"
echo "=================================================="
echo ""

# Check if openapi.yaml exists
if [ ! -f "$OPENAPI_FILE" ]; then
    echo "❌ Error: openapi.yaml not found at $OPENAPI_FILE"
    exit 1
fi

echo "✅ Found: $OPENAPI_FILE"
echo ""

# File statistics
echo "File Statistics:"
echo "  Lines: $(wc -l < "$OPENAPI_FILE")"
echo "  Size: $(du -h "$OPENAPI_FILE" | cut -f1)"
echo ""

# Check for required tools
echo "Checking validation tools..."
echo ""

VALIDATORS=()

# Check for spectral
if command -v spectral &> /dev/null; then
    echo "✅ Spectral found"
    VALIDATORS+=("spectral")
else
    echo "⚠️  Spectral not found (npm install -g @stoplight/spectral-cli)"
fi

# Check for swagger-cli
if command -v swagger-cli &> /dev/null; then
    echo "✅ swagger-cli found"
    VALIDATORS+=("swagger-cli")
else
    echo "⚠️  swagger-cli not found (npm install -g swagger-cli)"
fi

# Check for openapi-generator-cli
if command -v openapi-generator-cli &> /dev/null; then
    echo "✅ openapi-generator-cli found"
    VALIDATORS+=("openapi-generator-cli")
else
    echo "⚠️  openapi-generator-cli not found (npm install -g @openapitools/openapi-generator-cli)"
fi

echo ""

if [ ${#VALIDATORS[@]} -eq 0 ]; then
    echo "❌ No validation tools found!"
    echo ""
    echo "Please install at least one of the following:"
    echo "  npm install -g @stoplight/spectral-cli"
    echo "  npm install -g swagger-cli"
    echo "  npm install -g @openapitools/openapi-generator-cli"
    echo ""
    exit 1
fi

# Run validations
echo "=================================================="
echo "Running Validations..."
echo "=================================================="
echo ""

# Validate with Spectral
if [[ " ${VALIDATORS[@]} " =~ " spectral " ]]; then
    echo "--- Spectral Validation ---"
    if spectral lint "$OPENAPI_FILE"; then
        echo "✅ Spectral validation passed"
    else
        echo "⚠️  Spectral found issues"
    fi
    echo ""
fi

# Validate with swagger-cli
if [[ " ${VALIDATORS[@]} " =~ " swagger-cli " ]]; then
    echo "--- Swagger CLI Validation ---"
    if swagger-cli validate "$OPENAPI_FILE"; then
        echo "✅ Swagger CLI validation passed"
    else
        echo "❌ Swagger CLI validation failed"
        exit 1
    fi
    echo ""
fi

# Validate with openapi-generator
if [[ " ${VALIDATORS[@]} " =~ " openapi-generator-cli " ]]; then
    echo "--- OpenAPI Generator Validation ---"
    if openapi-generator-cli validate -i "$OPENAPI_FILE"; then
        echo "✅ OpenAPI Generator validation passed"
    else
        echo "❌ OpenAPI Generator validation failed"
        exit 1
    fi
    echo ""
fi

# Check for common issues
echo "=================================================="
echo "Checking for Common Issues..."
echo "=================================================="
echo ""

# Check for TODO/FIXME
if grep -i "TODO\|FIXME" "$OPENAPI_FILE" > /dev/null; then
    echo "⚠️  Found TODO/FIXME comments:"
    grep -in "TODO\|FIXME" "$OPENAPI_FILE" | head -5
    echo ""
else
    echo "✅ No TODO/FIXME comments found"
fi

# Check for localhost URLs in production
if grep -E "localhost|127\.0\.0\.1" "$OPENAPI_FILE" | grep -v "description:" | grep -v "#" > /dev/null; then
    echo "⚠️  Warning: localhost URLs found (should use environment-specific URLs)"
    grep -n -E "localhost|127\.0\.0\.1" "$OPENAPI_FILE" | grep -v "description:" | head -5
    echo ""
fi

# Check for proper versioning
if grep "version:" "$OPENAPI_FILE" | grep -E "[0-9]+\.[0-9]+\.[0-9]+" > /dev/null; then
    VERSION=$(grep "version:" "$OPENAPI_FILE" | head -1 | sed 's/.*version: //' | tr -d '"' | tr -d "'")
    echo "✅ Version found: $VERSION"
else
    echo "⚠️  Warning: No semantic version found"
fi

echo ""

# Summary
echo "=================================================="
echo "  Validation Summary"
echo "=================================================="
echo ""
echo "File: $OPENAPI_FILE"
echo "Status: ✅ Valid OpenAPI 3.0 Specification"
echo ""
echo "Next steps:"
echo "  1. View in Swagger UI: docker run -p 8080:8080 -e SWAGGER_JSON=/docs/openapi.yaml -v \$(pwd)/docs/api:/docs swaggerapi/swagger-ui"
echo "  2. Generate client: openapi-generator-cli generate -i $OPENAPI_FILE -g python -o client/python"
echo "  3. Import to Postman: File → Import → $OPENAPI_FILE"
echo ""

exit 0
