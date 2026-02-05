import os
import requests
from bs4 import BeautifulSoup

# The URL of the page you want to scrape
url = "https://abdelhamidsaidi.com"

# Step 1: Fetch the page
response = requests.get(url, timeout=15)
response.raise_for_status()

# Step 2: Parse the HTML
html_content = response.text
soup = BeautifulSoup(html_content, "html.parser")

# Remove scripts/styles
for tag in soup(["script", "style", "noscript"]):
    tag.decompose()

# Step 3: Extract text content from the page
page_text = soup.get_text(separator="\n", strip=True)

# Save scraped text to file
file_path = "scraped_page.txt"

if os.path.exists(file_path):
    os.remove(file_path)
    print(f"Existing file {file_path} removed.")

save_path = os.path.join(os.getcwd(), "scraped_page.txt")
try:
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(page_text)
    print(f"Saved scraped text to {save_path}")
except Exception as e:
    print(f"Failed to save scraped text: {e}")
    print("Scraped text output below:")
    print(page_text[:1000])