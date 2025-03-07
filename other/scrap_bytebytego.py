import os
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify
from typing import List, Optional
import ssl
import certifi
import time
from urllib.parse import urljoin
from urllib.parse import urlparse
import random

# 🖥️ Selenium Imports for JavaScript-Rendered Pages
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 🔹 Session Setup with Updated SSL Certificates
SESSION = requests.Session()
SESSION.verify = certifi.where()  # Force updated SSL certs

# 🔐 Replace this with your authenticated session cookie from the browser
COOKIES = {
    "connect.sid": "s%3Afp78tknzDGuLFLoUQRi3SZXFdn9s55rT.jnY03Q8IZ7O7Hr987QdzfpdeHQI3AbYg8nR%2F5ou2IYI"
}

BASE_URL = "https://blog.bytebytego.com/archive"
OUTPUT_DIR = "bytebytego_newsletters"
REQUEST_DELAY = 5  # ⏳ Delay (in seconds) between requests to avoid being blocked

# 🛠️ Function to Initialize Selenium WebDriver
def get_selenium_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run Chrome in headless mode (no UI)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 🔍 Function to Scroll & Load All Newsletter Links
def get_newsletter_links_selenium() -> List[str]:
    """
    Use Selenium to scroll and load all newsletter links dynamically.
    
    Returns:
        List[str]: A list of URLs to individual newsletter pages.
    """
    driver = get_selenium_driver()
    driver.get(BASE_URL)

    # Simulate scrolling to load more content
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # Scroll to bottom
        time.sleep(2)  # Wait for new content to load
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:  # Stop if no new content loads
            break
        
        last_height = new_height

    print("✅ Finished scrolling. Extracting links...")

    # Extract all `<a>` elements
    elements = driver.find_elements(By.TAG_NAME, "a")
    
    # Extract and filter newsletter links
    links = [
        clean_url(urljoin(BASE_URL, el.get_attribute("href")))
        for el in elements
        if el.get_attribute("href") and "bytebytego.com/p/" in el.get_attribute("href")
    ]

    driver.quit()

    if links:
        print(f"✅ Found {len(links)} newsletters using Selenium.")
    else:
        print("❌ No newsletter links found, check page structure.")

    return links

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

# 📥 Function to Download a Newsletter
def download_newsletter(url: str) -> None:
    """Download and convert a newsletter to Markdown format.

    Args:
        url (str): The URL of the newsletter to download.

    The function saves the newsletter as a Markdown file in the OUTPUT_DIR directory.
    The filename includes both the newsletter's title and the last segment of the URL
    for better identification and to prevent filename collisions.
    """
    print(f"📥 Downloading: {url}")

    response = SESSION.get(url, cookies=COOKIES)
    if response.status_code != 200:
        print(f"⚠️ Failed to fetch newsletter: {url}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    # 📌 Extract Title
    title_element = soup.find("h1")
    if not title_element:
        print(f"⚠️ No title found for {url}. Skipping.")
        return

    # Extract the last part of the URL for the filename
    url_slug = url.rstrip('/').split('/')[-1]
    
    # Combine title and URL slug for the filename
    title_text = title_element.get_text(strip=True).replace(" ", "_")
    filename = f"{title_text}_{url_slug}.md"

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
    """Download all ByteByteGo newsletters from the archive.
    
    Creates the output directory if it doesn't exist, then iterates through
    all newsletter links to download and save each newsletter as a Markdown file.
    A random delay between requests is added to avoid overwhelming the server.
    """
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Get all newsletter links
    links = get_newsletter_links_selenium()
    print(f"🔍 Found {len(links)} newsletters")

    # Download each newsletter
    for i, link in enumerate(links):
        download_newsletter(link)
        
        # Add a random delay between requests (between 2 and 7 seconds)
        if i < len(links) - 1:  # No need to wait after the last request
            delay = random.uniform(2, 7)
            print(f"⏱️ Waiting {delay:.2f} seconds before next request...")
            time.sleep(delay)

    print("✨ All newsletters downloaded!")

if __name__ == "__main__":
    main()