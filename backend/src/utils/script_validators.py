"""
Enhanced script validation and sanitization utilities
"""
import re
import html
import unicodedata
from typing import Tuple, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ScriptValidator:
    """Enhanced script content validator with sanitization capabilities"""

    def __init__(self):
        # Size limits
        self.max_content_length = 51200  # 50KB
        self.max_line_length = 2000
        self.max_lines = 10000

        # Security patterns (more comprehensive)
        self.harmful_patterns = [
            # Script injections
            r'<script[^>]*>.*?</script>',
            r'javascript\s*:',
            r'vbscript\s*:',
            r'data\s*:.*base64',

            # Server-side code
            r'<\?php.*?\?>',
            r'<%.*?%>',
            r'<\?.*?\?>',

            # Shell commands
            r'#!/(?:bin/)?(?:bash|sh|zsh|fish|python|perl)',
            r'\$\(\s*.*\s*\)',
            r'`.*`',

            # Dangerous function calls
            r'(?:exec|eval|system|shell_exec|passthru|proc_open)\s*\(',
            r'(?:import|require|include|include_once|require_once)\s+[\'"]',

            # SQL injection patterns
            r'(?:union|select|insert|update|delete|drop|create|alter)\s+',
            r'--\s*[^\r\n]*',
            r'/\*.*?\*/',

            # Path traversal
            r'\.\./',
            r'\.\.\\',

            # Protocol handlers
            r'(?:file|ftp|mailto|tel|sms)://',
        ]

        # Allowed content types
        self.allowed_content_types = [
            'text/plain',
            'text/markdown',
            'text/csv',
            'application/octet-stream'  # For generic text files
        ]

    def validate_and_sanitize(self, content: str, content_type: str = 'text/plain') -> Tuple[bool, str, List[str]]:
        """
        Validate and sanitize script content
        Returns: (is_valid, sanitized_content, errors)
        """
        errors = []
        sanitized_content = content

        try:
            # Step 1: Basic validation
            basic_errors = self._validate_basic_requirements(content, content_type)
            errors.extend(basic_errors)

            # Step 2: Security validation
            security_errors = self._validate_security(content)
            errors.extend(security_errors)

            # Step 3: Content sanitization (if validation passes basic checks)
            if not errors:
                sanitized_content = self._sanitize_content(content)

                # Step 4: Format validation
                format_errors = self._validate_format(sanitized_content)
                errors.extend(format_errors)

            is_valid = len(errors) == 0

            return is_valid, sanitized_content, errors

        except Exception as e:
            logger.error(f"Error in validate_and_sanitize: {e}")
            return False, content, [f"Validation error: {str(e)}"]

    def _validate_basic_requirements(self, content: str, content_type: str) -> List[str]:
        """Validate basic content requirements"""
        errors = []

        # Check if content exists
        if not content:
            errors.append("Script content cannot be empty")
            return errors

        # Normalize and check again
        normalized_content = content.strip()
        if not normalized_content:
            errors.append("Script content cannot contain only whitespace")
            return errors

        # Check content length
        if len(content) > self.max_content_length:
            errors.append(f"Content exceeds {self.max_content_length // 1024}KB limit "
                         f"({len(content)} characters)")

        # Check content type
        if content_type not in self.allowed_content_types:
            errors.append(f"Invalid content type: {content_type}")

        # Check encoding
        try:
            content.encode('utf-8')
        except UnicodeEncodeError as e:
            errors.append(f"Invalid character encoding: {str(e)}")

        return errors

    def _validate_security(self, content: str) -> List[str]:
        """Enhanced security validation"""
        errors = []

        # Check for harmful patterns
        for pattern in self.harmful_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                errors.append("Content contains potentially harmful code patterns")
                break

        # Check for excessive special characters (possible obfuscation)
        special_char_ratio = sum(1 for c in content if not c.isalnum() and not c.isspace()) / len(content)
        if special_char_ratio > 0.3:  # More than 30% special characters
            errors.append("Content contains excessive special characters")

        # Check for control characters (except common ones)
        control_chars = [c for c in content if ord(c) < 32 and c not in '\n\r\t']
        if control_chars:
            errors.append("Content contains suspicious control characters")

        # Check for potential binary content
        try:
            # Check if content can be properly decoded as text
            content.encode('utf-8').decode('utf-8')
        except UnicodeError:
            errors.append("Content appears to contain binary data")

        return errors

    def _sanitize_content(self, content: str) -> str:
        """Sanitize content while preserving readability"""

        # Step 1: Normalize Unicode
        sanitized = unicodedata.normalize('NFKC', content)

        # Step 2: HTML escape dangerous characters
        sanitized = html.escape(sanitized, quote=False)

        # Step 3: Remove or replace problematic characters
        # Remove control characters except newline, carriage return, and tab
        sanitized = ''.join(char for char in sanitized
                           if ord(char) >= 32 or char in '\n\r\t')

        # Step 4: Normalize line endings
        sanitized = sanitized.replace('\r\n', '\n').replace('\r', '\n')

        # Step 5: Remove excessive whitespace (but preserve intentional formatting)
        lines = sanitized.split('\n')
        cleaned_lines = []

        for line in lines:
            # Remove trailing whitespace but preserve leading indentation
            cleaned_line = line.rstrip()
            cleaned_lines.append(cleaned_line)

        sanitized = '\n'.join(cleaned_lines)

        # Step 6: Remove excessive blank lines (more than 3 consecutive)
        sanitized = re.sub(r'\n{4,}', '\n\n\n', sanitized)

        return sanitized

    def _validate_format(self, content: str) -> List[str]:
        """Validate content format and structure"""
        errors = []

        lines = content.split('\n')

        # Check line count
        if len(lines) > self.max_lines:
            errors.append(f"Content has too many lines ({len(lines)}). Maximum: {self.max_lines}")

        # Check line lengths
        long_lines = [i + 1 for i, line in enumerate(lines) if len(line) > self.max_line_length]
        if long_lines:
            errors.append(f"Lines exceed maximum length ({self.max_line_length} chars): {long_lines[:5]}")

        # Check for reasonable content structure
        non_empty_lines = [line for line in lines if line.strip()]
        if len(non_empty_lines) == 0:
            errors.append("Content contains no meaningful text")

        return errors

    def get_content_analysis(self, content: str) -> Dict[str, Any]:
        """Get detailed content analysis"""
        lines = content.split('\n')
        words = content.split()

        # Character analysis
        char_counts = {
            'total': len(content),
            'alphabetic': sum(1 for c in content if c.isalpha()),
            'numeric': sum(1 for c in content if c.isdigit()),
            'whitespace': sum(1 for c in content if c.isspace()),
            'punctuation': sum(1 for c in content if c in '.,!?;:'),
            'special': sum(1 for c in content if not c.isalnum() and not c.isspace())
        }

        # Language detection patterns
        speaker_patterns = [
            r'^(?:Speaker\s+\d+|[A-Z][a-zA-Z\s]+):\s*',
            r'^\*\*[^*]+\*\*:\s*',
            r'^[A-Z]{2,}:\s*'
        ]

        dialogue_lines = 0
        for pattern in speaker_patterns:
            dialogue_lines += len(re.findall(pattern, content, re.MULTILINE))

        # Quality metrics
        avg_words_per_line = len(words) / len([l for l in lines if l.strip()]) if lines else 0
        reading_time = len(words) / 150  # 150 words per minute

        return {
            'character_analysis': char_counts,
            'line_count': len(lines),
            'word_count': len(words),
            'paragraph_count': len([p for p in content.split('\n\n') if p.strip()]),
            'dialogue_lines': dialogue_lines,
            'avg_words_per_line': round(avg_words_per_line, 2),
            'estimated_reading_time': round(reading_time, 1),
            'has_dialogue_format': dialogue_lines > 0,
            'content_density': round(char_counts['alphabetic'] / char_counts['total'], 3) if char_counts['total'] > 0 else 0
        }

    def validate_file_upload(self, file_content: bytes, filename: str, content_type: str) -> Tuple[bool, str, List[str]]:
        """Validate uploaded file before processing"""
        errors = []

        # Check file size
        if len(file_content) > self.max_content_length:
            errors.append(f"File size exceeds 50KB limit ({len(file_content)} bytes)")

        # Check content type
        if content_type not in self.allowed_content_types:
            errors.append(f"Invalid file type: {content_type}")

        # Check filename
        if not self._is_safe_filename(filename):
            errors.append("Invalid or unsafe filename")

        # Try to decode content
        try:
            content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                # Try common encodings
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    content = file_content.decode(encoding)
                    break
            except UnicodeDecodeError:
                errors.append("File encoding not supported (must be UTF-8 compatible)")
                return False, "", errors

        if errors:
            return False, "", errors

        # Validate the decoded content
        return self.validate_and_sanitize(content, content_type)

    def _is_safe_filename(self, filename: str) -> bool:
        """Check if filename is safe"""
        if not filename:
            return False

        # Check for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False

        # Check for dangerous extensions
        dangerous_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.js', '.vbs', '.jar']
        if any(filename.lower().endswith(ext) for ext in dangerous_extensions):
            return False

        # Check filename length
        if len(filename) > 255:
            return False

        return True


# Global validator instance
script_validator = ScriptValidator()