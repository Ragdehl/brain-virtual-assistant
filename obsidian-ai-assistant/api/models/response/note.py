"""
Response model for a note.
"""
from typing import Any, Dict, List, Optional


def format_note_response(note: Dict[str, Any], include_content: bool = True) -> Dict[str, Any]:
    """
    Format a note for API response.

    Args:
        note (dict): Note data from DynamoDB
        include_content (bool): Whether to include the note content

    Returns:
        dict: Formatted note response
    """
    response = {
        "id": note.get("id"),
        "title": note.get("title"),
        "createdAt": note.get("createdAt"),
        "updatedAt": note.get("updatedAt"),
        "tags": note.get("tags", []),
        "folder": note.get("folder", "")
    }

    if include_content and "content" in note:
        response["content"] = note["content"]

    return response


def format_note_list_response(
    notes: List[Dict[str, Any]],
    total_count: int,
    next_cursor: Optional[str] = None
) -> Dict[str, Any]:
    """
    Format a list of notes for API response.

    Args:
        notes (list): List of notes from DynamoDB
        total_count (int): Total count of notes
        next_cursor (str, optional): Cursor for pagination

    Returns:
        dict: Formatted note list response
    """
    formatted_notes = [format_note_response(note, include_content=False) for note in notes]

    response = {
        "notes": formatted_notes,
        "totalCount": total_count
    }

    if next_cursor:
        response["nextCursor"] = next_cursor

    return response 