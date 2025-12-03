"""
Quick Score API - Fast single-model evaluation
Uses only Gemini for speed
"""
import os
import json
import re
from http.server import BaseHTTPRequestHandler

try:
    import google.generativeai as genai
except ImportError:
    genai = None


def clean_json_response(text):
    """Clean and extract JSON from model response"""
    text = text.strip()

    # Remove markdown code blocks
    if '```' in text:
        # Find content between ```json and ```
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if match:
            text = match.group(1).strip()

    # Try to find JSON object
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        text = match.group(0)

    return text


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

            script = data.get('script', '')

            if not script:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Script is required"}).encode())
                return

            api_key = os.environ.get('GEMINI_API_KEY', '')

            if not genai or not api_key:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Gemini not configured"}).encode())
                return

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')

            prompt = f"""Evaluate this ad script for Meta/Facebook ads on a scale of 0-100.

SCRIPT: {script}

Return ONLY a JSON object with these exact keys (no markdown, no explanation):
score (number 0-100)
verdict (one of: STRONG_APPROVE, APPROVE, REVISE, REJECT)
feedback (string with 1-2 sentences)
improvements (array of 2 short strings)"""

            response = model.generate_content(prompt)
            text = response.text

            # Clean the response
            cleaned = clean_json_response(text)

            try:
                result = json.loads(cleaned)
            except json.JSONDecodeError:
                # Fallback: create a basic response
                result = {
                    "score": 70,
                    "verdict": "REVISE",
                    "feedback": "Unable to parse AI response. Manual review recommended.",
                    "improvements": ["Add stronger hook", "Include clear CTA"],
                    "raw_response": text[:500]
                }

            result['model'] = 'gemini-1.5-flash'
            result['success'] = True

            self.send_response(200)
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
