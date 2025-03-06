import os
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify
from typing import List, Optional
import ssl
import certifi
from urllib.parse import urljoin

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

# 🛠️ Function to Initialize Selenium WebDriver (for JavaScript-rendered pages)
def get_selenium_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run Chrome in headless mode (no UI)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 🔍 Function to Scrape Newsletter Links
def get_newsletter_links() -> List[str]:
    """
    Scrape the ByteByteGo newsletter archive page for newsletter URLs.

    Returns:
        List[str]: A list of URLs to individual newsletter pages.
    """
    response = SESSION.get(BASE_URL, cookies=COOKIES)

    # 🛑 Check if the request failed (may indicate a JavaScript-rendered page)
    if response.status_code != 200 or not response.text:
        print(f"⚠️ Failed to fetch archive page with requests ({response.status_code}), trying Selenium...")
        return get_newsletter_links_selenium()

    # 🌐 Parse HTML with BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 🏗️ Extract Newsletter Links (Update Selector Based on Page Structure)
    links = [
        urljoin(BASE_URL, a["href"])  # Ensure absolute URLs
        for a in soup.find_all("a", href=True)  # Grab all anchor tags with href
        if "bytebytego.com/p/" in a["href"]  # Filter for newsletter links
    ]
    
    if not links:
        print("⚠️ No links found with `requests`. Trying Selenium...")
        return get_newsletter_links_selenium()

    print(f"✅ Found {len(links)} newsletters using `requests`.")
    return links

# 🔍 Alternative Function: Use Selenium If JavaScript is Required
def get_newsletter_links_selenium() -> List[str]:
    """
    Use Selenium to scrape newsletter links from a JavaScript-rendered page.

    Returns:
        List[str]: A list of newsletter URLs.
    """
    driver = get_selenium_driver()
    driver.get(BASE_URL)

    # Wait for the page to load (adjust sleep if necessary)
    driver.implicitly_wait(5)

    # Extract all `<a>` elements
    elements = driver.find_elements(By.TAG_NAME, "a")
    
    # Extract and filter newsletter links
    links = [
        urljoin(BASE_URL, el.get_attribute("href"))
        for el in elements
        if el.get_attribute("href") and "bytebytego.com/p/" in el.get_attribute("href")
    ]

    driver.quit()

    if links:
        print(f"✅ Found {len(links)} newsletters using Selenium.")
    else:
        print("❌ No newsletter links found, check page structure.")

    return links

# 📥 Function to Download a Newsletter
def download_newsletter(url: str) -> None:
    """
    Download and convert a newsletter to Markdown format.

    Args:
        url (str): The URL of the newsletter to download.
    """
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

    title = title_element.get_text(strip=True).replace(" ", "_") + ".md"

    # 📌 Extract Content
    content = soup.find("article") or soup.find("div", class_="newsletter-content")
    if not content:
        print(f"⚠️ No content found for {url}. Skipping.")
        return

    # Convert HTML to Markdown
    md_content = markdownify(str(content))

    # Save to File
    with open(os.path.join(OUTPUT_DIR, title), "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print(f"✅ Saved: {title}")

# 🚀 Main Function to Download All Newsletters
def main() -> None:
    """
    Download all ByteByteGo newsletters from the archive.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    links = get_newsletter_links()
    if not links:
        print("❌ No newsletter links found. Exiting.")
        return

    for link in links:
        download_newsletter(link)

if __name__ == "__main__":
    main()
