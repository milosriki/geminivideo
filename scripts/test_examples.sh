#!/bin/bash
# Example curl commands for testing the AI Ad Intelligence Suite

GATEWAY_URL="${GATEWAY_URL:-http://localhost:8080}"

echo "📝 Example API Test Commands"
echo "=============================="
echo ""

echo "1. Check Gateway health:"
echo "curl $GATEWAY_URL/health | jq ."
echo ""

echo "2. Get all assets:"
echo "curl $GATEWAY_URL/assets | jq ."
echo ""

echo "3. Ingest local videos:"
echo "curl -X POST $GATEWAY_URL/assets/ingest/local \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"folderPath\": \"/app/data/cache\"}' | jq ."
echo ""

echo "4. Get ranked clips for an asset:"
echo "curl '$GATEWAY_URL/assets/{ASSET_ID}/clips?ranked=true&top=5' | jq ."
echo ""

echo "5. Search clips:"
echo "curl -X POST $GATEWAY_URL/assets/search/clips \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"q\": \"person\", \"topK\": 10}' | jq ."
echo ""

echo "6. Score clips for prediction:"
echo "curl -X POST $GATEWAY_URL/predict/score \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"clips\": [{\"objects\": [\"person\"], \"ocr_tokens\": [\"free\"], \"motion_score\": 0.7}]}' | jq ."
echo ""

echo "7. Create a render job:"
echo "curl -X POST $GATEWAY_URL/render/remix \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"clips\": [{\"videoPath\": \"/app/data/cache/video.mp4\", \"start\": 0, \"duration\": 5}], \"variant\": \"reels\"}' | jq ."
echo ""

echo "8. Get job status:"
echo "curl $GATEWAY_URL/render/jobs/{JOB_ID} | jq ."
echo ""

echo "9. Get reliability stats:"
echo "curl $GATEWAY_URL/predict/reliability | jq ."
echo ""

echo "10. Publish to Meta (dry-run):"
echo "curl -X POST $GATEWAY_URL/../publish/meta \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"videoUrl\": \"https://example.com/video.mp4\", \"pageId\": \"123\"}' | jq ."
echo ""

echo "To run these commands, replace {ASSET_ID} and {JOB_ID} with actual values."
