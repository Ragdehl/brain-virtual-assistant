"""
Request model for creating a note.
"""
from typing import Any, Dict, List, Optional

# JSON schema for note creation request
CREATE_NOTE_SCHEMA = {
    "type": "object",
    "required": ["title", "content"],
    "properties": {
        "title": {
            "type": "string",
            "minLength": 1,
            "maxLength": 200,
            "description": "Title of the note"
        },
        "content": {
            "type": "string",
            "minLength": 1,
            "description": "Content of the note in Markdown format"
        },
        "tags": {
            "type": "array",
            "items": {
                "type": "string",
                "minLength": 1,
                "maxLength": 50
            },
            "description": "List of tags associated with the note"
        },
        "folder": {
            "type": "string",
            "description": "Folder path for the note"
        }
    },
    "additionalProperties": False
}


def validate_create_note_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a note creation request against the schema.

    Args:
        data (dict): Request data to validate

    Returns:
        dict: Validation errors, or empty dict if valid
    """
    errors = {}

    # Validate required fields
    if "title" not in data:
        errors["title"] = "Title is required"
    elif not isinstance(data["title"], str):
        errors["title"] = "Title must be a string"
    elif len(data["title"]) < 1:
        errors["title"] = "Title cannot be empty"
    elif len(data["title"]) > 200:
        errors["title"] = "Title cannot exceed 200 characters"

    if "content" not in data:
        errors["content"] = "Content is required"
    elif not isinstance(data["content"], str):
        errors["content"] = "Content must be a string"
    elif len(data["content"]) < 1:
        errors["content"] = "Content cannot be empty"

    # Validate optional fields
    if "tags" in data:
        if not isinstance(data["tags"], list):
            errors["tags"] = "Tags must be an array"
        else:
            invalid_tags = []
            for i, tag in enumerate(data["tags"]):
                if not isinstance(tag, str):
                    invalid_tags.append(f"Tag at index {i} must be a string")
                elif len(tag) < 1:
                    invalid_tags.append(f"Tag at index {i} cannot be empty")
                elif len(tag) > 50:
                    invalid_tags.append(f"Tag at index {i} cannot exceed 50 characters")
            if invalid_tags:
                errors["tags"] = invalid_tags

    if "folder" in data and not isinstance(data["folder"], str):
        errors["folder"] = "Folder must be a string"

    # Check for additional properties
    allowed_props = {"title", "content", "tags", "folder"}
    additional_props = [prop for prop in data.keys() if prop not in allowed_props]
    if additional_props:
        errors["additionalProperties"] = f"Unknown properties: {', '.join(additional_props)}"

    return errors 