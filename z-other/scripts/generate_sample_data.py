#!/usr/bin/env python3
"""
Generate sample notes for testing.

This script creates test notes in S3 and DynamoDB for development and testing.
"""

import os
import sys
import boto3
import json
import uuid
import argparse
import logging
import random
from datetime import datetime
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Sample note templates
SAMPLE_NOTES = [
    {
        "title": "Getting Started with Obsidian AI Assistant",
        "content": """# Getting Started with Obsidian AI Assistant

Welcome to Obsidian AI Assistant! This tool helps you organize and search your notes using AI.

## Key Features

- Create and edit markdown notes
- Semantic search across your notes
- AI-powered suggestions and insights
- Secure cloud storage

## Next Steps

1. Create your first note
2. Explore the search functionality
3. Try the AI assistant features
"""
    },
    {
        "title": "Project Ideas",
        "content": """# Project Ideas

## Web Development
- Personal portfolio site
- Recipe sharing platform
- Productivity tracker

## Data Science
- Sentiment analysis of news articles
- Stock price prediction model
- Image classification for plant species

## Mobile Apps
- Habit tracker
- Meditation timer
- Language learning flashcards
"""
    },
    {
        "title": "Meeting Notes - Product Team",
        "content": """# Meeting Notes - Product Team

**Date**: {date}
**Attendees**: Alice, Bob, Charlie, Diana

## Agenda
1. Q2 roadmap review
2. Feature prioritization
3. User feedback discussion

## Action Items
- Alice: Finalize Q2 roadmap document
- Bob: Schedule user testing sessions
- Charlie: Update design prototypes
- Diana: Prepare analytics report

## Notes
We discussed the upcoming features and decided to prioritize the search improvements and mobile app integration for Q2.
"""
    },
    {
        "title": "Research on Machine Learning",
        "content": """# Research on Machine Learning

## Supervised Learning
- Classification algorithms
- Regression techniques
- Evaluation metrics

## Unsupervised Learning
- Clustering methods
- Dimensionality reduction
- Anomaly detection

## Reinforcement Learning
- Q-learning
- Policy gradients
- Applications in robotics

## Resources
- [Stanford CS229 Course](https://cs229.stanford.edu/)
- [Deep Learning Book](https://www.deeplearningbook.org/)
- [arXiv Papers](https://arxiv.org/list/cs.LG/recent)
"""
    },
    {
        "title": "Weekly Goals",
        "content": """# Weekly Goals

## Work
- Complete project proposal
- Review code PRs
- Attend team meeting

## Personal
- Read 50 pages of current book
- Exercise 3 times
- Meal prep for the week

## Learning
- Complete online course module
- Practice coding problems
- Watch tech conference talk
"""
    },
    {
        "title": "Book Notes: Thinking Fast and Slow",
        "content": """# Book Notes: Thinking Fast and Slow

## Key Concepts
- System 1 (fast, intuitive) vs System 2 (slow, deliberate) thinking
- Cognitive biases and heuristics
- Prospect theory and loss aversion

## Interesting Quotes
> "A reliable way to make people believe in falsehoods is frequent repetition, because familiarity is not easily distinguished from truth."

> "Nothing in life is as important as you think it is when you are thinking about it."

## Applications
- Decision making frameworks
- Understanding cognitive biases in daily life
- Improving judgment under uncertainty
"""
    },
    {
        "title": "Travel Plans: Japan 2023",
        "content": """# Travel Plans: Japan 2023

## Itinerary
- Tokyo (5 days)
- Kyoto (3 days)
- Osaka (2 days)
- Hiroshima (2 days)

## Must-See Places
- Shibuya Crossing
- Fushimi Inari Shrine
- Arashiyama Bamboo Grove
- Hiroshima Peace Memorial

## Practical Info
- JR Pass: 7-day, activate in Tokyo
- Accommodations: Mix of hotels and ryokans
- Budget: ~$3000 excluding flights
"""
    },
    {
        "title": "Recipe Collection",
        "content": """# Recipe Collection

## Breakfast
- Overnight oats with berries
- Avocado toast with poached eggs
- Spinach and feta omelette

## Main Dishes
- Lemon garlic roast chicken
- Vegetable curry with coconut milk
- Pasta with homemade pesto

## Desserts
- Dark chocolate brownies
- Apple crumble
- Lemon bars
"""
    },
    {
        "title": "Coding Best Practices",
        "content": """# Coding Best Practices

## Code Organization
- Follow consistent naming conventions
- Keep functions small and focused
- Use meaningful comments

## Testing
- Write unit tests for core functionality
- Implement integration tests
- Use test-driven development when appropriate

## Version Control
- Make small, focused commits
- Write clear commit messages
- Use feature branches for new development
"""
    },
    {
        "title": "Meditation Techniques",
        "content": """# Meditation Techniques

## Mindfulness Meditation
- Focus on breath
- Body scan technique
- Observing thoughts without judgment

## Loving-Kindness Meditation
- Cultivating compassion for self and others
- Repeating positive phrases
- Visualization exercises

## Movement Meditation
- Walking meditation
- Tai chi
- Yoga flows

## Resources
- Headspace app
- "Wherever You Go, There You Are" book
- Local meditation groups
"""
    }
]

def generate_note_id() -> str:
    """
    Generate a unique note ID.
    
    Returns:
        A unique note ID
    """
    return str(uuid.uuid4())

def create_sample_note(bucket_name: str, table_name: str, note_template: Dict[str, str]) -> str:
    """
    Create a sample note in S3 and DynamoDB.
    
    Args:
        bucket_name: The S3 bucket name
        table_name: The DynamoDB table name
        note_template: The note template
        
    Returns:
        The ID of the created note
    """
    # Generate a unique ID for the note
    note_id = generate_note_id()
    
    # Format the content with current date if needed
    content = note_template['content'].format(date=datetime.now().strftime('%Y-%m-%d'))
    
    # Create the note in S3
    s3_key = f"notes/{note_id}.md"
    s3.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=content.encode('utf-8'),
        ContentType='text/markdown'
    )
    
    # Create the note metadata in DynamoDB
    table = dynamodb.Table(table_name)
    timestamp = int(datetime.now().timestamp())
    
    table.put_item(
        Item={
            'id': note_id,
            'title': note_template['title'],
            's3Key': s3_key,
            'createdAt': timestamp,
            'updatedAt': timestamp,
            'tags': generate_random_tags()
        }
    )
    
    logger.info(f"Created sample note: {note_template['title']} (ID: {note_id})")
    return note_id

def generate_random_tags() -> List[str]:
    """
    Generate a random list of tags.
    
    Returns:
        A list of random tags
    """
    all_tags = [
        'work', 'personal', 'ideas', 'research', 'meeting', 'project',
        'learning', 'book', 'travel', 'food', 'health', 'technology',
        'productivity', 'finance', 'goals', 'reference'
    ]
    
    # Select 0-3 random tags
    num_tags = random.randint(0, 3)
    if num_tags == 0:
        return []
    
    return random.sample(all_tags, num_tags)

def generate_sample_data(bucket_name: str, table_name: str, num_notes: int = 10) -> None:
    """
    Generate sample notes for testing.
    
    Args:
        bucket_name: The S3 bucket name
        table_name: The DynamoDB table name
        num_notes: The number of notes to generate
    """
    logger.info(f"Generating {num_notes} sample notes")
    
    # Ensure the S3 bucket exists
    try:
        s3.head_bucket(Bucket=bucket_name)
    except:
        logger.info(f"Creating S3 bucket {bucket_name}")
        s3.create_bucket(Bucket=bucket_name)
    
    # Ensure the DynamoDB table exists
    try:
        table = dynamodb.Table(table_name)
        table.table_status
    except:
        logger.info(f"Creating DynamoDB table {table_name}")
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        # Wait for the table to be created
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
    
    # Generate the sample notes
    note_ids = []
    for i in range(num_notes):
        # Select a random note template (with replacement)
        template = random.choice(SAMPLE_NOTES)
        
        # Create the note
        note_id = create_sample_note(bucket_name, table_name, template)
        note_ids.append(note_id)
    
    logger.info(f"Successfully generated {len(note_ids)} sample notes")
    
    # Print the IDs of the generated notes
    logger.info("Generated note IDs:")
    for note_id in note_ids:
        logger.info(f"  {note_id}")

def main():
    parser = argparse.ArgumentParser(description='Generate sample notes for testing')
    parser.add_argument('--s3-bucket', help='S3 bucket name')
    parser.add_argument('--dynamodb-table', help='DynamoDB table name')
    parser.add_argument('--num-notes', type=int, default=10, help='Number of notes to generate')
    
    args = parser.parse_args()
    
    # Get values from environment variables if not provided as arguments
    s3_bucket = args.s3_bucket or os.environ.get('S3_BUCKET')
    dynamodb_table = args.dynamodb_table or os.environ.get('DYNAMODB_TABLE')
    
    if not s3_bucket:
        logger.error("S3 bucket name is required")
        sys.exit(1)
    
    if not dynamodb_table:
        logger.error("DynamoDB table name is required")
        sys.exit(1)
    
    generate_sample_data(s3_bucket, dynamodb_table, args.num_notes)

if __name__ == "__main__":
    main()