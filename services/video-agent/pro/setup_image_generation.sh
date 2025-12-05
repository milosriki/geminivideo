#!/bin/bash
# Setup script for AI Image Generation Service
# Agent 37: FLUX.1 / DALL-E 3 / Imagen 3 / SDXL Turbo

set -e

echo "=========================================="
echo "AI Image Generation Setup"
echo "Agent 37: Multi-Provider Image Generation"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "image_generator.py" ]; then
    echo "❌ Error: Run this script from /services/video-agent/pro/"
    exit 1
fi

echo "1. Checking dependencies..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi
echo "✅ Python 3 found"

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Please install pip"
    exit 1
fi
echo "✅ pip3 found"

echo ""
echo "2. Installing Python dependencies..."
echo ""

# Install requirements
pip3 install -r requirements_image_generation.txt

echo ""
echo "3. Checking API keys..."
echo ""

# Check OpenAI
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY not set (DALL-E 3 will not work)"
else
    echo "✅ OPENAI_API_KEY set"
fi

# Check Replicate
if [ -z "$REPLICATE_API_TOKEN" ]; then
    echo "⚠️  REPLICATE_API_TOKEN not set (FLUX.1/SDXL will not work)"
else
    echo "✅ REPLICATE_API_TOKEN set"
fi

# Check Together
if [ -z "$TOGETHER_API_KEY" ]; then
    echo "⚠️  TOGETHER_API_KEY not set (optional)"
else
    echo "✅ TOGETHER_API_KEY set"
fi

# Check Google Cloud
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo "⚠️  GOOGLE_CLOUD_PROJECT not set (Imagen 3 will not work)"
else
    echo "✅ GOOGLE_CLOUD_PROJECT set"
fi

echo ""
echo "4. Creating output directory..."
echo ""

OUTPUT_DIR="${IMAGE_OUTPUT_DIR:-/tmp/generated_images}"
mkdir -p "$OUTPUT_DIR"
echo "✅ Output directory: $OUTPUT_DIR"

echo ""
echo "5. Running test generation..."
echo ""

# Test if module imports work
python3 -c "
import sys
sys.path.append('.')
try:
    from image_generator import ImageGenerator, ImageProvider
    print('✅ ImageGenerator module loaded successfully')

    # Check available providers
    generator = ImageGenerator(output_dir='$OUTPUT_DIR')
    providers = generator.get_supported_providers()

    print(f'✅ Available providers: {len(providers)}')
    for provider in providers:
        print(f'   - {provider}')

    if len(providers) == 0:
        print('⚠️  No providers available. Set API keys.')
    else:
        print('✅ Image generation ready!')

except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Set missing API keys (see warnings above)"
echo "2. Run database migration:"
echo "   psql \$DATABASE_URL -f ../../gateway-api/prisma/migrations/00000_add_image_generations.sql"
echo ""
echo "3. Test image generation:"
echo "   python3 -c 'import asyncio; from image_generator import generate_product_image; asyncio.run(generate_product_image(\"test product\"))'"
echo ""
echo "4. Start the service:"
echo "   python3 image_generator.py"
echo ""
echo "API Endpoints will be available at:"
echo "  - POST /api/image/generate"
echo "  - POST /api/image/product-shot"
echo "  - POST /api/image/lifestyle"
echo "  - POST /api/image/thumbnail"
echo ""
echo "Documentation: IMAGE_GENERATION_README.md"
echo ""
echo "=========================================="
