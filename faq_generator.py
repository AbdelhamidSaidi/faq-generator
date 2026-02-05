import os
import sys
import json
import urllib.parse
import requests
from google import genai
import requests
from bs4 import BeautifulSoup


def build_prompt(url, page_text):
	return (
		f"You are an assistant that reads the provided website context and returns a "
		f"strictly parseable JSON object with exactly 5 frequently asked questions and answers "
		f"derived from the website. Do not include any extra commentary or explanation—only the JSON.\n\n"
		f"Website URL: {url}\n\n"
		f"Website text (context):\n{page_text}\n\n"
		"Output format (exact JSON):\n"
		"{\n  \"faqs\": [\n    {\"question\": \"...\", \"answer\": \"...\"},\n    {\"question\": \"...\", \"answer\": \"...\"},\n    {\"question\": \"...\", \"answer\": \"...\"},\n    {\"question\": \"...\", \"answer\": \"...\"},\n    {\"question\": \"...\", \"answer\": \"...\"}\n  ]\n}\n"
		"Rules:\n"
		"- Return exactly one JSON object matching the shown structure.\n"
		"- `faqs` must be an array of 5 objects with `question` and `answer` strings.\n"
		"- Use the website context to produce answers; if the site doesn't provide explicit answers, give best-effort answers in the site context.\n"
		"- Do not include markdown, backticks, or any surrounding text.\n"
	)



def main():
	
	input_file = None
	url = None

	def scrape_text(url, max_chars=25000):
		resp = requests.get(url, timeout=15)
		resp.raise_for_status()
		soup = BeautifulSoup(resp.text, "html.parser")
		for tag in soup(["script", "style", "noscript"]):
			tag.decompose()
		text = soup.get_text(separator="\n", strip=True)
		if len(text) > max_chars:
			return text[:max_chars]
		return text

	# Accept either a .txt file path or a URL as the first argument. If none provided, prompt.
	if len(sys.argv) > 1:
		arg = sys.argv[1]
		if os.path.isfile(arg) and arg.lower().endswith('.txt'):
			input_file = arg
			url = f"file://{os.path.abspath(arg)}"
		else:
			# treat as URL
			url = arg
	else:
		url = input("Enter website URL (or path to .txt file): ")
		if not url:
			print("ERROR: No input provided.")
			sys.exit(1)
		if os.path.isfile(url) and url.lower().endswith('.txt'):
			input_file = url
			url = f"file://{os.path.abspath(url)}"

	# Prefer Google API key for Gemini
	client_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
	if not client_key:
		print("ERROR: Please set GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")
		sys.exit(1)
	model_name = os.getenv("OPENAI_MODEL", "gemini-2.5-flash-lite")
	print(f"Using model: {model_name}")

	# Determine page_text: read file if provided, otherwise scrape the URL
	if input_file:
		try:
			with open(input_file, "r", encoding="utf-8") as f:
				page_text = f.read()
			print(f"Loaded text from {input_file}")
		except Exception as e:
			print(f"Failed to read input file {input_file}: {e}")
			sys.exit(1)
	else:
		try:
			print(f"Fetching and scraping {url}...")
			page_text = scrape_text(url)
		except Exception as e:
			print(f"Failed to fetch/scrape the URL: {e}")
			sys.exit(1)

	prompt = build_prompt(url or "", page_text)

	print("Querying Gemini for 5 FAQs (JSON)...")
	try:
		# Initialize genai client: prefer genai.configure if available, otherwise pass api_key to Client
		if hasattr(genai, 'configure'):
			genai.configure(api_key=client_key)
			client = genai.Client()
		else:
			try:
				client = genai.Client(api_key=client_key)
			except TypeError:
				client = genai.Client()
		resp = client.models.generate_content(model=model_name, contents=prompt)
		content = getattr(resp, 'text', None) or getattr(resp, 'output', None) or json.dumps(resp)
	except Exception as e:
		print(f"Gemini API request failed: {e}")
		sys.exit(1)

	# Try to parse JSON from the model output
	try:
		data = json.loads(content)
		print(json.dumps(data, indent=2, ensure_ascii=False))
	except json.JSONDecodeError:
		# If parsing fails, show raw output for debugging
		print("Warning: model output was not valid JSON. Raw output below:\n")
		print(content)


if __name__ == "__main__":
	main()