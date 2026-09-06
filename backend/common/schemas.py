USER_AVATAR_SCHEMA = {
    "type": "object",
    "properties": {
        "provider": {"enum": ["google-oauth2", "gravatar", "microsoft-graph"]},
        "google-oauth2": {"type": "string", "format": "uri"},
        "gravatar": {"type": "string", "format": "uri"},
        "microsoft-graph": {"type": "string", "format": "uri"},
    },
    "required": ["provider"],
    "additionalProperties": False,
}
