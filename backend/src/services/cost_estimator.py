"""
Cost Estimator Service - Calculate costs for AI-generated content production.
Provides pricing estimates for images, videos, and processing time.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CostEstimator:
    """Service for estimating generation costs across different AI services."""

    def __init__(self):
        # Current pricing as of 2024 (USD)
        self.pricing = {
            "images": {
                "dall_e_3": {
                    "1024x1024": 0.040,
                    "1024x1792": 0.080,
                    "1792x1024": 0.080
                }
            },
            "videos": {
                "runway_ml": {
                    "per_second": 0.50,  # Approximate pricing
                    "minimum_charge": 2.00
                },
                "pika_labs": {
                    "per_second": 0.40,
                    "minimum_charge": 1.50
                }
            },
            "audio": {
                "text_to_speech": 0.50,  # Per minute
                "background_music": 0.25   # Per minute (stock)
            },
            "processing": {
                "composition": 0.10,  # Per minute of final video
                "storage": 0.05       # Per GB per month
            }
        }

    def estimate_generation_costs(self, assets_plan: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate total estimated costs for a generation plan.

        Args:
            assets_plan: Asset plan from EnhancedContentPlanner

        Returns:
            Dictionary with cost breakdown by asset type
        """
        try:
            costs = {
                "images": 0.0,
                "videos": 0.0,
                "audio": 0.0,
                "processing": 0.0,
                "total": 0.0
            }

            # Calculate image costs
            if "images" in assets_plan.get("assets", {}):
                for image in assets_plan["assets"]["images"]:
                    resolution = image.get("resolution", "1920x1080")
                    # Map to DALL-E pricing tiers
                    if "1920x1080" in resolution or "1080" in resolution:
                        cost = self.pricing["images"]["dall_e_3"]["1024x1024"]
                    else:
                        cost = self.pricing["images"]["dall_e_3"]["1024x1024"]

                    costs["images"] += cost

            # Calculate video costs
            if "videos" in assets_plan.get("assets", {}):
                for video in assets_plan["assets"]["videos"]:
                    duration = video.get("duration", 5.0)
                    video_cost = max(
                        duration * self.pricing["videos"]["runway_ml"]["per_second"],
                        self.pricing["videos"]["runway_ml"]["minimum_charge"]
                    )
                    costs["videos"] += video_cost

            # Calculate audio costs
            if "audio" in assets_plan.get("assets", {}):
                for audio in assets_plan["assets"]["audio"]:
                    duration_minutes = audio.get("duration", 180) / 60.0
                    if audio.get("type") == "narration":
                        costs["audio"] += duration_minutes * self.pricing["audio"]["text_to_speech"]
                    else:
                        costs["audio"] += duration_minutes * self.pricing["audio"]["background_music"]

            # Calculate processing costs
            total_duration_minutes = assets_plan.get("summary", {}).get("total_duration", 180) / 60.0
            costs["processing"] = total_duration_minutes * self.pricing["processing"]["composition"]

            # Calculate total
            costs["total"] = sum(costs[key] for key in ["images", "videos", "audio", "processing"])

            logger.info(f"Cost estimation complete: ${costs['total']:.2f} total")
            return costs

        except Exception as e:
            logger.error(f"Cost estimation failed: {e}")
            # Return conservative estimate
            return {
                "images": 5.0,
                "videos": 15.0,
                "audio": 2.0,
                "processing": 1.0,
                "total": 23.0
            }

    def estimate_generation_time(self, assets_plan: Dict[str, Any]) -> int:
        """
        Estimate total generation time in minutes.

        Args:
            assets_plan: Asset plan from EnhancedContentPlanner

        Returns:
            Estimated time in minutes
        """
        try:
            time_estimates = {
                "images": 2,    # minutes per image
                "videos": 5,    # minutes per video
                "audio": 1,     # minutes per audio track
                "composition": 3  # minutes for final composition
            }

            total_time = 0

            # Image generation time
            image_count = len(assets_plan.get("assets", {}).get("images", []))
            total_time += image_count * time_estimates["images"]

            # Video generation time
            video_count = len(assets_plan.get("assets", {}).get("videos", []))
            total_time += video_count * time_estimates["videos"]

            # Audio generation time
            audio_count = len(assets_plan.get("assets", {}).get("audio", []))
            total_time += audio_count * time_estimates["audio"]

            # Final composition time
            total_time += time_estimates["composition"]

            # Add 20% buffer for processing overhead
            total_time = int(total_time * 1.2)

            logger.info(f"Time estimation: {total_time} minutes")
            return max(total_time, 5)  # Minimum 5 minutes

        except Exception as e:
            logger.error(f"Time estimation failed: {e}")
            return 15  # Conservative fallback

    def get_current_pricing(self) -> Dict[str, Any]:
        """
        Get current pricing information for all services.

        Returns:
            Complete pricing structure with descriptions
        """
        return {
            "images": {
                "service": "DALL-E 3",
                "pricing": self.pricing["images"]["dall_e_3"],
                "description": "Professional image generation",
                "average_cost": "$0.04 per image"
            },
            "videos": {
                "service": "RunwayML",
                "pricing": self.pricing["videos"]["runway_ml"],
                "description": "AI video generation from text/image",
                "average_cost": "$0.50 per second"
            },
            "audio": {
                "services": {
                    "narration": "Text-to-Speech",
                    "music": "Stock Music Library"
                },
                "pricing": self.pricing["audio"],
                "description": "Narration and background audio",
                "average_cost": "$0.50 per minute"
            },
            "processing": {
                "service": "FFmpeg Composition",
                "pricing": self.pricing["processing"],
                "description": "Video assembly and effects",
                "average_cost": "$0.10 per minute"
            }
        }

    def calculate_budget_compliance(
        self,
        assets_plan: Dict[str, Any],
        budget_limit: float
    ) -> Dict[str, Any]:
        """
        Check if generation plan fits within budget and suggest optimizations.

        Args:
            assets_plan: Asset plan to evaluate
            budget_limit: Maximum budget in USD

        Returns:
            Budget analysis with recommendations
        """
        try:
            estimated_costs = self.estimate_generation_costs(assets_plan)
            total_cost = estimated_costs["total"]

            compliance = {
                "within_budget": total_cost <= budget_limit,
                "estimated_cost": total_cost,
                "budget_limit": budget_limit,
                "variance": budget_limit - total_cost,
                "variance_percent": ((budget_limit - total_cost) / budget_limit) * 100,
                "recommendations": []
            }

            if not compliance["within_budget"]:
                # Suggest cost optimizations
                overage = total_cost - budget_limit

                if estimated_costs["videos"] > 0:
                    compliance["recommendations"].append({
                        "type": "reduce_videos",
                        "description": "Replace some videos with static images",
                        "potential_savings": estimated_costs["videos"] * 0.3
                    })

                if estimated_costs["images"] > 2.0:
                    compliance["recommendations"].append({
                        "type": "reduce_images",
                        "description": "Reduce image count or use simpler styles",
                        "potential_savings": estimated_costs["images"] * 0.2
                    })

                compliance["recommendations"].append({
                    "type": "extend_deadline",
                    "description": "Use batch processing for 20% cost reduction",
                    "potential_savings": total_cost * 0.2
                })

            return compliance

        except Exception as e:
            logger.error(f"Budget compliance check failed: {e}")
            return {
                "within_budget": False,
                "estimated_cost": 0.0,
                "budget_limit": budget_limit,
                "error": str(e)
            }