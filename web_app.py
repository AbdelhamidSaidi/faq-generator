import os
import json
import requests
from flask import Flask, request, jsonify, send_from_directory
from bs4 import BeautifulSoup


DEFAULT_MODEL = 'gemini-2.5-flash-lite'


def load_env_file(path: str) -> None:
    """Load KEY=VALUE lines from a .env-like file into os.environ.

    Also supports a single bare token (treated as GEMINI_API_KEY).
    """
    full_path = os.path.join(os.getcwd(), path)
    if not os.path.exists(full_path):
        return

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f if l.strip() and not l.strip().startswith('#')]
    except Exception:
        return

    if not lines:
        return

    handled_any = False
    for line in lines:
        if '=' not in line:
            continue
        key, val = line.split('=', 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and os.getenv(key) is None:
            os.environ[key] = val
        handled_any = True

    if not handled_any:
        first = lines[0].strip().strip('"').strip("'")
        if first and os.getenv('GEMINI_API_KEY') is None and os.getenv('GOOGLE_API_KEY') is None:
            os.environ['GEMINI_API_KEY'] = first


def refresh_env() -> None:
    # Backwards compat + current
    load_env_file('api.env')
    load_env_file('.env')


def get_api_key() -> str | None:
    refresh_env()
    return os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')


def get_model_name() -> str:
    refresh_env()
    return os.getenv('OPENAI_MODEL', DEFAULT_MODEL)


def scrape_text(url: str, max_chars: int = 25000) -> str:
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    text = soup.get_text(separator=' ', strip=True)
    text = ' '.join(text.split())
    return text[:max_chars]


def build_prompt(url: str, page_text: str) -> str:
    return (
        "You are given a website URL and the site's scraped text. "
        "Produce EXACTLY valid JSON with a single top-level key `faqs` which is an array of exactly 5 objects. "
        "Each object must have the keys `question` and `answer`. "
        "Answers must be concise and based only on the provided text. Do not add commentary, analysis, or any extra keys. "
        "Return only the JSON object and nothing else. "
        "Return only JSON (no markdown/backticks).\n\n"
        f"URL:\n{url}\n\nPAGE_TEXT:\n{page_text}\n"
    )


def _extract_text_from_generate_content(response_json: dict) -> str:
    candidates = response_json.get('candidates') or []
    if not candidates:
        return json.dumps(response_json)
    content = candidates[0].get('content') or {}
    parts = content.get('parts') or []
    texts: list[str] = []
    for p in parts:
        t = p.get('text')
        if isinstance(t, str):
            texts.append(t)
    return ''.join(texts) if texts else json.dumps(response_json)


def call_gemini_rest(api_key: str, model: str, prompt: str) -> str:
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}'
    body = {
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': {'temperature': 0.0, 'maxOutputTokens': 1024},
    }
    r = requests.post(url, json=body, timeout=60)
    if not r.ok:
        raise RuntimeError(f'{r.status_code} {r.reason}: {r.text}')
    return _extract_text_from_generate_content(r.json())


def call_gemini(prompt: str) -> str:
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError('GEMINI_API_KEY (or GOOGLE_API_KEY) is not set')
    model = get_model_name()

    # Prefer the official SDK if available; fallback to REST.
    try:
        from google import genai  # type: ignore

        if hasattr(genai, 'configure'):
            genai.configure(api_key=api_key)
            client = genai.Client()
        else:
            try:
                client = genai.Client(api_key=api_key)
            except TypeError:
                client = genai.Client()

        resp = client.models.generate_content(model=model, contents=prompt)
        text = getattr(resp, 'text', None)
        if isinstance(text, str) and text.strip():
            return text
        return json.dumps(resp, default=str)
    except Exception:
        return call_gemini_rest(api_key, model, prompt)


app = Flask(__name__, static_folder='static', static_url_path='/static')


@app.route('/')
def index():
    index_path = os.path.join(app.static_folder, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(app.static_folder, 'index.html')
    return jsonify({'success': True, 'message': 'Backend running. Open /static/index.html for UI.'})


@app.route('/health')
def health():
    return jsonify({'ok': True, 'has_key': bool(get_api_key()), 'model': get_model_name()})


@app.route('/scraped')
def scraped():
    path = os.path.join(os.getcwd(), 'scraped_page.txt')
    if os.path.exists(path):
        return send_from_directory(os.getcwd(), 'scraped_page.txt')
    return ('', 404)


@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json(silent=True) or {}
    page_text = data.get('text') or request.form.get('text')
    url = data.get('url') or request.form.get('url')

    try:
        if not page_text and url:
            page_text = scrape_text(url)
        if not page_text:
            return jsonify({'success': False, 'error': 'Provide `url` or `text`.'}), 400

        try:
            with open(os.path.join(os.getcwd(), 'scraped_page.txt'), 'w', encoding='utf-8') as f:
                f.write(page_text)
        except Exception:
            pass

        prompt = build_prompt(url or 'pasted_text', page_text)
        out = call_gemini(prompt)

        try:
            parsed = json.loads(out)
            return jsonify({'success': True, 'faqs': parsed.get('faqs', parsed)}), 200
        except Exception:
            return jsonify({'success': False, 'error': 'Model output was not valid JSON', 'raw': out}), 502

    except Exception as e:
        msg = str(e)
        if '404' in msg and 'models/' in msg:
            msg += ' (Model not found for this API key. Try setting OPENAI_MODEL to a model available to your key.)'
        return jsonify({'success': False, 'error': msg}), 502


if __name__ == '__main__':
    import socket

    def pick_port(preferred: int) -> int:
        for candidate in (preferred, 5001, 5050, 8000):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('127.0.0.1', candidate))
                s.close()
                return candidate
            except OSError:
                try:
                    s.close()
                except Exception:
                    pass
        return preferred

    preferred_port = int(os.getenv('PORT', '5000'))
    port = pick_port(preferred_port)
    app.run(host='127.0.0.1', port=port, debug=False)
