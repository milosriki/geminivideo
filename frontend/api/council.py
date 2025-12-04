"""
AI Council API - Vercel Serverless Function
Handles AI model voting for ad script evaluation
"""
import os
import json
import hashlib
from http.server import BaseHTTPRequestHandler

# Try imports - Vercel will install these
try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None


def get_gemini_score(script: str, api_key: str) -> dict:
    """Get Gemini's evaluation of the ad script"""
    if not genai or not api_key:
        return {"score": 75, "confidence": 0.7, "feedback": "Gemini not configured"}

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""You are an expert ad creative director. Evaluate this ad script for Meta/Facebook ads.

SCRIPT:
{script}

Rate on a scale of 0-100 and provide brief feedback. Return JSON only:
{{"score": <number>, "confidence": <0-1>, "feedback": "<brief feedback>"}}"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith('```'):
            text = text.split('```')[1].replace('json', '').strip()
        return json.loads(text)
    except Exception as e:
        return {"score": 70, "confidence": 0.5, "feedback": str(e)}


def get_claude_score(script: str, api_key: str) -> dict:
    """Get Claude's evaluation of the ad script"""
    if not anthropic or not api_key:
        return {"score": 75, "confidence": 0.7, "feedback": "Claude not configured"}

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""You are an expert ad creative director. Evaluate this ad script for Meta/Facebook ads.

SCRIPT:
{script}

Rate on a scale of 0-100 and provide brief feedback. Return JSON only:
{{"score": <number>, "confidence": <0-1>, "feedback": "<brief feedback>"}}"""

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if text.startswith('```'):
            text = text.split('```')[1].replace('json', '').strip()
        return json.loads(text)
    except Exception as e:
        return {"score": 70, "confidence": 0.5, "feedback": str(e)}


def get_gpt_score(script: str, api_key: str) -> dict:
    """Get GPT-4o's evaluation of the ad script"""
    if not openai or not api_key:
        return {"score": 75, "confidence": 0.7, "feedback": "GPT not configured"}

    client = openai.OpenAI(api_key=api_key)

    prompt = f"""You are an expert ad creative director. Evaluate this ad script for Meta/Facebook ads.

SCRIPT:
{script}

Rate on a scale of 0-100 and provide brief feedback. Return JSON only:
{{"score": <number>, "confidence": <0-1>, "feedback": "<brief feedback>"}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        text = response.choices[0].message.content.strip()
        if text.startswith('```'):
            text = text.split('```')[1].replace('json', '').strip()
        return json.loads(text)
    except Exception as e:
        return {"score": 70, "confidence": 0.5, "feedback": str(e)}


def get_deepctr_score(script: str) -> dict:
    """Heuristic CTR prediction based on script features"""
    score = 50
    feedback = []

    # Hook analysis
    lines = script.split('\n')
    first_line = lines[0].lower() if lines else ""

    if any(word in first_line for word in ['stop', 'wait', 'attention', 'breaking']):
        score += 15
        feedback.append("Strong pattern interrupt hook")

    if '?' in first_line:
        score += 10
        feedback.append("Curiosity-driven opening")

    # Emotional triggers
    emotional_words = ['pain', 'struggle', 'finally', 'secret', 'proven', 'guaranteed', 'free']
    emotional_count = sum(1 for word in emotional_words if word in script.lower())
    score += min(emotional_count * 5, 15)
    if emotional_count > 2:
        feedback.append(f"Good emotional triggers ({emotional_count} found)")

    # CTA presence
    cta_words = ['click', 'sign up', 'get started', 'book', 'call', 'buy', 'join']
    if any(word in script.lower() for word in cta_words):
        score += 10
        feedback.append("Clear call-to-action")

    # Length check
    word_count = len(script.split())
    if 30 <= word_count <= 150:
        score += 5
        feedback.append("Optimal length for engagement")

    return {
        "score": min(score, 95),
        "confidence": 0.8,
        "feedback": "; ".join(feedback) if feedback else "Baseline analysis"
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

            script = data.get('script', '')

            if not script:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Script is required"}).encode())
                return

            # Get API keys from environment
            gemini_key = os.environ.get('GEMINI_API_KEY', '')
            openai_key = os.environ.get('OPENAI_API_KEY', '')
            anthropic_key = os.environ.get('ANTHROPIC_API_KEY', '')

            # Get scores from all models
            gemini_result = get_gemini_score(script, gemini_key)
            claude_result = get_claude_score(script, anthropic_key)
            gpt_result = get_gpt_score(script, openai_key)
            deepctr_result = get_deepctr_score(script)

            # Weighted average (Gemini 40%, Claude 30%, GPT 20%, DeepCTR 10%)
            weights = {
                'gemini': 0.40,
                'claude': 0.30,
                'gpt': 0.20,
                'deepctr': 0.10
            }

            final_score = (
                gemini_result['score'] * weights['gemini'] +
                claude_result['score'] * weights['claude'] +
                gpt_result['score'] * weights['gpt'] +
                deepctr_result['score'] * weights['deepctr']
            )

            avg_confidence = (
                gemini_result['confidence'] * weights['gemini'] +
                claude_result['confidence'] * weights['claude'] +
                gpt_result['confidence'] * weights['gpt'] +
                deepctr_result['confidence'] * weights['deepctr']
            )

            # Determine verdict
            if final_score >= 85:
                verdict = "STRONG_APPROVE"
                recommendation = "Excellent ad! Ready for production."
            elif final_score >= 70:
                verdict = "APPROVE"
                recommendation = "Good ad with minor improvements possible."
            elif final_score >= 55:
                verdict = "REVISE"
                recommendation = "Needs work. Consider strengthening the hook and CTA."
            else:
                verdict = "REJECT"
                recommendation = "Significant changes needed before deployment."

            response = {
                "council_score": round(final_score, 1),
                "confidence": round(avg_confidence, 2),
                "verdict": verdict,
                "recommendation": recommendation,
                "breakdown": {
                    "gemini": {
                        "weight": "40%",
                        "score": gemini_result['score'],
                        "confidence": gemini_result['confidence'],
                        "feedback": gemini_result['feedback']
                    },
                    "claude": {
                        "weight": "30%",
                        "score": claude_result['score'],
                        "confidence": claude_result['confidence'],
                        "feedback": claude_result['feedback']
                    },
                    "gpt4o": {
                        "weight": "20%",
                        "score": gpt_result['score'],
                        "confidence": gpt_result['confidence'],
                        "feedback": gpt_result['feedback']
                    },
                    "deepctr": {
                        "weight": "10%",
                        "score": deepctr_result['score'],
                        "confidence": deepctr_result['confidence'],
                        "feedback": deepctr_result['feedback']
                    }
                }
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
