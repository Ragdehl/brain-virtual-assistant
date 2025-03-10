import os
import time
import random
import requests
import re

# 🔹 Define Source and Destination Folders
SOURCE_FOLDER = "C:/Users/edgar/OneDrive/Documents/Obsidian/Personal Obsidian/Bytebytego"
IMAGE_FOLDER = "C:/Users/edgar/OneDrive/Documents/Obsidian/Personal Obsidian/Bytebytego/downloaded_images"

# Ensure image folder exists
os.makedirs(IMAGE_FOLDER, exist_ok=True)

def download_image(img_url: str, save_path: str) -> str:
    """
    Downloads an image and saves it to the specified directory with a delay.

    Args:
        img_url (str): The URL of the image.
        save_path (str): The directory where the image should be saved.

    Returns:
        str: The path to the saved image.
    """
    time.sleep(random.uniform(2, 5))  # Random delay to prevent blocking
    try:
        response = requests.get(img_url, stream=True)
        if response.status_code == 200:
            filename = os.path.join(save_path, os.path.basename(img_url))
            os.makedirs(os.path.dirname(filename), exist_ok=True)  # Ensure directory exists
            with open(filename, 'wb') as img_file:
                for chunk in response.iter_content(1024):
                    img_file.write(chunk)
            return filename
    except Exception as e:
        print(f"⚠️ Failed to download {img_url}: {e}")
    return ""

def update_markdown_images(file_path: str) -> None:
    """
    Updates markdown file links to use locally downloaded images instead of remote URLs.

    Args:
        file_path (str): Path to the markdown file.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        
        updated_content = content
        image_links = re.findall(r'!\[.*?\]\((https?://[^)]+)\)', content)
        
        for img_url in image_links:
            relative_path = os.path.relpath(file_path, SOURCE_FOLDER)
            local_folder = os.path.join(IMAGE_FOLDER, os.path.dirname(relative_path))
            local_path = download_image(img_url, local_folder)
            if local_path:
                updated_content = updated_content.replace(img_url, local_path)
        
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(updated_content)
    except Exception as e:
        print(f"⚠️ Error updating images in {file_path}: {e}")

def process_markdown_files(root_folder: str):
    """
    Recursively processes all markdown files in the given root folder.

    Args:
        root_folder (str): The root directory containing markdown files.
    """
    for root, _, files in os.walk(root_folder):
        for filename in files:
            if filename.endswith(".md"):  # Only process Markdown files
                file_path = os.path.join(root, filename)
                try:
                    update_markdown_images(file_path)
                    print(f"✅ Updated images in '{file_path}'")
                except Exception as e:
                    print(f"⚠️ Error processing {file_path}: {e}")

# 🔹 Start processing all markdown files in SOURCE_FOLDER
process_markdown_files(SOURCE_FOLDER)

print("✨ All images downloaded and markdown updated!")
