import os
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify
from typing import List
import time
import random
from urllib.parse import urlparse

# 🔹 Session Setup
SESSION = requests.Session()

# 🔐 Replace this with your authenticated session cookie from the browser
COOKIES = {
    "connect.sid": "s%3Afp78tknzDGuLFLoUQRi3SZXFdn9s55rT.jnY03Q8IZ7O7Hr987QdzfpdeHQI3AbYg8nR%2F5ou2IYI"
}

SITEMAP_URL = "https://blog.bytebytego.com/sitemap.xml"
OUTPUT_DIR = "C:/Users/edgar/OneDrive/Documents/Obsidian/Personal Obsidian/Bytebytego"
REQUEST_DELAY = (2, 7)  # ⏳ Random delay range (seconds) to avoid being blocked

# 🔗 Function to Clean Newsletter URLs (Remove `/comments` or similar)
def clean_url(url: str) -> str:
    """
    Removes unnecessary path segments from a URL (e.g., `/comments` at the end).
    
    Args:
        url (str): The original URL.

    Returns:
        str: The cleaned URL.
    """
    parsed = urlparse(url)
    cleaned_path = "/".join(parsed.path.split("/")[:3])  # Keep only the first 3 segments
    cleaned_url = f"{parsed.scheme}://{parsed.netloc}{cleaned_path}"
    return cleaned_url

# 🔍 Function to Extract Newsletter Links from Sitemap
def get_newsletter_links() -> List[str]:
    """
    Extracts all newsletter links from the sitemap.
    
    Returns:
        List[str]: A list of URLs to individual newsletter pages.
    """
    response = SESSION.get(SITEMAP_URL)
    if response.status_code != 200:
        print("⚠️ Failed to fetch sitemap.")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    urls = [clean_url(loc.text) for loc in soup.find_all("loc") if "/p/" in loc.text]
    
    print(f"✅ Found {len(urls)} newsletters from sitemap.")
    return urls

# 👥 Function to Download a Newsletter
def download_newsletter(url: str) -> None:
    """Download and convert a newsletter to Markdown format.

    Args:
        url (str): The URL of the newsletter to download.

    The function saves the newsletter as a Markdown file in the OUTPUT_DIR directory.
    The filename includes both the newsletter's title and the last segment of the URL
    for better identification and to prevent filename collisions. If the file already
    exists, the download is skipped.
    """
    print(f"📥 Downloading: {url}")

    # First, get the URL slug to check if we already have this newsletter
    url_slug = url.rstrip('/').split('/')[-1]
    
    # Check if any existing files contain this URL slug
    existing_files = os.listdir(OUTPUT_DIR) if os.path.exists(OUTPUT_DIR) else []
    for existing_file in existing_files:
        if url_slug in existing_file:
            print(f"⏩ Already downloaded: {existing_file}. Skipping.")
            return

    response = SESSION.get(url, cookies=COOKIES)
    if response.status_code != 200:
        print(f"⚠️ Failed to fetch newsletter: {url}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract the last part of the URL for the filename
    url_slug = url.rstrip('/').split('/')[-1]
    
    # Create filename
    filename = f"{url_slug}.md"

    # 📌 Extract Content
    content = soup.find("article") or soup.find("div", class_="newsletter-content")
    if not content:
        print(f"⚠️ No content found for {url}. Skipping.")
        return

    # Convert HTML to Markdown
    md_content = markdownify(str(content))

    # Save to File
    with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print(f"✅ Saved: {filename}")

# 🚀 Main Function to Download All Newsletters
def main() -> None:
    """Download all ByteByteGo newsletters from the sitemap.
    
    Creates the output directory if it doesn't exist, then iterates through
    all newsletter links to download and save each newsletter as a Markdown file.
    A random delay between requests is added to avoid overwhelming the server.
    """
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Get all newsletter links
    links = get_newsletter_links()
    print(f"🔍 Found {len(links)} newsletters")

    # Download each newsletter
    for i, link in enumerate(links):
        download_newsletter(link)
        
        # Add a random delay between requests (between REQUEST_DELAY range)
        if i < len(links) - 1:  # No need to wait after the last request
            delay = random.uniform(*REQUEST_DELAY)
            print(f"⏱️ Waiting {delay:.2f} seconds before next request...")
            time.sleep(delay)

    print("✨ All newsletters downloaded!")

if __name__ == "__main__":
    main()
