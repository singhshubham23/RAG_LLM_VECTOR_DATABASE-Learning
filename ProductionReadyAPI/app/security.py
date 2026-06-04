import re
from typing import Optional, Tuple
from langsmith import traceable


class InputSanitizer:
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"forget\s+(all\s+)?previous",
        r"new\s+instructions\s*:",
        r"system\s*prompt",
        r"---\s*end\s*(of)?\s*prompt",
        r"pretend\s+you\s+are",
        r"act\s+as\s+(if\s+)?you",
        r"bypass\s+(all\s+)?restrictions",
        r"reveal\s+(your|the)\s+(system|instructions|prompt)",
        r"you\s+are\s+now\s+(DAN|jailbroken)",
    ]

    def __init__(self):
        # Pre-compile for speed
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS]

    @traceable(name="input_security_check")
    def check(self, text: str) -> Tuple[bool, Optional[str]]:
        """Verify if the input is safe."""
        for pattern in self.patterns:
            if pattern.search(text):
                return False, f"Potential prompt injection detected."
        return True, None

    def sanitize(self, text: str) -> str:
        """
        Basic normalization.
        Note: Use this for formatting, but rely on .check() for security.
        """
        # Normalize whitespace (replace multiple spaces/newlines with one space)
        text = re.sub(r"\s+", " ", text)
        # Remove common template injection markers
        text = text.replace("{{", "").replace("}}", "")
        return text.strip()


class PIIDetector:
    # Placeholder for future PII detection logic
    PATTERNS = {
        "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "phone": re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b\d{3}[-.\s]?\d{4}\b"),
        "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "credit_card": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    }

    MASK_MAP = {
        "email": "[EMAIL REDACTED]",
        "phone": "[PHONE REDACTED]",
        "ssn": "[SSN REDACTED]",
        "credit_card": "[CREDIT_CARD REDACTED]",
    }

    def detect(self, text: str) -> dict:
        """Detect PII in the text."""
        found = {}
        for key, pattern in self.PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                found[key] = matches
        return found
    
    def mask(self, text: str) -> str:
        """Mask detected PII in the text."""
        masked = text
        for pii_type, pattern in self.PATTERNS.items():
            masked = pattern.sub(self.MASK_MAP[pii_type], masked)
        return masked


class OutputValidator:
    """Simple output validator to ensure generated text is safe to return."""
    FORBIDDEN_PATTERNS = [
        re.compile(r"\b(ssn|social security number)\b", re.IGNORECASE),
        re.compile(r"\b(password|credit card|cvv)\b", re.IGNORECASE),
    ]

    def validate(self, text: str) -> Tuple[bool, Optional[str]]:
        for p in self.FORBIDDEN_PATTERNS:
            if p.search(text):
                return False, "Output contains sensitive content"
        return True, None



class SecurityPipeline:
    """
    Full Security Pipeline that processes input and output.
    This is a single class you wire into your API.
    """
    def __init__(self):
        self.sanitizer = InputSanitizer()
        self.pii_detector = PIIDetector()
        self.output_validator = OutputValidator()

    @traceable(name="security_check_input")
    def process_input(self, text: str) -> Tuple[bool, str, Optional[str]]:
        """
        Runs full input security suite.
        Returns: (is_safe, processed_text, error_message)
        """
        # 1. Check for prompt injection
        is_safe, error = self.sanitizer.check(text)
        if not is_safe:
            return False, text, error

        # 2. Mask PII (Privacy)
        masked_text = self.pii_detector.mask(text)

        # 3. Clean formatting (Sanitize)
        final_text = self.sanitizer.sanitize(masked_text)

        return True, final_text, None

    @traceable(name="security_check_output")
    def process_output(self, llm_response: str) -> Tuple[bool, str, Optional[str]]:
        """
        Runs checks on the LLM's response before it reaches the user.
        """
        # 1. Validate against forbidden patterns (leak prevention)
        is_valid, error = self.output_validator.validate(llm_response)
        if not is_valid:
            # In production, we usually return a generic refusal rather than the leaked data
            return False, "Response blocked: Sensitive content detected.", error

        # 2. Final check for any PII the LLM might have hallucinated
        final_output = self.pii_detector.mask(llm_response)

        return True, final_output, None