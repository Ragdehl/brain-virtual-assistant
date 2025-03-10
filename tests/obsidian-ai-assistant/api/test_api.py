#!/usr/bin/env python3
"""
Test API Gateway endpoints for the Obsidian AI Assistant.

This script runs tests against the API Gateway endpoints to verify
that the API is functioning correctly.
"""

import os
import sys
import json
import uuid
import requests
import argparse
import logging
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ApiTester:
    """
    Class for testing API Gateway endpoints.
    """
    
    def __init__(self, api_url: str, api_key: Optional[str] = None):
        """
        Initialize the API tester.
        
        Args:
            api_url: The base URL of the API Gateway
            api_key: Optional API key for authentication
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.headers = {}
        
        if api_key:
            self.headers['x-api-key'] = api_key
    
    def test_get_note(self, note_id: str) -> bool:
        """
        Test the GET /notes/{note_id} endpoint.
        
        Args:
            note_id: The ID of the note to retrieve
            
        Returns:
            True if the test passed, False otherwise
        """
        logger.info(f"Testing GET /notes/{note_id}")
        
        try:
            response = requests.get(
                f"{self.api_url}/notes/{note_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                note = response.json()
                logger.info(f"Successfully retrieved note: {note.get('title', 'Untitled')}")
                return True
            elif response.status_code == 404:
                logger.warning(f"Note {note_id} not found")
                return False
            else:
                logger.error(f"Error retrieving note: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Exception during GET /notes/{note_id}: {str(e)}")
            return False
    
    def test_create_note(self, title: str, content: str) -> Optional[str]:
        """
        Test the POST /notes endpoint.
        
        Args:
            title: The title of the note
            content: The content of the note
            
        Returns:
            The ID of the created note if successful, None otherwise
        """
        logger.info(f"Testing POST /notes with title: {title}")
        
        try:
            response = requests.post(
                f"{self.api_url}/notes",
                headers=self.headers,
                json={
                    'title': title,
                    'content': content
                }
            )
            
            if response.status_code == 201:
                result = response.json()
                note_id = result.get('id')
                logger.info(f"Successfully created note with ID: {note_id}")
                return note_id
            else:
                logger.error(f"Error creating note: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Exception during POST /notes: {str(e)}")
            return None
    
    def test_update_note(self, note_id: str, title: str, content: str) -> bool:
        """
        Test the PUT /notes/{note_id} endpoint.
        
        Args:
            note_id: The ID of the note to update
            title: The new title of the note
            content: The new content of the note
            
        Returns:
            True if the test passed, False otherwise
        """
        logger.info(f"Testing PUT /notes/{note_id}")
        
        try:
            response = requests.put(
                f"{self.api_url}/notes/{note_id}",
                headers=self.headers,
                json={
                    'title': title,
                    'content': content
                }
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully updated note {note_id}")
                return True
            else:
                logger.error(f"Error updating note: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Exception during PUT /notes/{note_id}: {str(e)}")
            return False
    
    def test_delete_note(self, note_id: str) -> bool:
        """
        Test the DELETE /notes/{note_id} endpoint.
        
        Args:
            note_id: The ID of the note to delete
            
        Returns:
            True if the test passed, False otherwise
        """
        logger.info(f"Testing DELETE /notes/{note_id}")
        
        try:
            response = requests.delete(
                f"{self.api_url}/notes/{note_id}",
                headers=self.headers
            )
            
            if response.status_code == 204:
                logger.info(f"Successfully deleted note {note_id}")
                return True
            else:
                logger.error(f"Error deleting note: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Exception during DELETE /notes/{note_id}: {str(e)}")
            return False
    
    def test_search_notes(self, query: str) -> bool:
        """
        Test the GET /notes/search endpoint.
        
        Args:
            query: The search query
            
        Returns:
            True if the test passed, False otherwise
        """
        logger.info(f"Testing GET /notes/search?q={query}")
        
        try:
            response = requests.get(
                f"{self.api_url}/notes/search",
                headers=self.headers,
                params={'q': query}
            )
            
            if response.status_code == 200:
                results = response.json()
                logger.info(f"Search returned {len(results)} results")
                return True
            else:
                logger.error(f"Error searching notes: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Exception during GET /notes/search: {str(e)}")
            return False
    
    def run_all_tests(self) -> None:
        """
        Run all API tests.
        """
        logger.info(f"Running all tests against {self.api_url}")
        
        # Create a test note
        test_title = f"Test Note {uuid.uuid4()}"
        test_content = "This is a test note created by the API tester."
        
        note_id = self.test_create_note(test_title, test_content)
        
        if note_id:
            # Test retrieving the note
            self.test_get_note(note_id)
            
            # Test updating the note
            updated_title = f"Updated {test_title}"
            updated_content = f"{test_content}\n\nThis note has been updated."
            self.test_update_note(note_id, updated_title, updated_content)
            
            # Test searching for the note
            self.test_search_notes("test note")
            
            # Test deleting the note
            self.test_delete_note(note_id)
            
            # Verify the note was deleted
            if not self.test_get_note(note_id):
                logger.info("Delete verification passed")
        
        logger.info("All tests completed")

def main():
    parser = argparse.ArgumentParser(description='Test API Gateway endpoints')
    parser.add_argument('--api-url', required=True, help='Base URL of the API Gateway')
    parser.add_argument('--api-key', help='API key for authentication')
    parser.add_argument('--create', action='store_true', help='Test creating a note')
    parser.add_argument('--get', help='Test getting a note by ID')
    parser.add_argument('--update', help='Test updating a note by ID')
    parser.add_argument('--delete', help='Test deleting a note by ID')
    parser.add_argument('--search', help='Test searching for notes')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    tester = ApiTester(args.api_url, args.api_key)
    
    if args.all:
        tester.run_all_tests()
    else:
        if args.create:
            title = f"Test Note {uuid.uuid4()}"
            content = "This is a test note created by the API tester."
            tester.test_create_note(title, content)
        
        if args.get:
            tester.test_get_note(args.get)
        
        if args.update:
            title = f"Updated Note {uuid.uuid4()}"
            content = "This note has been updated by the API tester."
            tester.test_update_note(args.update, title, content)
        
        if args.delete:
            tester.test_delete_note(args.delete)
        
        if args.search:
            tester.test_search_notes(args.search)
        
        if not any([args.create, args.get, args.update, args.delete, args.search, args.all]):
            parser.print_help()

if __name__ == "__main__":
    main() 