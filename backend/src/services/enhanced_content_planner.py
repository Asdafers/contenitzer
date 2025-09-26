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
        # TODO: Implement database storage
        logger.info(f"Storing generation plan {plan.plan_id}")
        return plan.plan_id

    async def get_generation_plan(self, db, plan_id: str):
        """Retrieve stored generation plan."""
        # TODO: Implement database retrieval
        logger.info(f"Retrieving generation plan {plan_id}")
        return None

    async def apply_user_modifications(self, plan, modifications: Dict[str, Any]):
        """Apply user modifications to generation plan."""
        logger.info(f"Applying user modifications to plan {plan.plan_id}")
        # TODO: Implement modification logic
        return plan

    async def start_generation_workflow(self, db, plan) -> str:
        """Start the actual asset generation workflow."""
        workflow_id = str(uuid.uuid4())
        logger.info(f"Starting generation workflow {workflow_id} for plan {plan.plan_id}")
        # TODO: Integrate with existing Celery workflow
        return workflow_id

    async def mark_plan_rejected(self, db, plan_id: str, notes: Optional[str] = None):
        """Mark plan as rejected by user."""
        logger.info(f"Marking plan {plan_id} as rejected: {notes}")
        # TODO: Implement rejection tracking