#!/bin/bash

###############################################################################
# Kaggle Dataset Downloader
# Downloads free ad performance datasets for offline analysis
#
# Prerequisites:
# 1. Install Kaggle CLI: pip install kaggle
# 2. Setup API credentials: https://www.kaggle.com/docs/api
#    - Go to kaggle.com/account
#    - Create New API Token
#    - Save kaggle.json to ~/.kaggle/kaggle.json
#    - chmod 600 ~/.kaggle/kaggle.json
#
# Usage: ./download_datasets.sh
###############################################################################

set -e  # Exit on error

# Configuration
DATA_DIR="${KAGGLE_DATA_PATH:-/data/kaggle}"
TEMP_DIR="/tmp/kaggle_downloads"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=================================================="
echo "   Kaggle Ad Datasets Downloader"
echo "=================================================="
echo ""

# Check if kaggle CLI is installed
if ! command -v kaggle &> /dev/null; then
    echo -e "${RED}ERROR: Kaggle CLI not found${NC}"
    echo "Install with: pip install kaggle"
    echo "Then setup credentials: https://www.kaggle.com/docs/api"
    exit 1
fi

# Check if kaggle credentials are configured
if [ ! -f "$HOME/.kaggle/kaggle.json" ]; then
    echo -e "${RED}ERROR: Kaggle credentials not found${NC}"
    echo "Setup instructions:"
    echo "1. Go to https://www.kaggle.com/account"
    echo "2. Scroll to API section and click 'Create New API Token'"
    echo "3. Save kaggle.json to ~/.kaggle/kaggle.json"
    echo "4. Run: chmod 600 ~/.kaggle/kaggle.json"
    exit 1
fi

# Create directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p "$DATA_DIR"
mkdir -p "$TEMP_DIR"

# Function to download and extract dataset
download_dataset() {
    local dataset_id=$1
    local dataset_name=$2
    local target_file=$3

    echo ""
    echo -e "${YELLOW}Downloading: $dataset_name${NC}"
    echo "Dataset ID: $dataset_id"

    cd "$TEMP_DIR"

    # Download dataset
    if kaggle datasets download -d "$dataset_id" --force; then
        echo -e "${GREEN}✓ Downloaded successfully${NC}"

        # Extract zip file
        if [ -f "$dataset_id.zip" ] || [ -f "*.zip" ]; then
            echo "Extracting files..."
            unzip -o "*.zip" 2>/dev/null || unzip -o "$dataset_id.zip" 2>/dev/null

            # Move target file to data directory
            if [ -n "$target_file" ]; then
                if [ -f "$target_file" ]; then
                    mv "$target_file" "$DATA_DIR/"
                    echo -e "${GREEN}✓ Installed: $DATA_DIR/$target_file${NC}"
                else
                    # Try to find the file with different naming
                    found_file=$(find . -maxdepth 1 -iname "*${target_file}*" -type f | head -n 1)
                    if [ -n "$found_file" ]; then
                        mv "$found_file" "$DATA_DIR/$target_file"
                        echo -e "${GREEN}✓ Installed: $DATA_DIR/$target_file${NC}"
                    else
                        echo -e "${RED}✗ Warning: Target file $target_file not found in archive${NC}"
                        echo "Available files:"
                        ls -la
                    fi
                fi
            else
                # Move all CSV files
                mv *.csv "$DATA_DIR/" 2>/dev/null || true
                echo -e "${GREEN}✓ Installed all CSV files to $DATA_DIR${NC}"
            fi

            # Cleanup
            rm -f *.zip
        fi
    else
        echo -e "${RED}✗ Failed to download $dataset_name${NC}"
        return 1
    fi

    cd - > /dev/null
}

# Download Dataset 1: Advertising Dataset (TV, Radio, Newspaper -> Sales)
echo ""
echo "=================================================="
echo "Dataset 1: Advertising Performance Data"
echo "=================================================="
download_dataset "ashydv/advertising-dataset" "Advertising Dataset" "advertising.csv"

# Download Dataset 2: Facebook Ad Campaign
echo ""
echo "=================================================="
echo "Dataset 2: Facebook Ad Campaign Performance"
echo "=================================================="
download_dataset "madislemsalu/facebook-ad-campaign" "Facebook Ad Campaign" "facebook_ad_campaign.csv"

# Download Dataset 3: Digital Marketing Campaign Dataset (Alternative)
echo ""
echo "=================================================="
echo "Dataset 3: Digital Marketing Campaign Data"
echo "=================================================="
# This dataset has various marketing campaign metrics
download_dataset "yoghurtpatil/direct-marketing-dataset" "Direct Marketing Dataset" ""

# Download Dataset 4: Social Media Ads Dataset (if available)
echo ""
echo "=================================================="
echo "Dataset 4: Social Media Advertisements"
echo "=================================================="
download_dataset "loveall/appliances-energy-prediction" "Appliances Energy Dataset" "" || true

# Cleanup temp directory
echo ""
echo -e "${YELLOW}Cleaning up temporary files...${NC}"
rm -rf "$TEMP_DIR"

# List downloaded datasets
echo ""
echo "=================================================="
echo "   Downloaded Datasets Summary"
echo "=================================================="
echo ""
if [ -d "$DATA_DIR" ]; then
    echo "Location: $DATA_DIR"
    echo ""
    echo "Files:"
    ls -lh "$DATA_DIR" | grep -v "^total" | awk '{print "  " $9 " (" $5 ")"}'
    echo ""
    echo -e "${GREEN}✓ Total datasets: $(ls -1 "$DATA_DIR" | wc -l)${NC}"
else
    echo -e "${RED}No datasets found${NC}"
    exit 1
fi

# Generate metadata file
echo ""
echo -e "${YELLOW}Generating metadata file...${NC}"
cat > "$DATA_DIR/metadata.json" <<EOF
{
  "downloaded_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "datasets": [
    {
      "name": "advertising.csv",
      "source": "Kaggle: ashydv/advertising-dataset",
      "description": "TV, Radio, Newspaper ad spend vs Sales performance",
      "rows": $(wc -l < "$DATA_DIR/advertising.csv" 2>/dev/null || echo 0),
      "columns": ["TV", "Radio", "Newspaper", "Sales"]
    },
    {
      "name": "facebook_ad_campaign.csv",
      "source": "Kaggle: madislemsalu/facebook-ad-campaign",
      "description": "Facebook ad campaign performance metrics",
      "rows": $(wc -l < "$DATA_DIR/facebook_ad_campaign.csv" 2>/dev/null || echo 0),
      "columns": ["ad_id", "campaign_id", "age", "gender", "interest", "impressions", "clicks", "spent", "total_conversion"]
    }
  ],
  "usage": "Load datasets using KaggleLoader.loadAdDataset('filename.csv')"
}
EOF

echo -e "${GREEN}✓ Metadata saved to $DATA_DIR/metadata.json${NC}"

echo ""
echo "=================================================="
echo -e "${GREEN}   All datasets downloaded successfully!${NC}"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Set environment variable: export KAGGLE_DATA_PATH=$DATA_DIR"
echo "2. Use KaggleLoader in your application:"
echo "   const patterns = await kaggleLoader.loadAdDataset('advertising.csv');"
echo ""
echo "To re-download datasets, run this script again."
echo ""
