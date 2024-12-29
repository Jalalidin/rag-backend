import mimetypes
import os

def get_mime_type(filename: str) -> str:
    """
    Get MIME type for a file based on its extension.
    
    Args:
        filename: Name of the file
        
    Returns:
        str: MIME type of the file
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream' 