import os
import shutil
from collections import Counter
from typing import Tuple
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
import nltk

nltk.download('punkt_tab')

# 🔹 Define Source and Destination Folders
SOURCE_FOLDER = "C:/Users/edgar/OneDrive/Documents/Obsidian/Personal Obsidian/Bytebytego"
DEST_FOLDER = "C:/Users/edgar/OneDrive/Documents/Obsidian/Personal Obsidian/Bytebytego/categories"

# 🔹 Define Categories and Subcategories with Keywords
CATEGORIES = {
    "Distributed_Systems": {
        "Scalability": ["scalability", "load balancing", "horizontal scaling", "distributed systems"],
        "Consistency": ["consistency", "eventual consistency", "quorum", "replication"],
        "Fault_Tolerance": ["fault tolerance", "high availability", "failover", "resilience"]
    },
    "Databases": {
        "SQL": ["sql", "relational", "transactions", "acid", "postgresql", "mysql"],
        "NoSQL": ["nosql", "document store", "key-value", "columnar", "cassandra", "mongodb"],
        "Indexing": ["indexing", "query optimization", "b-tree", "hash indexing", "database performance"]
    },
    "Machine_Learning": {
        "Deep_Learning": ["neural networks", "cnn", "rnn", "deep learning", "transformers"],
        "Reinforcement_Learning": ["reinforcement learning", "q-learning", "policy gradient", "ai"],
        "NLP": ["natural language processing", "nlp", "word embeddings", "text analysis"]
    },
    "Software_Engineering": {
        "Architecture": ["microservices", "monolith", "event-driven", "architecture", "clean architecture"],
        "Development_Methodologies": ["agile", "scrum", "devops", "tdd", "bdd", "software development"]
    },
    "Networking": {
        "Protocols": ["tcp/ip", "udp", "http", "https", "dns", "grpc"],
        "Performance": ["latency", "throughput", "bandwidth", "congestion control", "network optimization"]
    },
    "Cloud_Computing": {
        "AWS": ["aws", "lambda", "s3", "cloudfront", "dynamodb"],
        "Kubernetes": ["kubernetes", "containers", "orchestration", "scaling", "service mesh"]
    },
    "Security": {
        "Authentication": ["jwt", "oauth", "sso", "session tokens", "api security"],
        "Encryption": ["encryption", "ssl", "tls", "hashing", "secure protocols"]
    },
    "System_Design": {
        "High_Availability": ["high availability", "failover", "redundancy", "replication"],
        "Caching": ["cache", "redis", "memcached", "in-memory", "distributed caching"]
    }
}

# 🔹 Ensure Category and Subcategory Folders Exist
os.makedirs(DEST_FOLDER, exist_ok=True)
for category, subcategories in CATEGORIES.items():
    category_path = os.path.join(DEST_FOLDER, category)
    os.makedirs(category_path, exist_ok=True)
    for subcategory in subcategories:
        os.makedirs(os.path.join(category_path, subcategory), exist_ok=True)

# Create "Uncategorized" Folder for Unmatched Files
UNCATEGORIZED_FOLDER = os.path.join(DEST_FOLDER, "Uncategorized")
os.makedirs(UNCATEGORIZED_FOLDER, exist_ok=True)

ps = PorterStemmer()

def classify_file(file_path: str) -> Tuple[str, str]:
    """
    Reads a Markdown file and determines its category and subcategory based on keyword frequency.
    Uses stemming to account for plurals and verb conjugations.

    Args:
        file_path (str): Path to the Markdown file.

    Returns:
        Tuple[str, str]: The determined category and subcategory, or ("Uncategorized", "Uncategorized") if no match is found.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read().lower()
    except Exception as e:
        print(f"⚠️ Error reading {file_path}: {e}")
        return ("Uncategorized", "Uncategorized")
    
    words = word_tokenize(content)
    stemmed_words = [ps.stem(word) for word in words]
    
    category_scores = Counter()
    
    for category, subcategories in CATEGORIES.items():
        for subcategory, keywords in subcategories.items():
            for keyword in keywords:
                stemmed_keyword = ps.stem(keyword)
                category_scores[(category, subcategory)] += stemmed_words.count(stemmed_keyword)
    
    if category_scores:
        best_match = sorted(category_scores.items(), key=lambda x: (-x[1], x[0][0]))[0][0]  # Highest count, then alphabetically
        return best_match
    
    return ("Uncategorized", "Uncategorized")

# 🔹 Process Each Markdown File
for filename in os.listdir(SOURCE_FOLDER):
    if filename.endswith(".md"):  # Only process Markdown files
        file_path = os.path.join(SOURCE_FOLDER, filename)
        try:
            category, subcategory = classify_file(file_path)
            destination_folder = os.path.join(DEST_FOLDER, category, subcategory)
            os.makedirs(destination_folder, exist_ok=True)
            shutil.move(file_path, os.path.join(destination_folder, filename))
            print(f"✅ Moved '{filename}' → {destination_folder}")
        except Exception as e:
            print(f"⚠️ Error processing {filename}: {e}")

# 🔥 Remove Empty Folders
for category in os.listdir(DEST_FOLDER):
    category_path = os.path.join(DEST_FOLDER, category)
    if os.path.isdir(category_path):
        for subcategory in os.listdir(category_path):
            subcategory_path = os.path.join(category_path, subcategory)
            if os.path.isdir(subcategory_path) and not os.listdir(subcategory_path):
                try:
                    shutil.rmtree(subcategory_path)
                except PermissionError:
                    print(f"⚠️ Could not remove {subcategory_path}, check permissions.")
        if not os.listdir(category_path):
            try:
                shutil.rmtree(category_path)
            except PermissionError:
                print(f"⚠️ Could not remove {category_path}, check permissions.")

print("✨ All files classified and organized!")
