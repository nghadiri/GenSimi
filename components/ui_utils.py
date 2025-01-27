from urllib.parse import urlparse

def get_neo4j_url_from_uri(uri: str) -> str:
    """Convert Neo4j URI to browser URL"""
    parsed = urlparse(uri)
    port = "7474" if parsed.scheme == "neo4j" else "7473"
    return f"http://{parsed.hostname}:{port}/browser/"

def format_metadata(metadata: dict) -> str:
    """Format metadata for display"""
    if not metadata:
        return ""
    
    formatted = []
    for key, value in metadata.items():
        if isinstance(value, list):
            formatted.append(f"**{key}**: {', '.join(str(v) for v in value[:3])}...")
        else:
            formatted.append(f"**{key}**: {value}")
    
    return "\n".join(formatted)