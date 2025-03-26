"""
Models package for the Obsidian AI Assistant.

This package contains Pydantic models for request and response serialization.
"""

from .note import (
    NoteRequest,
    NoteResponse,
    NoteListResponse,
    SearchNotesRequest
)

__all__ = [
    "NoteRequest",
    "NoteResponse",
    "NoteListResponse",
    "SearchNotesRequest"
] 