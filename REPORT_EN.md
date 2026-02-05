# FAQ Generator — University-Style Project Report (English)

**Project title:** FAQ Generator from Web Content (Scrape → LLM → Strict JSON)

**Date:** 2026-02-05

**Authors:** _[Your Name]_  
**Course / Module:** _[Course Name]_  
**Supervisor:** _[Supervisor Name]_  
**Institution:** _[University Name]_  

---

## Abstract
This project implements a local toolchain that converts a public webpage into a structured FAQ dataset. The system (1) scrapes readable text from a URL, (2) prompts a Large Language Model (Google Gemini) to generate **exactly five** question/answer pairs grounded in the scraped content, and (3) returns the result as **strict JSON** suitable for storage and downstream use (websites, support bots, knowledge bases). A lightweight Flask backend exposes an API and a simple single-page UI that can trigger generation and download the produced JSON.

**Keywords:** web scraping, BeautifulSoup, Flask API, Gemini, prompt engineering, JSON contract, FAQ generation

---

## 1. Introduction
Many small organizations publish information in unstructured webpages (marketing pages, documentation, portfolio sites). Turning that content into a consistent FAQ format is time-consuming when done manually.

The goal of this project is to automate the conversion from webpage text into a high-quality FAQ list while enforcing a machine-readable format (JSON) and limiting output to exactly five items for predictability.

---

## 2. Problem Statement
Given a webpage URL, automatically produce a JSON object containing five FAQ question/answer pairs. The answers must be derived from the webpage text, and the output must be strict JSON with a fixed schema.

Primary challenges:
- Webpages contain noise (scripts, styles, navigation, repeated text).
- LLM output may deviate from the requested format (extra commentary, Markdown, wrong number of items).
- The system needs to be usable by non-developers (simple UI) while remaining scriptable (CLI).

---

## 3. Objectives
### 3.1 Functional objectives
1. Scrape and normalize webpage text.
2. Generate **exactly 5** FAQs in strict JSON format.
3. Provide a web API endpoint to trigger generation.
4. Provide a minimal web UI to input a URL and download JSON.
5. Provide a CLI alternative for batch or terminal usage.

### 3.2 Non-functional objectives
- Reliability: reasonable error reporting when scraping fails or the model response is invalid.
- Reproducibility: configuration via environment variables and `.env` file.
- Simplicity: minimal dependencies and easy local execution on Windows.

---

## 4. Requirements
### 4.1 Inputs
- URL of a webpage (HTTP/HTTPS) OR pasted text (API supports `text`).

### 4.2 Output contract
The intended output schema is:

```json
{
  "faqs": [
    {"question": "...", "answer": "..."},
    {"question": "...", "answer": "..."},
    {"question": "...", "answer": "..."},
    {"question": "...", "answer": "..."},
    {"question": "...", "answer": "..."}
  ]
}
```

Constraints:
- Exactly 5 items.
- `question` and `answer` are strings.
- No Markdown/backticks; **JSON only**.

### 4.3 Configuration
The backend loads configuration using environment variables and a `.env` file:
- `GEMINI_API_KEY` or `GOOGLE_API_KEY` — API key
- `OPENAI_MODEL` — model name (defaults to `gemini-2.5-flash-lite`)

---

## 5. System Overview
The system has two main usage modes:

1. **Web app mode** (recommended for interactive use)
   - Flask backend (`web_app.py`)
   - Static UI (`static/index.html`, `static/app.js`, `static/style.css`)
2. **CLI mode** for quick terminal generation (`faq_generator.py`)

### 5.1 High-level architecture

```
User/UI/CLI
   |
   v
Flask API (/generate)
   |
   +--> Scraper (requests + BeautifulSoup)
   |
   +--> Prompt Builder (strict JSON contract)
   |
   +--> Gemini Call (google-genai SDK, REST fallback)
   |
   +--> JSON parse/validation
   v
Return { success, faqs } (or error)
```

---

## 6. Implementation Details
### 6.1 Web scraping strategy
The scraper uses `requests` to fetch HTML and `BeautifulSoup` to parse it.

Noise reduction:
- Removes `script`, `style`, and `noscript` tags.
- Extracts visible text.
- Normalizes whitespace.
- Truncates text to a maximum length (default ~25k chars) to keep model input bounded.

This behavior exists in:
- `web_app.py` function `scrape_text(url, max_chars=25000)`
- `faq_generator.py` defines a similar internal `scrape_text()` for CLI.

### 6.2 Prompt engineering
The core design choice is a strict contract prompt:
- Explicitly requires a single JSON object with one key: `faqs`.
- Requires exactly 5 objects.
- Requires only JSON (no extra commentary).
- Requests concise, context-grounded answers.

In the backend, the prompt is built by `build_prompt(url, page_text)`.

### 6.3 Model integration (Gemini)
The backend uses a two-tier approach:
1. Prefer the official SDK (`google-genai`, imported as `from google import genai`).
2. If SDK call fails, use the Google Generative Language REST endpoint as a fallback.

This reduces operational risk: if the SDK API surface differs by version or fails in some environments, the REST fallback can still work.

### 6.4 JSON parsing & response handling
Even with strong prompting, LLM output can be invalid JSON. The backend:
- Attempts `json.loads()` on the model output.
- On success: returns `{'success': True, 'faqs': ...}`.
- On failure: returns `{'success': False, 'error': 'Model output was not valid JSON', 'raw': <model_text>}` with HTTP 502.

This design keeps the UI responsive and provides debugging visibility.

### 6.5 Flask API endpoints
The backend exposes:
- `GET /health` — returns `{ok, has_key, model}`.
- `POST /generate` — accepts `{url}` or `{text}` and returns JSON.
- `GET /scraped` — returns the latest `scraped_page.txt` when present.
- `GET /` — serves `static/index.html` if present.

### 6.6 UI behavior
The single-page UI:
- Shows one URL field.
- Calls `POST /generate`.
- Renders the 5 FAQs.
- Provides a **Download JSON** button (client-side blob download).
- Shows a link to view scraped text.

---

## 7. Data Storage
For transparency and debugging, the backend writes the last scraped/used text to:
- `scraped_page.txt` (project root)

This enables:
- verifying the scraper output
- comparing generated FAQs to the underlying text

---

## 8. Testing and Validation
This project primarily uses manual validation:
- `GET /health` to confirm the server is running and has an API key.
- Run generation on known URLs.
- Confirm the returned payload is valid JSON and contains 5 items.

Suggested additional tests (future work):
- Unit tests for `scrape_text()` (tag removal, truncation, whitespace normalization).
- Contract tests for response schema (`faqs` length = 5).
- Golden-file tests using saved HTML fixtures.

---

## 9. Limitations
- Scraping quality depends on HTML structure and may include boilerplate content.
- Some sites block bots or require JavaScript rendering; this implementation uses static HTML only.
- Strictly enforcing “exactly five” relies on the model following instructions; the backend currently validates JSON shape but does not automatically repair outputs (beyond error reporting).
- Model availability: some API keys may not have access to certain model names.

---

## 10. Security and Ethics
- API keys are secrets; they must not be committed. Use `.env` locally.
- Respect website terms of service and robots policies when scraping.
- Generated answers should be considered assistive summaries; for compliance-critical use, implement human review.

---

## 11. Conclusion
The project demonstrates an end-to-end pipeline from web content to structured FAQ JSON using standard Python tools (requests, BeautifulSoup) and a modern LLM (Gemini). The combination of strict prompting, JSON parsing, and a small web UI yields a practical workflow for quickly generating FAQ datasets.

---

## 12. Future Improvements
- Add schema enforcement and automatic repair (e.g., re-prompt on invalid JSON).
- Add deduplication and relevance scoring to reduce boilerplate FAQs.
- Support multi-page crawling (sitemap or internal link depth).
- Add language selection (generate in French/English).
- Add Docker packaging for deployment.

---

## Appendix A — How to run (local)
1. Install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

2. Add `.env`:

```
GEMINI_API_KEY=...
OPENAI_MODEL=gemini-2.5-flash-lite
```

3. Run server:

```powershell
python web_app.py
```

4. Open UI:

http://127.0.0.1:5000/static/index.html

---

## Appendix B — Repository structure (typical)
```
faq_generator.py
web_app.py
web_scraper.py
requirements.txt
.env
static/
  index.html
  app.js
  style.css
scraped_page.txt
```
