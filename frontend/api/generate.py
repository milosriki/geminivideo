"""
Blueprint Generator API - Vercel Serverless Function
Generates ad scripts using Gemini
"""
import os
import json
from http.server import BaseHTTPRequestHandler

try:
    import google.generativeai as genai
except ImportError:
    genai = None


def generate_blueprint(product: str, target: str, pain_points: list, hook_type: str) -> dict:
    """Generate an ad blueprint using Gemini"""

    api_key = os.environ.get('GEMINI_API_KEY', '')

    if not genai or not api_key:
        return {
            "success": False,
            "error": "Gemini not configured"
        }

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')

    pain_text = ", ".join(pain_points) if pain_points else "general fitness struggles"

    prompt = f"""You are an expert direct-response copywriter specializing in fitness ads that convert.

Create a powerful video ad script for:
- Product: {product}
- Target Audience: {target}
- Pain Points: {pain_text}
- Hook Type: {hook_type}

Generate a script with these sections:
1. HOOK (first 3 seconds - pattern interrupt, {hook_type} style)
2. PROBLEM (agitate the pain)
3. SOLUTION (introduce the product)
4. PROOF (social proof/results)
5. CTA (clear call to action)

Return ONLY valid JSON:
{{
    "hook_text": "<the hook line>",
    "hook_type": "{hook_type}",
    "full_script": "<complete script>",
    "scenes": [
        {{"scene": 1, "duration": "0-3s", "text": "<hook>", "visual": "<what to show>"}},
        {{"scene": 2, "duration": "3-8s", "text": "<problem>", "visual": "<what to show>"}},
        {{"scene": 3, "duration": "8-15s", "text": "<solution>", "visual": "<what to show>"}},
        {{"scene": 4, "duration": "15-22s", "text": "<proof>", "visual": "<what to show>"}},
        {{"scene": 5, "duration": "22-30s", "text": "<cta>", "visual": "<what to show>"}}
    ],
    "estimated_duration": 30,
    "target_platform": "meta"
}}"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Clean up markdown if present
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
            text = text.strip()

        result = json.loads(text)
        result['success'] = True
        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)

            product = data.get('product', 'Fitness Coaching')
            target = data.get('target', 'People who want to get fit')
            pain_points = data.get('pain_points', ['lack of time', 'no motivation'])
            hook_type = data.get('hook_type', 'pattern_interrupt')

            result = generate_blueprint(product, target, pain_points, hook_type)

            status = 200 if result.get('success') else 500
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e), "success": False}).encode())
