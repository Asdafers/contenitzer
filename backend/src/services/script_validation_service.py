from typing import List, Tuple, Optional, Dict, Any
import re
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from ..models.uploaded_script import UploadedScript, ValidationStatusEnum
from ..lib.database import get_db_session

logger = logging.getLogger(__name__)


class ScriptValidationService:
    """Service for validating script content and format"""

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

        # Validation rules and patterns
        self.max_content_length = 51200  # 50KB in characters
        self.min_content_length = 1
        self.allowed_content_types = ['text/plain', 'text/markdown', 'text/txt']

        # Patterns for potentially harmful content
        self.harmful_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'<\?php.*?\?>',              # PHP tags
            r'#!/(?:bin/)?(?:bash|sh|zsh|fish)',  # Shell script shebangs
            r'import\s+os\s*;',           # Suspicious Python imports
            r'exec\s*\(',                 # Exec calls
            r'eval\s*\(',                 # Eval calls
            r'subprocess\.',              # Subprocess calls
            r'system\s*\(',               # System calls
        ]

    def _get_session(self) -> Session:
        """Get database session"""
        if self.db_session:
            return self.db_session
        return next(get_db_session())

    def validate_content(self, content: str, content_type: str = "text/plain") -> Tuple[bool, List[str]]:
        """Validate script content and return validation result"""
        errors = []

        # Basic content validation
        errors.extend(self._validate_basic_content(content))

        # Content type validation
        errors.extend(self._validate_content_type(content_type))

        # Security validation
        errors.extend(self._validate_security(content))

        # Format validation
        errors.extend(self._validate_format(content))

        is_valid = len(errors) == 0

        if is_valid:
            logger.info("Script content validation passed")
        else:
            logger.warning(f"Script content validation failed: {errors}")

        return is_valid, errors

    def _validate_basic_content(self, content: str) -> List[str]:
        """Validate basic content requirements"""
        errors = []

        # Check if content exists and is not empty
        if not content or not content.strip():
            errors.append("Script content cannot be empty")
            return errors

        # Check content length
        content_length = len(content)
        if content_length > self.max_content_length:
            errors.append(f"Script content exceeds {self.max_content_length // 1024}KB limit "
                         f"(current: {content_length} characters)")

        if content_length < self.min_content_length:
            errors.append(f"Script content too short (minimum: {self.min_content_length} character)")

        return errors

    def _validate_content_type(self, content_type: str) -> List[str]:
        """Validate content type"""
        errors = []

        if content_type not in self.allowed_content_types:
            errors.append(f"Invalid content type: {content_type}. "
                         f"Allowed types: {', '.join(self.allowed_content_types)}")

        return errors

    def _validate_security(self, content: str) -> List[str]:
        """Validate content for security issues"""
        errors = []

        # Check for potentially harmful patterns
        for pattern in self.harmful_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                errors.append("Script content contains potentially harmful code")
                break

        # Check for binary content (non-UTF-8)
        try:
            content.encode('utf-8')
        except UnicodeEncodeError:
            errors.append("Script content contains invalid characters (non-UTF-8)")

        return errors

    def _validate_format(self, content: str) -> List[str]:
        """Validate content format and structure"""
        errors = []

        # Check for reasonable line lengths (optional warning)
        lines = content.split('\n')
        max_line_length = 1000  # characters per line

        long_lines = [i + 1 for i, line in enumerate(lines) if len(line) > max_line_length]
        if long_lines:
            errors.append(f"Some lines are very long (>{max_line_length} chars). "
                         f"Consider breaking them up. Lines: {long_lines[:5]}")

        # Check for reasonable number of lines
        if len(lines) > 10000:
            errors.append(f"Script has too many lines ({len(lines)}). Maximum recommended: 10,000")

        return errors

    def validate_script_structure(self, content: str) -> Tuple[bool, Dict[str, Any]]:
        """Validate and analyze script structure"""
        analysis = {
            "total_characters": len(content),
            "total_lines": content.count('\n') + 1,
            "total_words": len(content.split()),
            "speaker_count": 0,
            "estimated_duration_seconds": 0,
            "has_dialogue": False,
            "structure_issues": []
        }

        # Detect speakers (basic pattern matching)
        speaker_pattern = r'^(?:Speaker\s+\d+|[A-Z][a-zA-Z\s]+):\s+'
        speaker_matches = re.findall(speaker_pattern, content, re.MULTILINE)
        unique_speakers = set(speaker_matches)
        analysis["speaker_count"] = len(unique_speakers)
        analysis["has_dialogue"] = len(unique_speakers) > 1

        # Estimate duration (rough calculation: ~150 words per minute)
        words_per_minute = 150
        analysis["estimated_duration_seconds"] = (analysis["total_words"] / words_per_minute) * 60

        # Check for potential structure issues
        if analysis["speaker_count"] == 0:
            analysis["structure_issues"].append("No speakers detected. Consider using 'Speaker 1:', 'Speaker 2:' format")

        if analysis["total_words"] < 50:
            analysis["structure_issues"].append("Script appears very short for meaningful content")

        if analysis["estimated_duration_seconds"] < 60:
            analysis["structure_issues"].append("Estimated duration is less than 1 minute")

        is_well_structured = len(analysis["structure_issues"]) == 0
        return is_well_structured, analysis

    def validate_uploaded_script(self, script_id: str) -> Tuple[bool, str]:
        """Validate an uploaded script and update its status"""
        try:
            session = self._get_session()

            script = session.query(UploadedScript).filter(
                UploadedScript.id == script_id
            ).first()

            if not script:
                return False, "Script not found"

            # Validate content
            is_valid, errors = self.validate_content(script.content, script.content_type)

            # Update validation status
            if is_valid:
                script.validation_status = ValidationStatusEnum.VALID
                message = "Script validation passed"
            else:
                script.validation_status = ValidationStatusEnum.INVALID
                message = f"Validation failed: {'; '.join(errors)}"

            script.updated_at = datetime.utcnow()
            session.commit()

            logger.info(f"Validated script {script_id}: {message}")
            return is_valid, message

        except Exception as e:
            logger.error(f"Error validating script {script_id}: {e}")
            session.rollback() if session else None
            return False, f"Validation error: {str(e)}"

    def get_validation_report(self, content: str, content_type: str = "text/plain") -> Dict[str, Any]:
        """Get comprehensive validation report for content"""
        # Basic validation
        is_valid, errors = self.validate_content(content, content_type)

        # Structure analysis
        is_well_structured, structure_analysis = self.validate_script_structure(content)

        # Content quality metrics
        quality_metrics = self._calculate_quality_metrics(content)

        return {
            "is_valid": is_valid,
            "is_well_structured": is_well_structured,
            "errors": errors,
            "structure_analysis": structure_analysis,
            "quality_metrics": quality_metrics,
            "validation_timestamp": datetime.utcnow().isoformat()
        }

    def _calculate_quality_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate content quality metrics"""
        lines = content.split('\n')
        words = content.split()

        # Character distribution
        char_counts = {
            "alphabetic": sum(1 for c in content if c.isalpha()),
            "numeric": sum(1 for c in content if c.isdigit()),
            "whitespace": sum(1 for c in content if c.isspace()),
            "special": sum(1 for c in content if not c.isalnum() and not c.isspace())
        }

        # Line statistics
        line_lengths = [len(line) for line in lines]
        avg_line_length = sum(line_lengths) / len(line_lengths) if line_lengths else 0

        # Word statistics
        word_lengths = [len(word) for word in words]
        avg_word_length = sum(word_lengths) / len(word_lengths) if word_lengths else 0

        return {
            "character_distribution": char_counts,
            "average_line_length": round(avg_line_length, 2),
            "average_word_length": round(avg_word_length, 2),
            "longest_line": max(line_lengths) if line_lengths else 0,
            "empty_lines": sum(1 for line in lines if not line.strip()),
            "readability_score": self._calculate_readability_score(words, lines)
        }

    def _calculate_readability_score(self, words: List[str], lines: List[str]) -> float:
        """Calculate a simple readability score (0-100)"""
        if not words or not lines:
            return 0.0

        # Simple metrics for readability
        avg_words_per_line = len(words) / len([l for l in lines if l.strip()])
        avg_chars_per_word = sum(len(w) for w in words) / len(words)

        # Ideal ranges: 10-15 words per line, 4-6 characters per word
        word_score = max(0, 100 - abs(avg_words_per_line - 12.5) * 4)
        char_score = max(0, 100 - abs(avg_chars_per_word - 5) * 10)

        return round((word_score + char_score) / 2, 1)