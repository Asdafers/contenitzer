"""
Redis-based session management service for storing user sessions and workflow state.
Handles user preferences, API keys with encryption, and workflow tracking.
"""
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from ..lib.redis import RedisService, RedisConfig
from ..lib.encryption import encrypt_api_key, decrypt_api_key, ensure_api_key_encrypted

logger = logging.getLogger(__name__)

class SessionServiceError(Exception):
    """Custom exception for session service operations"""
    pass

class SessionService(RedisService):
    """Redis service for user session management"""

    def __init__(self):
        """Initialize session service with Redis connection"""
        super().__init__(RedisConfig.SESSION_PREFIX)
        logger.info("SessionService initialized")

    def create_session(self, preferences: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new user session with optional preferences

        Args:
            preferences: User preferences dictionary

        Returns:
            session_id: New session UUID

        Raises:
            SessionServiceError: If session creation fails
        """
        try:
            session_id = str(uuid.uuid4())
            session_data = {
                "session_id": session_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "preferences": preferences or {},
                "workflow_state": {
                    "current_step": None,
                    "completed_steps": [],
                    "step_data": {}
                },
                "active": True
            }

            # Encrypt API keys in preferences if present
            session_data = self._encrypt_sensitive_data(session_data)

            success = self.set_json(session_id, session_data, RedisConfig.SESSION_TTL)

            if not success:
                raise SessionServiceError(f"Failed to store session data for {session_id}")

            logger.info(f"Created session {session_id}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise SessionServiceError(f"Session creation failed: {e}")

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data by ID

        Args:
            session_id: Session UUID

        Returns:
            Session data dictionary or None if not found
        """
        try:
            session_data = self.get_json(session_id)

            if not session_data:
                logger.debug(f"Session {session_id} not found")
                return None

            # Decrypt sensitive data
            session_data = self._decrypt_sensitive_data(session_data)

            # Extend TTL on access
            self.expire(session_id, RedisConfig.SESSION_TTL)

            logger.debug(f"Retrieved session {session_id}")
            return session_data

        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update session data with new values

        Args:
            session_id: Session UUID
            updates: Dictionary of updates to apply

        Returns:
            True if update successful, False otherwise
        """
        try:
            session_data = self.get_json(session_id)

            if not session_data:
                logger.warning(f"Session {session_id} not found for update")
                return False

            # Merge updates
            if "preferences" in updates:
                session_data["preferences"].update(updates["preferences"])
            if "workflow_state" in updates:
                session_data["workflow_state"].update(updates["workflow_state"])

            # Update timestamp
            session_data["updated_at"] = datetime.now(timezone.utc).isoformat()

            # Apply any other updates
            for key, value in updates.items():
                if key not in ["preferences", "workflow_state"]:
                    session_data[key] = value

            # Encrypt sensitive data
            session_data = self._encrypt_sensitive_data(session_data)

            success = self.set_json(session_id, session_data, RedisConfig.SESSION_TTL)

            if success:
                logger.info(f"Updated session {session_id}")
            else:
                logger.error(f"Failed to update session {session_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """
        Delete session and all associated data

        Args:
            session_id: Session UUID

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            success = self.delete(session_id)

            if success:
                logger.info(f"Deleted session {session_id}")
            else:
                logger.warning(f"Session {session_id} not found for deletion")

            return success

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def get_workflow_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get workflow state for session

        Args:
            session_id: Session UUID

        Returns:
            Workflow state dictionary or None if not found
        """
        try:
            session_data = self.get_session(session_id)

            if not session_data:
                return None

            return session_data.get("workflow_state")

        except Exception as e:
            logger.error(f"Failed to get workflow state for {session_id}: {e}")
            return None

    def update_workflow_state(self, session_id: str, workflow_state: Dict[str, Any]) -> bool:
        """
        Update workflow state for session

        Args:
            session_id: Session UUID
            workflow_state: New workflow state

        Returns:
            True if update successful, False otherwise
        """
        try:
            return self.update_session(session_id, {"workflow_state": workflow_state})

        except Exception as e:
            logger.error(f"Failed to update workflow state for {session_id}: {e}")
            return False

    def list_active_sessions(self) -> List[str]:
        """
        Get list of active session IDs

        Returns:
            List of active session IDs
        """
        try:
            all_keys = self.get_keys_by_pattern("*")
            active_sessions = []

            for session_id in all_keys:
                session_data = self.get_json(session_id)
                if session_data and session_data.get("active", True):
                    active_sessions.append(session_id)

            logger.debug(f"Found {len(active_sessions)} active sessions")
            return active_sessions

        except Exception as e:
            logger.error(f"Failed to list active sessions: {e}")
            return []

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions (for manual cleanup)

        Returns:
            Number of sessions cleaned up
        """
        try:
            all_keys = self.get_keys_by_pattern("*")
            cleaned_count = 0

            for session_id in all_keys:
                if not self.exists(session_id):
                    cleaned_count += 1

            logger.info(f"Cleaned up {cleaned_count} expired sessions")
            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0

    def _encrypt_sensitive_data(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive data in session (API keys)

        Args:
            session_data: Session data dictionary

        Returns:
            Session data with encrypted sensitive fields
        """
        try:
            # Create a copy to avoid modifying original
            encrypted_data = session_data.copy()

            # Encrypt API keys in preferences
            preferences = encrypted_data.get("preferences", {})
            for key in ["youtube_api_key", "openai_api_key", "gemini_api_key"]:
                if key in preferences and preferences[key]:
                    preferences[key] = ensure_api_key_encrypted(preferences[key])

            encrypted_data["preferences"] = preferences
            return encrypted_data

        except Exception as e:
            logger.error(f"Failed to encrypt sensitive data: {e}")
            return session_data

    def _decrypt_sensitive_data(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt sensitive data in session (API keys)

        Args:
            session_data: Session data with encrypted fields

        Returns:
            Session data with decrypted sensitive fields
        """
        try:
            # Create a copy to avoid modifying original
            decrypted_data = session_data.copy()

            # Decrypt API keys in preferences
            preferences = decrypted_data.get("preferences", {})
            for key in ["youtube_api_key", "openai_api_key", "gemini_api_key"]:
                if key in preferences and preferences[key]:
                    try:
                        preferences[key] = decrypt_api_key(preferences[key])
                    except Exception as decrypt_error:
                        logger.warning(f"Failed to decrypt {key}: {decrypt_error}")
                        # Keep encrypted value if decryption fails

            decrypted_data["preferences"] = preferences
            return decrypted_data

        except Exception as e:
            logger.error(f"Failed to decrypt sensitive data: {e}")
            return session_data

# Global service instance
_session_service: Optional[SessionService] = None

def get_session_service() -> SessionService:
    """Get global session service instance"""
    global _session_service

    if _session_service is None:
        _session_service = SessionService()

    return _session_service