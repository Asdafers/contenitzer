"""
Enhanced Content Planner Service - Comprehensive script analysis for hybrid video generation.
Uses Gemini to intelligently determine both image and video asset requirements.
"""

import logging
import uuid
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

from .gemini_service import GeminiService
from .script_analysis_service import ScriptAnalysisService
from ..lib.exceptions import ContentPlanningError
from ..models.generation_plan import GenerationPlan as GenerationPlanDB, PlanStatusEnum

logger = logging.getLogger(__name__)


class EnhancedContentPlanner:
    """Service for comprehensive content planning using AI analysis."""

    def __init__(self):
        self.gemini_service = GeminiService(api_key=os.getenv('GEMINI_API_KEY', 'test-key'))
        self.script_analyzer = ScriptAnalysisService()

    async def analyze_script_content(
        self,
        script_text: str,
        target_duration: int = 180,
        quality_level: str = "high",
        style_preference: str = "professional",
        include_motion: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze script using Gemini to determine content structure and asset requirements.

        Returns comprehensive analysis including scene breakdown and asset type decisions.
        """
        try:
            logger.info(f"Analyzing script content, target duration: {target_duration}s")

            # Use Gemini to analyze script and determine scene structure
            analysis_prompt = f"""
            Analyze this script for video production planning:

            Script: {script_text}

            Target duration: {target_duration} seconds
            Style: {style_preference}
            Include motion: {include_motion}

            For each scene, determine:
            1. Whether it needs a STATIC IMAGE or DYNAMIC VIDEO
            2. Scene duration and timing
            3. Visual description and style
            4. Text content and positioning

            Return JSON with:
            {{
                "total_duration": {target_duration},
                "scene_count": number,
                "scenes": [
                    {{
                        "index": 0,
                        "text": "scene text",
                        "start_time": 0.0,
                        "duration": 15.0,
                        "asset_type": "image" or "video",
                        "visual_description": "detailed description",
                        "style": "visual style",
                        "complexity": "simple/medium/complex"
                    }}
                ],
                "quality_score": 0.85
            }}
            """

            # Generate analysis using Gemini text model
            logger.info(f"📤 Calling Gemini for script analysis - Prompt: {len(analysis_prompt)} chars")
            gemini_result = await self.gemini_service.generate_with_fallback(
                prompt=analysis_prompt,
                preferred_model="gemini-2.5-flash",
                fallback_model="gemini-2.5-pro"
            )
            logger.info(f"📥 Gemini response received - Content: {len(gemini_result.get('content', ''))} chars, Model: {gemini_result.get('model_used', 'unknown')}")

            # Parse Gemini response for scene analysis
            analysis = self._parse_script_analysis(
                gemini_result.get("content", ""),
                script_text,
                target_duration
            )

            logger.info(f"Script analysis complete: {analysis['scene_count']} scenes identified")
            return analysis

        except Exception as e:
            logger.error(f"Script analysis failed: {e}")
            raise ContentPlanningError(f"Failed to analyze script content: {e}")

    async def create_asset_plan(
        self,
        analysis: Dict[str, Any],
        budget_limit: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Create detailed asset generation plan based on script analysis.

        Determines specific images and videos needed, with cost estimates.
        """
        try:
            logger.info("Creating detailed asset generation plan")

            images = []
            videos = []
            transitions = []

            for scene in analysis["scenes"]:
                asset_id = str(uuid.uuid4())

                if scene["asset_type"] == "image":
                    # Create image asset requirement
                    image_asset = {
                        "id": asset_id,
                        "type": "image",
                        "prompt": scene["visual_description"],
                        "duration": scene["duration"],
                        "start_time": scene["start_time"],
                        "style": scene["style"],
                        "resolution": "1920x1080",
                        "estimated_cost": 0.04,  # DALL-E 3 pricing
                        "generation_complexity": scene["complexity"]
                    }
                    images.append(image_asset)

                elif scene["asset_type"] == "video":
                    # Create video asset requirement
                    video_asset = {
                        "id": asset_id,
                        "type": "video",
                        "prompt": scene["visual_description"],
                        "duration": scene["duration"],
                        "start_time": scene["start_time"],
                        "style": scene["style"],
                        "resolution": "1920x1080",
                        "estimated_cost": scene["duration"] * 0.50,  # RunwayML pricing
                        "generation_complexity": scene["complexity"]
                    }
                    videos.append(video_asset)

                # Add transition if not the last scene
                if scene["index"] < len(analysis["scenes"]) - 1:
                    transitions.append({
                        "from_asset": asset_id,
                        "to_asset": "next_scene",
                        "type": "fade",
                        "duration": 0.5
                    })

            # Calculate summary
            summary = {
                "images": len(images),
                "videos": len(videos),
                "audio": 1,  # Narration track
                "total_assets": len(images) + len(videos) + 1
            }

            assets_plan = {
                "summary": summary,
                "assets": {
                    "images": images,
                    "videos": videos,
                    "audio": [{
                        "id": str(uuid.uuid4()),
                        "type": "narration",
                        "prompt": " ".join([s.get("text", "") for s in analysis["scenes"] if s.get("text")]),
                        "duration": analysis["total_duration"],
                        "start_time": 0.0,
                        "style": "natural",
                        "resolution": "audio/wav",
                        "estimated_cost": 0.50,
                        "generation_complexity": "simple"
                    }]
                },
                "transitions": transitions
            }

            logger.info(f"Asset plan created: {summary}")
            return assets_plan

        except Exception as e:
            logger.error(f"Asset plan creation failed: {e}")
            raise ContentPlanningError(f"Failed to create asset plan: {e}")

    def _parse_script_analysis(
        self,
        gemini_response: str,
        script_text: str,
        target_duration: int
    ) -> Dict[str, Any]:
        """Parse Gemini response into structured analysis."""
        try:
            # Try to extract JSON from Gemini response
            if "{" in gemini_response and "}" in gemini_response:
                start = gemini_response.find("{")
                end = gemini_response.rfind("}") + 1
                json_str = gemini_response[start:end]
                analysis = json.loads(json_str)
                return analysis
        except:
            pass

        # Fallback: create basic analysis
        sentences = [s.strip() for s in script_text.split(".") if s.strip()]
        scene_duration = target_duration / max(len(sentences), 1)

        scenes = []
        for i, sentence in enumerate(sentences):
            # Simple heuristic: longer sentences or action words suggest video
            needs_video = (
                len(sentence) > 100 or
                any(word in sentence.lower() for word in ["moving", "action", "dynamic", "flowing"])
            )

            scenes.append({
                "index": i,
                "text": sentence,
                "start_time": i * scene_duration,
                "duration": scene_duration,
                "asset_type": "video" if needs_video else "image",
                "visual_description": f"Professional {sentence[:50]}...",
                "style": "professional",
                "complexity": "medium"
            })

        return {
            "total_duration": target_duration,
            "scene_count": len(scenes),
            "scenes": scenes,
            "quality_score": 0.75
        }

    async def generate_content_preview(self, script_text: str) -> Dict[str, Any]:
        """Generate quick preview without full planning."""
        try:
            analysis = await self.analyze_script_content(script_text, target_duration=180)

            image_count = sum(1 for s in analysis["scenes"] if s["asset_type"] == "image")
            video_count = sum(1 for s in analysis["scenes"] if s["asset_type"] == "video")

            return {
                "estimated_images": image_count,
                "estimated_videos": video_count,
                "estimated_duration": analysis["total_duration"],
                "cost_estimate": (image_count * 0.04) + (video_count * 0.50 * 5) + 0.50,
                "time_estimate": 10 + (image_count * 2) + (video_count * 5)  # minutes
            }
        except Exception as e:
            logger.error(f"Preview generation failed: {e}")
            raise ContentPlanningError(f"Failed to generate preview: {e}")

    async def store_generation_plan(self, db, plan) -> str:
        """Store generation plan in database for approval workflow."""
        try:
            logger.info(f"Storing generation plan {plan.plan_id}")

            # Convert Pydantic model to JSON string
            plan_json = plan.model_dump_json()

            # Convert string script_id to UUID
            script_uuid = uuid.UUID(plan.script_id)

            # Create database record
            db_plan = GenerationPlanDB(
                id=uuid.UUID(plan.plan_id),
                script_id=script_uuid,
                plan_data=plan_json,
                status=PlanStatusEnum.PENDING
            )

            db.add(db_plan)
            db.commit()
            db.refresh(db_plan)

            logger.info(f"Successfully stored generation plan {plan.plan_id}")
            return plan.plan_id

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to store generation plan {plan.plan_id}: {e}")
            raise ContentPlanningError(f"Failed to store generation plan: {e}")

    async def get_generation_plan(self, db, plan_id: str):
        """Retrieve stored generation plan."""
        try:
            logger.info(f"Retrieving generation plan {plan_id}")

            # Convert string to UUID for database query
            plan_uuid = uuid.UUID(plan_id)

            # Query database
            db_plan = db.query(GenerationPlanDB).filter(GenerationPlanDB.id == plan_uuid).first()

            if not db_plan:
                logger.warning(f"Generation plan {plan_id} not found in database")
                return None

            # Convert JSON back to dict for return
            plan_data = json.loads(db_plan.plan_data)
            logger.info(f"Successfully retrieved generation plan {plan_id}")
            return plan_data

        except Exception as e:
            logger.error(f"Failed to retrieve generation plan {plan_id}: {e}")
            raise ContentPlanningError(f"Failed to retrieve generation plan: {e}")

    async def apply_user_modifications(self, plan, modifications: Dict[str, Any]):
        """Apply user modifications to generation plan."""
        plan_id = plan.get('plan_id', 'unknown')
        logger.info(f"Applying user modifications to plan {plan_id}")
        # TODO: Implement modification logic
        return plan

    async def start_generation_workflow(self, db, plan) -> str:
        """Start the actual asset generation workflow."""
        workflow_id = str(uuid.uuid4())
        plan_id = plan.get('plan_id', 'unknown')
        logger.info(f"Starting generation workflow {workflow_id} for plan {plan_id}")
        # TODO: Integrate with existing Celery workflow
        return workflow_id

    async def mark_plan_rejected(self, db, plan_id: str, notes: Optional[str] = None):
        """Mark plan as rejected by user."""
        logger.info(f"Marking plan {plan_id} as rejected: {notes}")
        # TODO: Implement rejection tracking

    async def edit_plan_asset(self, plan: Dict[str, Any], asset_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Edit a specific asset in the plan."""
        logger.info(f"Editing asset {asset_id} with updates: {list(updates.keys())}")

        updated_plan = plan.copy()
        asset_found = False

        # Find and update the asset in all asset categories
        for asset_type in ["images", "videos", "audio"]:
            if asset_type in updated_plan.get("assets", {}):
                for i, asset in enumerate(updated_plan["assets"][asset_type]):
                    if asset.get("id") == asset_id:
                        # Update the asset with provided fields
                        for key, value in updates.items():
                            if key == "asset_type" and value != asset_type:
                                # Handle type change separately
                                continue
                            asset[key] = value

                        # Recalculate cost based on changes
                        if "duration" in updates or "asset_type" in updates:
                            asset["estimated_cost"] = self._calculate_asset_cost(asset)

                        asset_found = True
                        logger.info(f"Updated asset {asset_id} in {asset_type} category")
                        break

                if asset_found:
                    break

        if not asset_found:
            raise ValueError(f"Asset {asset_id} not found in plan")

        # Update summary counts
        updated_plan["summary"] = self._calculate_summary(updated_plan["assets"])

        return updated_plan

    async def delete_plan_asset(self, plan: Dict[str, Any], asset_id: str) -> Dict[str, Any]:
        """Delete a specific asset from the plan."""
        logger.info(f"Deleting asset {asset_id}")

        updated_plan = plan.copy()
        asset_found = False

        # Find and remove the asset from all asset categories
        for asset_type in ["images", "videos", "audio"]:
            if asset_type in updated_plan.get("assets", {}):
                original_count = len(updated_plan["assets"][asset_type])
                updated_plan["assets"][asset_type] = [
                    asset for asset in updated_plan["assets"][asset_type]
                    if asset.get("id") != asset_id
                ]

                if len(updated_plan["assets"][asset_type]) < original_count:
                    asset_found = True
                    logger.info(f"Deleted asset {asset_id} from {asset_type} category")
                    break

        if not asset_found:
            raise ValueError(f"Asset {asset_id} not found in plan")

        # Update summary counts
        updated_plan["summary"] = self._calculate_summary(updated_plan["assets"])

        return updated_plan

    async def change_asset_type(self, plan: Dict[str, Any], asset_id: str, new_type: str) -> Dict[str, Any]:
        """Change an asset type between image and video."""
        logger.info(f"Changing asset {asset_id} type to {new_type}")

        updated_plan = plan.copy()
        asset_to_move = None
        original_type = None

        # Find the asset and determine its current type
        for asset_type in ["images", "videos"]:
            if asset_type in updated_plan.get("assets", {}):
                for asset in updated_plan["assets"][asset_type]:
                    if asset.get("id") == asset_id:
                        asset_to_move = asset.copy()
                        original_type = asset_type
                        # Remove from original category
                        updated_plan["assets"][asset_type] = [
                            a for a in updated_plan["assets"][asset_type]
                            if a.get("id") != asset_id
                        ]
                        break
                if asset_to_move:
                    break

        if not asset_to_move:
            raise ValueError(f"Asset {asset_id} not found or cannot change type")

        # Update asset properties for new type
        asset_to_move["type"] = new_type
        asset_to_move["estimated_cost"] = self._calculate_asset_cost_by_type(asset_to_move, new_type)

        # Add to new category
        target_category = "images" if new_type == "image" else "videos"
        if target_category not in updated_plan["assets"]:
            updated_plan["assets"][target_category] = []
        updated_plan["assets"][target_category].append(asset_to_move)

        # Update summary counts
        updated_plan["summary"] = self._calculate_summary(updated_plan["assets"])

        logger.info(f"Changed asset {asset_id} from {original_type} to {target_category}")
        return updated_plan

    async def update_generation_plan(self, db, plan_id: str, updated_plan: Dict[str, Any], cost_breakdown: Dict[str, float]):
        """Update an existing generation plan in the database."""
        try:
            logger.info(f"Updating generation plan {plan_id}")

            # Convert string to UUID for database query
            plan_uuid = uuid.UUID(plan_id)

            # Update the plan data
            updated_plan_data = {
                **updated_plan,
                "estimated_costs": cost_breakdown,
                "updated_at": datetime.utcnow().isoformat()
            }

            # Query and update database record
            db_plan = db.query(GenerationPlanDB).filter(GenerationPlanDB.id == plan_uuid).first()
            if not db_plan:
                raise ValueError(f"Plan {plan_id} not found in database")

            db_plan.plan_data = json.dumps(updated_plan_data)
            db.commit()

            logger.info(f"Successfully updated generation plan {plan_id}")

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update generation plan {plan_id}: {e}")
            raise ContentPlanningError(f"Failed to update generation plan: {e}")

    def _calculate_asset_cost(self, asset: Dict[str, Any]) -> float:
        """Calculate cost for a single asset."""
        asset_type = asset.get("type", "")
        duration = asset.get("duration", 1.0)

        return self._calculate_asset_cost_by_type(asset, asset_type)

    def _calculate_asset_cost_by_type(self, asset: Dict[str, Any], asset_type: str) -> float:
        """Calculate cost for asset by type."""
        duration = asset.get("duration", 1.0)

        if asset_type == "image":
            return 0.04  # DALL-E 3 pricing
        elif asset_type == "video":
            return duration * 0.50  # RunwayML pricing per second
        elif asset_type == "narration" or asset_type == "audio":
            return 0.50  # Audio generation pricing
        else:
            return 0.10  # Default fallback

    def _calculate_summary(self, assets: Dict[str, List]) -> Dict[str, int]:
        """Calculate summary counts for asset categories."""
        return {
            "images": len(assets.get("images", [])),
            "videos": len(assets.get("videos", [])),
            "audio": len(assets.get("audio", [])),
            "total_assets": len(assets.get("images", [])) + len(assets.get("videos", [])) + len(assets.get("audio", []))
        }