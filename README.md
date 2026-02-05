# FAQ Generator

Comprehensive local tool to scrape website text, call a large language model (Google Gemini) to produce a strict JSON of 5 FAQ Q/A pairs, and serve a small UI for interaction.

## What this project does
- Scrapes page text from a URL (via `web_app.py` or `web_scraper.py`) and saves it to `scraped_page.txt`.
- Sends the scraped text to a configured model (Gemini) and asks for EXACTLY 5 FAQs in a strict JSON format: a top-level `faqs` array with objects containing `question` and `answer` keys.
- Provides a minimal web UI served from `/static/index.html` that lets you enter a URL, call the backend, render the FAQs, view the scraped text, and download the JSON.
- Includes a small CLI/utility `faq_generator.py` to run the same pipeline from the terminal.

## Files of interest
- `web_app.py` — Flask backend. Routes:
  - `GET /` — serves the UI (if present) or a simple JSON message.
  - `GET /health` — returns `{ok, has_key, model}` for quick checks.
  - `GET /scraped` — returns `scraped_page.txt` when available.
  - `POST /generate` — accepts `{url}` or `{text}` and returns `{success, faqs}` or an error payload.
- `faq_generator.py` — CLI that reads a text file or scrapes a URL and requests the model to generate the 5 FAQs JSON.
- `static/index.html`, `static/app.js`, `static/style.css` — the single-page UI, now simplified: only the URL input is shown, a Generate button, a Download JSON button, and a link to the scraped text.
- `.env` — local environment file used by `web_app.py` for `GEMINI_API_KEY` / `GOOGLE_API_KEY` and `OPENAI_MODEL` (model name).

## Setup (Windows)
1. Create and activate a virtualenv (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your Gemini API key and preferred model. Example:

```
GEMINI_API_KEY=YOUR_KEY_HERE
OPENAI_MODEL=gemini-2.5-flash-lite
```

Note: `web_app.py` supports `GEMINI_API_KEY` or `GOOGLE_API_KEY`. If you set the variables in your shell instead of `.env`, the running process must be started from that shell so it inherits the env.

## Run the backend
Start the Flask backend (foreground to watch logs):

```powershell
.\.venv\Scripts\python.exe web_app.py
```

By default it attempts to bind to port `5000`, with a small fallback to `5001`, `5050`, `8000` if `5000` is occupied.

Visit the UI at: http://127.0.0.1:5000/static/index.html

Or call the endpoints directly with `curl`/fetch:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"url":"https://example.com"}' http://127.0.0.1:5000/generate
```

## How the prompt & output work
The backend builds a strict prompt instructing the model to RETURN ONLY JSON with a single top-level key `faqs` containing exactly five objects, each with `question` and `answer`. Example returned shape:

```json
{
  "faqs": [
    {"question": "...", "answer": "..."},
    ... (5 total)
  ]
}
```

If the model returns invalid JSON, the backend reports `success: false` and includes the raw model output for debugging.

## Frontend behavior
- Only the first input (URL) is presented now. The UI sends `{url}` to `POST /generate`.
- When the response is successful the UI renders the five FAQs and shows a `Download JSON` button which saves `faqs.json` locally.
- A `View scraped text` link appears when `scraped_page.txt` is saved on the server.

## Troubleshooting
- If you get `GEMINI_API_KEY ... is not set` from the server, confirm:
  - `.env` exists in the project root and contains `GEMINI_API_KEY` (no backticks or fences).
  - The server process was started after `.env` was created or that the shell has the env var exported.
- If the REST call returns a 404 for `models/...`, your API key may not have access to the requested model. Try changing `OPENAI_MODEL` in `.env` to a model available to your account or consult GCP IAM / Generative AI enablement.
- If port `5000` is already in use, either stop the existing process or connect to the fallback port printed in logs.

## Security notes
- `GEMINI_API_KEY` is sensitive — do not commit `.env` into source control.
- This project is for local dev/testing. If you deploy it publicly, secure the `/generate` endpoint with authentication and use proper secret management.

## Next steps & customization ideas
- Allow paste-text input in the UI again for manual content.
- Add rate-limiting, request queuing, and retries for robustness.
- Persist generated FAQs to a small DB or export multiple formats (CSV, Markdown).

## Support
If you want, I can:
- Start the server and verify the UI end-to-end.
- Add a CLI convenience command to launch the backend and open the UI in your browser.

---
Generated and maintained by the local development helper in this workspace.# FAQ Generator

This script scrapes a website with BeautifulSoup and asks OpenAI to return exactly 5 FAQs as JSON.

Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
# FAQ Generator

Small local tool that scrapes a web page (or accepts pasted page text) and uses a LLM to produce exactly 5 FAQ Q/A pairs as strict JSON.

Features
- Scrapes page text with BeautifulSoup
- Backend API (Flask) at `/generate` that accepts `url` or `text` and returns JSON
- Static frontend at `/static/index.html` that calls the backend
- Saves last scraped text to `scraped_page.txt` in the project root

Prerequisites
- Python 3.10+ and a virtual environment
- An API key for Google's Generative Language (set as `GEMINI_API_KEY` or `GOOGLE_API_KEY`)

Install
```powershell
& .\.venv\Scripts\python.exe -m pip install -r "c:\Users\azerty\Documents\faq generator\requirements.txt"
```

Environment
- Set the API key for the running process (PowerShell examples):
```powershell
$env:GEMINI_API_KEY = "YOUR_API_KEY"
# optional: override model
$env:OPENAI_MODEL = "gemini-2.5-flash-lite-preview"
```
To persist the key for your user:
```powershell
[Environment]::SetEnvironmentVariable("GEMINI_API_KEY","YOUR_API_KEY","User")
```

Run (backend)
```powershell
& .venv\Scripts\python.exe "c:\Users\azerty\Documents\faq generator\web_app.py"
```
This starts a development Flask server on `http://127.0.0.1:5000`.

Endpoints
- `POST /generate` — JSON or form body with `url` or `text` → returns `{ success: true, faqs: [...] }` or an error payload
- `GET /scraped` — download the last saved `scraped_page.txt`
- Static frontend: `http://127.0.0.1:5000/static/index.html`

Quick curl examples
```bash
# Send pasted text
curl -X POST -H "Content-Type: application/json" -d '{"text":"PASTE PAGE TEXT"}' http://127.0.0.1:5000/generate

# Ask by URL (server will scrape)
curl -X POST -F "url=https://example.com/page" http://127.0.0.1:5000/generate
```

CLI helper
- `faq_generator.py` prefers a text file input (`scraped_page.txt` or another .txt) and will send that content to the model; use that if you already have scraped content.

Security note
- Do not paste API keys into public logs or chat. Store keys in environment variables and keep them secret.

If you want a `/set_api_key` endpoint (server-side) to set the key without restarting, tell me and I can add it.
