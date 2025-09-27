"""
Custom Media Service for managing user-selected media assets in content plans.
Handles adding, updating, and removing custom media files from content planning workflow.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
from sqlalchemy.orm import Session

from .media_browsing_service import MediaBrowsingService
from ..lib.exceptions import MediaBrowsingError, ContentPlanningError
from ..lib.database import get_db_session


logger = logging.getLogger(__name__)


class CustomMediaService:
    """Service for managing custom media assets in content plans"""

    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize CustomMediaService.

        Args:
            db_session: Optional database session
        """
        self.db = db_session or get_db_session()
        self.media_browser = MediaBrowsingService()

    async def add_custom_media(
        self,
        plan_id: str,
        file_path: str,
        description: str,
        usage_intent: str,
        scene_association: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add custom media file to content plan.

        Args:
            plan_id: Content plan ID
            file_path: Path to media file relative to media root
            description: User description of the asset
            usage_intent: How the asset will be used (background, overlay, etc.)
            scene_association: Optional scene/segment association

        Returns:
            Dictionary with custom media asset information

        Raises:
            MediaBrowsingError: If file is invalid or unsupported
            ContentPlanningError: If plan doesn't exist or file already selected
        """
        try:
            # Validate content plan exists
            await self._validate_content_plan(plan_id)

            # Validate and get file information
            file_info = await self.validate_media_file(file_path)

            # Check if file is already selected for this plan
            if await self._is_file_already_selected(plan_id, file_path):
                raise ContentPlanningError("File already selected for this plan")

            # Create custom media asset record
            asset_id = str(uuid.uuid4())
            selected_at = datetime.utcnow().isoformat()

            custom_asset = {
                "id": asset_id,
                "plan_id": plan_id,
                "file_path": file_path,
                "description": description,
                "usage_intent": usage_intent,
                "scene_association": scene_association,
                "file_info": file_info.dict(),
                "selected_at": selected_at,
                "updated_at": selected_at
            }

            # Store in database (implementation depends on your storage strategy)
            await self._store_custom_media_asset(custom_asset)

            # Update content plan to include custom media
            await self._update_content_plan_with_custom_media(plan_id, custom_asset)

            logger.info(f"Added custom media {asset_id} to plan {plan_id}: {file_path}")
            return custom_asset

        except (MediaBrowsingError, ContentPlanningError):
            raise
        except Exception as e:
            logger.error(f"Error adding custom media to plan {plan_id}: {e}")
            raise ContentPlanningError(f"Failed to add custom media: {e}")

    async def update_custom_media(
        self,
        plan_id: str,
        asset_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update custom media asset in content plan.

        Args:
            plan_id: Content plan ID
            asset_id: Custom media asset ID
            updates: Dictionary of fields to update

        Returns:
            Updated custom media asset

        Raises:
            ContentPlanningError: If plan or asset doesn't exist
            MediaBrowsingError: If new file path is invalid
        """
        try:
            # Validate content plan exists
            await self._validate_content_plan(plan_id)

            # Get existing asset
            existing_asset = await self._get_custom_media_asset(plan_id, asset_id)
            if not existing_asset:
                raise ContentPlanningError(f"Custom media asset {asset_id} not found")

            # Validate updates
            validated_updates = await self._validate_updates(updates)

            if not validated_updates:
                raise ContentPlanningError("No fields to update")

            # If file_path is being updated, validate new file
            if 'file_path' in validated_updates:
                new_file_path = validated_updates['file_path']
                if new_file_path != existing_asset['file_path']:
                    # Check if new file is already selected
                    if await self._is_file_already_selected(plan_id, new_file_path):
                        raise ContentPlanningError("New file already selected for this plan")

                    # Validate new file and update file_info
                    file_info = await self.validate_media_file(new_file_path)
                    validated_updates['file_info'] = file_info.dict()

            # Apply updates
            validated_updates['updated_at'] = datetime.utcnow().isoformat()
            updated_asset = {**existing_asset, **validated_updates}

            # Store updated asset
            await self._update_custom_media_asset(updated_asset)

            # Update content plan
            await self._update_content_plan_with_custom_media(plan_id, updated_asset)

            logger.info(f"Updated custom media {asset_id} in plan {plan_id}")
            return updated_asset

        except (MediaBrowsingError, ContentPlanningError):
            raise
        except Exception as e:
            logger.error(f"Error updating custom media {asset_id} in plan {plan_id}: {e}")
            raise ContentPlanningError(f"Failed to update custom media: {e}")

    async def remove_custom_media(self, plan_id: str, asset_id: str) -> bool:
        """
        Remove custom media asset from content plan.

        Args:
            plan_id: Content plan ID
            asset_id: Custom media asset ID

        Returns:
            True if asset was removed, False if not found

        Raises:
            ContentPlanningError: If plan doesn't exist or removal fails
        """
        try:
            # Validate content plan exists
            await self._validate_content_plan(plan_id)

            # Check if asset exists
            existing_asset = await self._get_custom_media_asset(plan_id, asset_id)
            if not existing_asset:
                raise ContentPlanningError(f"Custom media asset {asset_id} not found")

            # Remove from database
            await self._delete_custom_media_asset(plan_id, asset_id)

            # Update content plan to remove custom media
            await self._remove_custom_media_from_content_plan(plan_id, asset_id)

            logger.info(f"Removed custom media {asset_id} from plan {plan_id}")
            return True

        except ContentPlanningError:
            raise
        except Exception as e:
            logger.error(f"Error removing custom media {asset_id} from plan {plan_id}: {e}")
            raise ContentPlanningError(f"Failed to remove custom media: {e}")

    async def get_custom_media_assets(self, plan_id: str) -> List[Dict[str, Any]]:
        """
        Get all custom media assets for a content plan.

        Args:
            plan_id: Content plan ID

        Returns:
            List of custom media assets

        Raises:
            ContentPlanningError: If plan doesn't exist
        """
        try:
            await self._validate_content_plan(plan_id)
            assets = await self._get_all_custom_media_assets(plan_id)
            logger.info(f"Retrieved {len(assets)} custom media assets for plan {plan_id}")
            return assets

        except ContentPlanningError:
            raise
        except Exception as e:
            logger.error(f"Error getting custom media assets for plan {plan_id}: {e}")
            raise ContentPlanningError(f"Failed to get custom media assets: {e}")

    async def validate_media_file(self, file_path: str) -> Any:
        """
        Validate media file and return file information.

        Args:
            file_path: Path to media file

        Returns:
            MediaFileInfo object

        Raises:
            MediaBrowsingError: If file is invalid or unsupported
        """
        file_info = await self.media_browser.get_file_info(file_path)
        if not file_info:
            raise MediaBrowsingError(f"File not found or unsupported: {file_path}")

        # Additional validation for supported formats in content planning
        if file_info.format not in self._get_supported_formats():
            raise MediaBrowsingError(f"Unsupported file format: .{file_info.format}")

        return file_info

    def _get_supported_formats(self) -> set:
        """Get formats supported for content planning"""
        # Based on user requirements: JPG, PNG, MP4
        return {'jpg', 'jpeg', 'png', 'mp4'}

    async def _validate_content_plan(self, plan_id: str) -> None:
        """Validate that content plan exists"""
        # This would check against your content planning service
        # For now, assume validation passes if plan_id is valid UUID format
        try:
            uuid.UUID(plan_id)
        except ValueError:
            raise ContentPlanningError(f"Invalid plan ID format: {plan_id}")

        # In real implementation, check if plan exists in database
        # plan = await self._get_content_plan(plan_id)
        # if not plan:
        #     raise ContentPlanningError(f"Content plan {plan_id} not found")

    async def _validate_updates(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Validate update fields"""
        allowed_fields = {
            'file_path', 'description', 'usage_intent', 'scene_association'
        }

        validated = {}
        for key, value in updates.items():
            if key in allowed_fields and value is not None:
                # Basic validation
                if key in ['description', 'usage_intent'] and not isinstance(value, str):
                    continue
                if key == 'file_path' and not isinstance(value, str):
                    continue
                validated[key] = value

        return validated

    async def _is_file_already_selected(self, plan_id: str, file_path: str) -> bool:
        """Check if file is already selected for this plan"""
        # This would query your database to check for existing selection
        # For now, return False (no duplicates)
        return False

    async def _store_custom_media_asset(self, asset: Dict[str, Any]) -> None:
        """Store custom media asset in database"""
        # Implementation depends on your database schema
        # This could store in a custom_media_assets table
        logger.debug(f"Storing custom media asset: {asset['id']}")

    async def _get_custom_media_asset(self, plan_id: str, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get custom media asset from database"""
        # Implementation depends on your database schema
        logger.debug(f"Getting custom media asset {asset_id} for plan {plan_id}")
        return None

    async def _update_custom_media_asset(self, asset: Dict[str, Any]) -> None:
        """Update custom media asset in database"""
        logger.debug(f"Updating custom media asset: {asset['id']}")

    async def _delete_custom_media_asset(self, plan_id: str, asset_id: str) -> None:
        """Delete custom media asset from database"""
        logger.debug(f"Deleting custom media asset {asset_id} from plan {plan_id}")

    async def _get_all_custom_media_assets(self, plan_id: str) -> List[Dict[str, Any]]:
        """Get all custom media assets for a plan"""
        logger.debug(f"Getting all custom media assets for plan {plan_id}")
        return []

    async def _update_content_plan_with_custom_media(self, plan_id: str, asset: Dict[str, Any]) -> None:
        """Update content plan to include custom media asset"""
        # This would integrate with EnhancedContentPlanner to update the plan
        logger.debug(f"Updating content plan {plan_id} with custom media {asset['id']}")

    async def _remove_custom_media_from_content_plan(self, plan_id: str, asset_id: str) -> None:
        """Remove custom media from content plan"""
        logger.debug(f"Removing custom media {asset_id} from content plan {plan_id}")