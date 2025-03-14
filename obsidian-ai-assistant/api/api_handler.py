import json
import logging

from auth import authenticate
from response import error_response, success_response
from utils import log_request

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Main entry point for API Gateway.
    
    Args:
        event (dict): API Gateway Lambda Proxy Input Format
        context (object): Lambda Context runtime methods and attributes
    
    Returns:
        dict: API Gateway Lambda Proxy Output Format
    """
    log_request(event)

    path = event.get("path", "")
    method = event.get("httpMethod", "").upper()
    headers = event.get("headers", {})
    query_params = event.get("queryStringParameters", {}) or {}
    body = None

    if event.get("body"):
        try:
            body = json.loads(event.get("body"))
        except json.JSONDecodeError:
            return error_response(400, "Invalid JSON in request body")

    # Authenticate the request
    user = authenticate(headers)
    if not user:
        return error_response(401, "Unauthorized")

    try:
        # Routes for notes
        if path.startswith("/notes"):
            note_id = path.split("/")[-1] if len(path.split("/")) > 2 else None

            if method == "POST" and not note_id:
                return create_note(body, user)
            elif method == "GET":
                if note_id:
                    return get_note(note_id, user)
                else:
                    return list_notes(query_params, user)
            elif method == "PUT" and note_id:
                return update_note(note_id, body, user)
            elif method == "DELETE" and note_id:
                return delete_note(note_id, user)

        # Route for search
        elif path == "/search" and method == "GET":
            return search_notes(query_params, user)

        # Health check endpoint
        elif path == "/health" and method == "GET":
            return success_response(200, {"status": "healthy"})

        return error_response(404, "Not Found")

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return error_response(500, "Internal Server Error")
