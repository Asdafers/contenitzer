"""
Redis-based UI component state service for storing and managing UI component states.
Handles form data, component state, and session-tied UI persistence.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from ..lib.redis import RedisService, RedisConfig

logger = logging.getLogger(__name__)

class UIStateServiceError(Exception):
    """Custom exception for UI state service operations"""
    pass

class UIStateService(RedisService):
    """Redis service for UI component state management"""

    def __init__(self):
        """Initialize UI state service with Redis connection"""
        super().__init__(RedisConfig.UI_STATE_PREFIX)
        logger.info("UIStateService initialized")

    def save_component_state(
        self,
        session_id: str,
        component_name: str,
        state_data: Dict[str, Any],
        form_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save UI component state for a session

        Args:
            session_id: Associated session ID
            component_name: Name of the UI component
            state_data: Component state data
            form_data: Form data (if applicable)
            metadata: Additional metadata

        Returns:
            True if save successful, False otherwise

        Raises:
            UIStateServiceError: If state saving fails
        """
        try:
            state_key = f"{session_id}:{component_name}"
            now = datetime.now(timezone.utc).isoformat()

            ui_state = {
                "session_id": session_id,
                "component_name": component_name,
                "state_data": state_data,
                "form_data": form_data or {},
                "metadata": metadata or {},
                "created_at": now,
                "updated_at": now
            }

            # Check if state already exists to preserve created_at
            existing_state = self.get_json(state_key)
            if existing_state:
                ui_state["created_at"] = existing_state.get("created_at", now)

            success = self.set_json(state_key, ui_state, RedisConfig.UI_STATE_TTL)

            if not success:
                raise UIStateServiceError(f"Failed to store UI state for {component_name}")

            logger.debug(f"Saved UI state for component {component_name} in session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save UI component state: {e}")
            raise UIStateServiceError(f"UI state saving failed: {e}")

    def get_component_state(
        self,
        session_id: str,
        component_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve UI component state

        Args:
            session_id: Session ID
            component_name: Name of the UI component

        Returns:
            Component state dictionary or None if not found
        """
        try:
            state_key = f"{session_id}:{component_name}"
            ui_state = self.get_json(state_key)

            if not ui_state:
                logger.debug(f"UI state for component {component_name} not found in session {session_id}")
                return None

            # Extend TTL on access
            self.expire(state_key, RedisConfig.UI_STATE_TTL)

            logger.debug(f"Retrieved UI state for component {component_name} in session {session_id}")
            return ui_state

        except Exception as e:
            logger.error(f"Failed to get UI component state for {component_name}: {e}")
            return None

    def update_component_state(
        self,
        session_id: str,
        component_name: str,
        state_updates: Optional[Dict[str, Any]] = None,
        form_updates: Optional[Dict[str, Any]] = None,
        metadata_updates: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update specific parts of UI component state

        Args:
            session_id: Session ID
            component_name: Name of the UI component
            state_updates: Updates to state_data
            form_updates: Updates to form_data
            metadata_updates: Updates to metadata

        Returns:
            True if update successful, False otherwise
        """
        try:
            state_key = f"{session_id}:{component_name}"
            ui_state = self.get_json(state_key)

            if not ui_state:
                logger.warning(f"UI state for component {component_name} not found for update")
                return False

            # Apply updates
            if state_updates:
                ui_state["state_data"].update(state_updates)

            if form_updates:
                ui_state["form_data"].update(form_updates)

            if metadata_updates:
                ui_state["metadata"].update(metadata_updates)

            # Update timestamp
            ui_state["updated_at"] = datetime.now(timezone.utc).isoformat()

            success = self.set_json(state_key, ui_state, RedisConfig.UI_STATE_TTL)

            if success:
                logger.debug(f"Updated UI state for component {component_name} in session {session_id}")
            else:
                logger.error(f"Failed to update UI state for component {component_name}")

            return success

        except Exception as e:
            logger.error(f"Failed to update UI component state: {e}")
            return False

    def delete_component_state(
        self,
        session_id: str,
        component_name: str
    ) -> bool:
        """
        Delete UI component state

        Args:
            session_id: Session ID
            component_name: Name of the UI component

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            state_key = f"{session_id}:{component_name}"
            success = self.delete(state_key)

            if success:
                logger.info(f"Deleted UI state for component {component_name} in session {session_id}")
            else:
                logger.warning(f"UI state for component {component_name} not found for deletion")

            return success

        except Exception as e:
            logger.error(f"Failed to delete UI component state: {e}")
            return False

    def get_session_ui_states(
        self,
        session_id: str,
        component_prefix: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get all UI component states for a session

        Args:
            session_id: Session ID
            component_prefix: Optional prefix to filter components

        Returns:
            Dictionary mapping component names to their states
        """
        try:
            pattern = f"{session_id}:*"
            if component_prefix:
                pattern = f"{session_id}:{component_prefix}*"

            matching_keys = self.get_keys_by_pattern(pattern)
            ui_states = {}

            for key in matching_keys:
                # Extract component name from key (remove session_id prefix)
                component_name = key.replace(f"{session_id}:", "")
                ui_state = self.get_json(key)

                if ui_state:
                    ui_states[component_name] = ui_state

            logger.debug(f"Retrieved {len(ui_states)} UI states for session {session_id}")
            return ui_states

        except Exception as e:
            logger.error(f"Failed to get session UI states for {session_id}: {e}")
            return {}

    def clear_session_ui_states(self, session_id: str) -> int:
        """
        Clear all UI component states for a session

        Args:
            session_id: Session ID

        Returns:
            Number of component states cleared
        """
        try:
            pattern = f"{session_id}:*"
            matching_keys = self.get_keys_by_pattern(pattern)
            cleared_count = 0

            for key in matching_keys:
                if self.delete(key):
                    cleared_count += 1

            logger.info(f"Cleared {cleared_count} UI states for session {session_id}")
            return cleared_count

        except Exception as e:
            logger.error(f"Failed to clear UI states for session {session_id}: {e}")
            return 0

    def save_form_data(
        self,
        session_id: str,
        component_name: str,
        form_data: Dict[str, Any]
    ) -> bool:
        """
        Convenience method to save only form data for a component

        Args:
            session_id: Session ID
            component_name: Name of the UI component
            form_data: Form data to save

        Returns:
            True if save successful, False otherwise
        """
        try:
            existing_state = self.get_component_state(session_id, component_name)

            if existing_state:
                # Update existing state
                return self.update_component_state(
                    session_id,
                    component_name,
                    form_updates=form_data
                )
            else:
                # Create new state with form data
                return self.save_component_state(
                    session_id,
                    component_name,
                    state_data={},
                    form_data=form_data
                )

        except Exception as e:
            logger.error(f"Failed to save form data for component {component_name}: {e}")
            return False

    def get_form_data(
        self,
        session_id: str,
        component_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Convenience method to get only form data for a component

        Args:
            session_id: Session ID
            component_name: Name of the UI component

        Returns:
            Form data dictionary or None if not found
        """
        try:
            ui_state = self.get_component_state(session_id, component_name)

            if not ui_state:
                return None

            return ui_state.get("form_data", {})

        except Exception as e:
            logger.error(f"Failed to get form data for component {component_name}: {e}")
            return None

    def save_workflow_ui_state(
        self,
        session_id: str,
        workflow_step: str,
        ui_data: Dict[str, Any]
    ) -> bool:
        """
        Save UI state for a specific workflow step

        Args:
            session_id: Session ID
            workflow_step: Name of workflow step
            ui_data: UI state data for the step

        Returns:
            True if save successful, False otherwise
        """
        try:
            component_name = f"workflow_{workflow_step}"
            return self.save_component_state(
                session_id,
                component_name,
                state_data=ui_data,
                metadata={"workflow_step": workflow_step}
            )

        except Exception as e:
            logger.error(f"Failed to save workflow UI state for step {workflow_step}: {e}")
            return False

    def get_workflow_ui_states(self, session_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Get all workflow-related UI states for a session

        Args:
            session_id: Session ID

        Returns:
            Dictionary mapping workflow steps to their UI states
        """
        try:
            workflow_states = self.get_session_ui_states(session_id, "workflow_")

            # Clean up the keys to remove "workflow_" prefix
            cleaned_states = {}
            for component_name, state in workflow_states.items():
                step_name = component_name.replace("workflow_", "")
                cleaned_states[step_name] = state

            logger.debug(f"Retrieved {len(cleaned_states)} workflow UI states for session {session_id}")
            return cleaned_states

        except Exception as e:
            logger.error(f"Failed to get workflow UI states for session {session_id}: {e}")
            return {}

    def cleanup_expired_ui_states(self) -> int:
        """
        Clean up expired UI component states

        Returns:
            Number of states cleaned up
        """
        try:
            all_keys = self.get_keys_by_pattern("*")
            cleaned_count = 0

            for key in all_keys:
                if not self.exists(key):
                    cleaned_count += 1

            logger.info(f"Cleaned up {cleaned_count} expired UI states")
            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup expired UI states: {e}")
            return 0

# Global service instance
_ui_state_service: Optional[UIStateService] = None

def get_ui_state_service() -> UIStateService:
    """Get global UI state service instance"""
    global _ui_state_service

    if _ui_state_service is None:
        _ui_state_service = UIStateService()

    return _ui_state_service