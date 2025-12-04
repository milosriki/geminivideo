#!/usr/bin/env python3
"""
Script to add cost tracking to AI endpoints in index.ts
"""

import re

# Read the file
with open('src/index.ts', 'r') as f:
    content = f.read()

# 1. Modify /api/analyze endpoint
analyze_pattern = r"(console\.log\(`Analyzing video with Gemini: \$\{video_uri\}`\);)\s+// Call Gemini Vision API for real analysis\s+const result = await model\.generateContent\(\{\s+contents: \[\{\s+role: 'user',\s+parts: \[\{\s+text: `([^`]+)`"

analyze_replacement = r"""\1

    const promptText = `\2`;

    // Call Gemini Vision API for real analysis
    const result = await model.generateContent({
      contents: [{
        role: 'user',
        parts: [{
          text: promptText"""

content = re.sub(analyze_pattern, analyze_replacement, content)

# 2. Add cost tracking before res.json(analysis) in /api/analyze
analyze_cost_pattern = r"(console\.log\(`Gemini analysis completed for \$\{video_uri\}`\);)\s+(res\.json\(analysis\);)"

analyze_cost_replacement = r"""\1

    // Record cost (estimate tokens: ~4 chars per token)
    const latency = Date.now() - startTime;
    const estimatedInputTokens = Math.ceil(promptText.length / 4);
    const estimatedOutputTokens = Math.ceil(analysisText.length / 4);
    const totalTokens = estimatedInputTokens + estimatedOutputTokens;

    await costTracker.recordCost(
      'gemini-2.0-flash-exp',
      totalTokens,
      latency,
      'analysis',
      {
        inputTokens: estimatedInputTokens,
        outputTokens: estimatedOutputTokens
      }
    );

    \2"""

content = re.sub(analyze_cost_pattern, analyze_cost_replacement, content)

# 3. Add cost tracking to /api/insights/ai endpoint
insights_cost_pattern = r"(const insights = JSON\.parse\(result\.response\.text\(\)\);)\s+(res\.json\(\{)"

insights_cost_replacement = r"""\1

    // Record cost
    const latency = Date.now() - startTime;
    const estimatedTokens = Math.ceil((prompt.length + result.response.text().length) / 4);
    await costTracker.recordCost(
      'gemini-2.0-flash-exp',
      estimatedTokens,
      latency,
      'insights'
    );

    \2"""

# Check if insights endpoint has startTime
if "app.get('/api/insights/ai'," in content:
    # Add startTime if not present
    insights_start_pattern = r"(app\.get\('/api/insights/ai', async \(req: Request, res: Response\) => \{)\s+(try \{)"
    if re.search(insights_start_pattern, content):
        insights_start_replacement = r"\1\n  const startTime = Date.now();\n  \2"
        content = re.sub(insights_start_pattern, insights_start_replacement, content)

content = re.sub(insights_cost_pattern, insights_cost_replacement, content)

# Write the modified content
with open('src/index.ts', 'w') as f:
    f.write(content)

print("✅ Cost tracking added to AI endpoints")
print("   - /api/analyze")
print("   - /api/insights/ai")
