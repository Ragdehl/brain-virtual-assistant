"""
Unit tests for the notes Lambda functions.

This module contains tests for the CRUD operations on notes,
including creating, retrieving, updating, and deleting notes.
"""

import unittest
import json
import os
import sys
import uuid
import boto3
from datetime import datetime
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List, Optional

# Add the Lambda function directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambdas', 'notes'))

# Import the Lambda functions
import create_note
import get_note
import update_note
import delete_note

class TestNotes(unittest.TestCase):
    """Test cases for the notes Lambda functions."""
    
    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Mock environment variables
        os.environ['DYNAMODB_TABLE'] = 'test-table'
        os.environ['S3_BUCKET'] = 'test-bucket'
        
        # Mock AWS services
        self.dynamodb_mock = MagicMock()
        self.s3_mock = MagicMock()
        
        # Sample note data
        self.sample_note: Dict[str, Any] = {
            'title': 'Test Note',
            'content': '# Test Note\n\nThis is a test note.',
            'tags': ['test', 'sample']
        }
        
        # Sample note ID
        self.sample_note_id: str = str(uuid.uuid4())
        
    @patch('boto3.resource')
    @patch('boto3.client')
    def test_create_note(self, mock_client: MagicMock, mock_resource: MagicMock) -> None:
        """
        Test creating a new note.
        
        This test verifies that:
        1. The create_note function returns a 201 status code
        2. The response includes a note ID
        3. DynamoDB and S3 are called with the correct parameters
        """
        # Set up mocks
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        
        # Create event
        event: Dict[str, Any] = {
            'body': json.dumps(self.sample_note)
        }
        
        # Call the Lambda function
        response: Dict[str, Any] = create_note.handler(event, {})
        
        # Assert response
        self.assertEqual(response['statusCode'], 201)
        response_body: Dict[str, Any] = json.loads(response['body'])
        self.assertIn('id', response_body)
        self.assertEqual(response_body['message'], 'Note created successfully')
        
        # Assert DynamoDB and S3 were called
        mock_table.put_item.assert_called_once()
        mock_client.return_value.put_object.assert_called_once()
    
    @patch('boto3.resource')
    @patch('boto3.client')
    def test_get_note(self, mock_client: MagicMock, mock_resource: MagicMock) -> None:
        """
        Test retrieving a note.
        
        This test verifies that:
        1. The get_note function returns a 200 status code for existing notes
        2. The response includes the note data
        3. The function returns a 404 status code for non-existent notes
        """
        # Set up mocks
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        
        # Mock DynamoDB response
        mock_table.get_item.return_value = {
            'Item': {
                'id': self.sample_note_id,
                'title': self.sample_note['title'],
                'tags': self.sample_note['tags'],
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
        }
        
        # Mock S3 response
        mock_client.return_value.get_object.return_value = {
            'Body': MagicMock(read=lambda: self.sample_note['content'].encode('utf-8'))
        }
        
        # Create event
        event: Dict[str, Any] = {
            'pathParameters': {
                'id': self.sample_note_id
            }
        }
        
        # Call the Lambda function
        response: Dict[str, Any] = get_note.handler(event, {})
        
        # Assert response
        self.assertEqual(response['statusCode'], 200)
        response_body: Dict[str, Any] = json.loads(response['body'])
        self.assertEqual(response_body['id'], self.sample_note_id)
        self.assertEqual(response_body['title'], self.sample_note['title'])
        self.assertEqual(response_body['content'], self.sample_note['content'])
        
        # Test non-existent note
        mock_table.get_item.return_value = {}
        response = get_note.handler(event, {})
        self.assertEqual(response['statusCode'], 404)
    
    # Add more tests for update_note, delete_note, etc.

if __name__ == '__main__':
    unittest.main() 