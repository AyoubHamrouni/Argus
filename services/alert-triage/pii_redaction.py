import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Regular expressions for common PII and sensitive tokens
PII_PATTERNS = {
    "EMAIL": r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
    # Credit Card (Visa, MasterCard, Amex, Discover)
    "CREDIT_CARD": r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9][0-9])[0-9]{12})\b',
    # SSN (US)
    "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
    # Simple hash detection (MD5, SHA1, SHA256) - sometimes we want hashes for IOCs, but if we want to redact 'passwords/hashes', we can be selective. The user asked for "hashes".
    # We will redact raw hex strings that look like typical password hashes but might leave known IOC hashes if needed. For now, redact 32, 40, 64 char hex strings.
    "HASH": r'\b[A-Fa-f0-9]{32}\b|\b[A-Fa-f0-9]{40}\b|\b[A-Fa-f0-9]{64}\b',
    # Passwords in URLs (e.g., http://user:password@host)
    "URL_PASSWORD": r'(?<=://)[^:@\s]+:([^:@\s]+)(?=@)',
}

def redact_text(text: str) -> str:
    """Redact sensitive tokens from a string."""
    if not text:
        return text
    
    redacted_text = text
    for token_type, pattern in PII_PATTERNS.items():
        # URL_PASSWORD is a special case with a capture group
        if token_type == "URL_PASSWORD":
            redacted_text = re.sub(pattern, '[REDACTED_PASSWORD]', redacted_text)
        else:
            redacted_text = re.sub(pattern, f'[REDACTED_{token_type}]', redacted_text)
            
    return redacted_text

def redact_alert_pii(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively redact sensitive tokens from an alert dictionary.
    Focuses on raw_log and rule_description.
    """
    redacted_data = alert_data.copy()
    
    # Target specific fields for redaction
    fields_to_redact = ['raw_log', 'rule_description']
    
    for field in fields_to_redact:
        if field in redacted_data and isinstance(redacted_data[field], str):
            redacted_data[field] = redact_text(redacted_data[field])
            
    # Also optionally scrub full_log recursively if it exists and is a dict
    if 'full_log' in redacted_data and isinstance(redacted_data['full_log'], dict):
        redacted_data['full_log'] = _redact_dict(redacted_data['full_log'])
        
    return redacted_data

def _redact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to recursively redact a dictionary."""
    redacted = {}
    for k, v in data.items():
        if isinstance(v, str):
            redacted[k] = redact_text(v)
        elif isinstance(v, dict):
            redacted[k] = _redact_dict(v)
        elif isinstance(v, list):
            redacted[k] = [_redact_dict(i) if isinstance(i, dict) else (redact_text(i) if isinstance(i, str) else i) for i in v]
        else:
            redacted[k] = v
    return redacted
