"""
Models for note operations.

This module contains Pydantic models for serializing and deserializing note data.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ValidationError as PydanticValidationError

# Import the ValidationError from lib to raise instead of Pydantic's ValidationError
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lambdas/layers/common_tools/python"))
from lib import ValidationError  # type: ignore


class NoteRequest(BaseModel):
    """Model for creating or updating a note."""
    title: str = Field(..., description="The title of the note")
    content: str = Field(..., description="The content of the note in markdown format")
    tags: Optional[List[str]] = Field(default=None, description="Tags associated with the note")
    folder: Optional[str] = Field(default=None, description="Folder path for the note")


class NoteResponse(BaseModel):
    """Model for note response data."""
    noteId: str = Field(..., description="The unique identifier for the note")
    userId: str = Field(..., description="The user ID who owns the note")
    title: str = Field(..., description="The title of the note")
    content: Optional[str] = Field(default=None, description="The content of the note in markdown format")
    s3Key: str = Field(..., description="The S3 key where the note content is stored")
    createdAt: str = Field(..., description="The creation timestamp")
    updatedAt: str = Field(..., description="The last update timestamp")
    tags: List[str] = Field(default_factory=list, description="Tags associated with the note")
    folder: Optional[str] = Field(default=None, description="Folder path for the note")
    embeddings: Optional[List[float]] = Field(default=None, description="Vector embeddings for semantic search")

    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> "NoteResponse":
        """
        Create a NoteResponse from a DynamoDB item.
        
        Args:
            item: The DynamoDB item
            
        Returns:
            A NoteResponse instance
        """
        return cls(
            noteId=item.get("noteId", ""),
            userId=item.get("userId", ""),
            title=item.get("title", ""),
            content=item.get("content"),  # May be None if not loaded
            s3Key=item.get("s3Key", ""),
            createdAt=item.get("createdAt", ""),
            updatedAt=item.get("updatedAt", ""),
            tags=item.get("tags", []),
            folder=item.get("folder"),
            embeddings=item.get("embeddings")
        )


class NoteListResponse(BaseModel):
    """Model for listing multiple notes."""
    notes: List[NoteResponse] = Field(..., description="List of notes")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")


class SearchNotesRequest(BaseModel):
    """Model for note search requests."""
    searchType: str = Field(..., description="Type of search: 'text' or 'semantic'")
    query: str = Field(..., description="The search query")
    tags: Optional[List[str]] = Field(default=None, description="Filter by tags")
    fromDate: Optional[str] = Field(default=None, description="Filter by creation date (start)")
    toDate: Optional[str] = Field(default=None, description="Filter by creation date (end)")
    limit: int = Field(default=50, description="Maximum number of results to return")
    
    @classmethod
    def from_request_body(cls, body: Dict[str, Any]) -> "SearchNotesRequest":
        """
        Create a SearchNotesRequest from a request body dictionary,
        handling all validation exceptions internally.
        
        Args:
            body: The request body dictionary
            
        Returns:
            A validated SearchNotesRequest instance
            
        Raises:
            ValidationError: If the body is invalid or validation fails
        """
        try:
            # Create instance from body
            instance = cls(**body)
            
            # Additional validation for searchType
            if instance.searchType not in ["text", "semantic"]:
                raise ValidationError(f"Invalid search type: {instance.searchType}. Must be 'text' or 'semantic'")
                
            # Additional validation for dates if provided
            if instance.fromDate and instance.toDate:
                try:
                    from_date = datetime.fromisoformat(instance.fromDate.replace('Z', '+00:00'))
                    to_date = datetime.fromisoformat(instance.toDate.replace('Z', '+00:00'))
                    if from_date > to_date:
                        raise ValidationError("fromDate must be before toDate")
                except ValueError:
                    raise ValidationError("Invalid date format. Use ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)")
            
            return instance
        except PydanticValidationError as e:
            # Convert Pydantic validation errors to our ValidationError
            error_details = e.errors()
            error_messages = [f"{error['loc'][0]}: {error['msg']}" for error in error_details]
            raise ValidationError(f"Invalid request body: {'; '.join(error_messages)}")
        except Exception as e:
            # Handle any other exceptions
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Invalid request body: {str(e)}") 