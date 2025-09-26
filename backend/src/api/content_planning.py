"""
Content Planning API - Enhanced script analysis for comprehensive video generation.
Determines both image and video asset requirements for complete video creation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import uuid
import logging
from datetime import datetime

from src.lib.database import get_db
from src.models.uploaded_script import UploadedScript
from src.services.enhanced_content_planner import EnhancedContentPlanner
from src.services.cost_estimator import CostEstimator
from src.lib.exceptions import ContentPlanningError
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/content-planning", tags=["content-planning"])


# Request/Response Models
class GenerationPlanRequest(BaseModel):
    script_id: str
    target_duration: Optional[int] = 180  # seconds
    quality_level: Optional[str] = "high"  # low, medium, high, ultra
    style_preference: Optional[str] = "professional"  # professional, creative, minimal
    include_motion: Optional[bool] = True  # Whether to include video clips
    budget_limit: Optional[float] = None  # Maximum cost in USD


class AssetRequirement(BaseModel):
    id: str
    type: str  # "image", "video", "audio"
    prompt: str
    duration: float
    start_time: float
    style: str
    resolution: str
    estimated_cost: float
    generation_complexity: str  # "simple", "medium", "complex"


class GenerationPlan(BaseModel):
    plan_id: str
    script_id: str
    total_duration: float
    scene_count: int
    asset_summary: Dict[str, int]  # {"images": 45, "videos": 12, "audio": 8}
    assets: Dict[str, List[AssetRequirement]]
    transitions: List[Dict[str, Any]]
    estimated_costs: Dict[str, float]
    estimated_generation_time: int  # minutes
    quality_score: float  # 0.0-1.0
    created_at: str


class ApprovalRequest(BaseModel):
    plan_id: str
    approved: bool
    user_modifications: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


@router.post("/generate-plan", response_model=GenerationPlan)
async def generate_content_plan(
    request: GenerationPlanRequest,
    db: Session = Depends(get_db)
) -> GenerationPlan:
    """
    Analyze script and generate comprehensive content plan with both images and videos.

    This endpoint uses Gemini to intelligently analyze the script and determine:
    - Which scenes need static images vs dynamic videos
    - Optimal timing and transitions
    - Cost estimates for generation
    - Quality predictions
    """
    try:
        # Debug logging
        logger.info(f"Received request: script_id={request.script_id}, type={type(request.script_id)}")

        # Convert string to UUID object for SQLAlchemy
        try:
            script_uuid = uuid.UUID(request.script_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid script_id format: {request.script_id}"
            )

        # Validate script exists
        script = db.query(UploadedScript).filter(UploadedScript.id == script_uuid).first()
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Script {request.script_id} not found"
            )

        # Initialize enhanced content planner
        planner = EnhancedContentPlanner()
        cost_estimator = CostEstimator()

        logger.info(f"Generating content plan for script {request.script_id}")

        # Analyze script content with Gemini
        analysis = await planner.analyze_script_content(
            script_text=script.content,
            target_duration=request.target_duration,
            quality_level=request.quality_level,
            style_preference=request.style_preference,
            include_motion=request.include_motion
        )

        # Generate asset requirements
        assets_plan = await planner.create_asset_plan(
            analysis=analysis,
            budget_limit=request.budget_limit
        )

        # Calculate costs and timing
        cost_breakdown = cost_estimator.estimate_generation_costs(assets_plan)
        generation_time = cost_estimator.estimate_generation_time(assets_plan)

        # Create generation plan
        plan_id = str(uuid.uuid4())
        generation_plan = GenerationPlan(
            plan_id=plan_id,
            script_id=request.script_id,
            total_duration=analysis["total_duration"],
            scene_count=analysis["scene_count"],
            asset_summary=assets_plan["summary"],
            assets=assets_plan["assets"],
            transitions=assets_plan["transitions"],
            estimated_costs=cost_breakdown,
            estimated_generation_time=generation_time,
            quality_score=analysis["quality_score"],
            created_at=datetime.utcnow().isoformat()
        )

        # Store plan in database for later approval
        await planner.store_generation_plan(db, generation_plan)

        logger.info(f"Generated content plan {plan_id} for script {request.script_id}")
        logger.info(f"Plan summary: {assets_plan['summary']}, estimated cost: ${cost_breakdown['total']:.2f}")

        return generation_plan

    except ContentPlanningError as e:
        logger.error(f"Content planning error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content planning failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in content planning: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during content planning"
        )


@router.get("/plans/{plan_id}", response_model=GenerationPlan)
async def get_content_plan(
    plan_id: str,
    db: Session = Depends(get_db)
) -> GenerationPlan:
    """Retrieve a previously generated content plan."""
    try:
        planner = EnhancedContentPlanner()
        plan = await planner.get_generation_plan(db, plan_id)

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content plan {plan_id} not found"
            )

        return plan

    except Exception as e:
        logger.error(f"Error retrieving content plan {plan_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving content plan"
        )


@router.post("/plans/{plan_id}/approve")
async def approve_content_plan(
    plan_id: str,
    approval: ApprovalRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Approve or reject a content plan, optionally with user modifications.

    When approved, this triggers the actual asset generation workflow.
    """
    try:
        planner = EnhancedContentPlanner()

        # Validate plan exists
        plan = await planner.get_generation_plan(db, plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content plan {plan_id} not found"
            )

        if approval.approved:
            # Apply user modifications if provided
            if approval.user_modifications:
                plan = await planner.apply_user_modifications(plan, approval.user_modifications)

            # Trigger asset generation workflow
            workflow_id = await planner.start_generation_workflow(db, plan)

            logger.info(f"Content plan {plan_id} approved, starting workflow {workflow_id}")

            return {
                "status": "approved",
                "plan_id": plan_id,
                "workflow_id": workflow_id,
                "message": "Content plan approved and generation workflow started",
                "estimated_completion": f"{plan.estimated_generation_time} minutes"
            }
        else:
            # Plan rejected
            await planner.mark_plan_rejected(db, plan_id, approval.notes)

            logger.info(f"Content plan {plan_id} rejected by user")

            return {
                "status": "rejected",
                "plan_id": plan_id,
                "message": "Content plan rejected",
                "notes": approval.notes
            }

    except Exception as e:
        logger.error(f"Error processing approval for plan {plan_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing plan approval"
        )


@router.get("/scripts/{script_id}/preview")
async def preview_script_content(
    script_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Quick preview of what content would be generated for a script without full planning.
    Useful for initial user feedback before detailed planning.
    """
    try:
        # Validate script exists
        script = db.query(UploadedScript).filter(UploadedScript.id == script_id).first()
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Script {script_id} not found"
            )

        planner = EnhancedContentPlanner()

        # Generate quick preview
        preview = await planner.generate_content_preview(
            script_text=script.content
        )

        return {
            "script_id": script_id,
            "preview": preview,
            "estimated_assets": {
                "images": preview["estimated_images"],
                "videos": preview["estimated_videos"],
                "total_duration": preview["estimated_duration"]
            },
            "rough_cost_estimate": f"${preview['cost_estimate']:.2f}",
            "generation_time_estimate": f"{preview['time_estimate']} minutes"
        }

    except Exception as e:
        logger.error(f"Error generating preview for script {script_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating content preview"
        )


@router.get("/cost-estimates")
async def get_cost_estimates() -> Dict[str, Any]:
    """
    Get current pricing information for different asset types and quality levels.
    Helps users understand costs before planning.
    """
    try:
        cost_estimator = CostEstimator()
        estimates = cost_estimator.get_current_pricing()

        return {
            "pricing": estimates,
            "last_updated": datetime.utcnow().isoformat(),
            "currency": "USD",
            "notes": [
                "Prices are estimates and may vary based on complexity",
                "Bulk generation may qualify for volume discounts",
                "Premium styles and quality levels incur additional costs"
            ]
        }

    except Exception as e:
        logger.error(f"Error retrieving cost estimates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving cost estimates"
        )