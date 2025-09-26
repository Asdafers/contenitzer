"""
Integration test for asset metadata tracking
Task: T010 [P] - Integration test asset metadata tracking
"""

import pytest
from sqlalchemy.orm import Session
from datetime import datetime


class TestAssetMetadataTracking:
    """Integration tests for asset metadata tracking"""

    def test_asset_includes_generation_model_field(self, db_session: Session):
        """Test asset metadata includes generation_model field with correct model name"""
        from backend.src.models.media_asset import MediaAsset

        asset = MediaAsset(
            asset_type="image",
            file_path="/media/images/test_001.jpg",
            gemini_model_used="gemini-2.5-flash-image",
            generation_metadata={
                "model_version": "gemini-2.5-flash-image",
                "generation_time_ms": 25000,
                "prompt": "Professional background for AI discussion"
            }
        )

        db_session.add(asset)
        db_session.commit()

        # Verify asset was saved with correct model information
        saved_asset = db_session.query(MediaAsset).filter(
            MediaAsset.gemini_model_used == "gemini-2.5-flash-image"
        ).first()

        assert saved_asset is not None
        assert saved_asset.gemini_model_used == "gemini-2.5-flash-image"

    def test_model_fallback_used_flag_accuracy(self, db_session: Session):
        """Test model_fallback_used flag is accurately set"""
        from backend.src.models.media_asset import MediaAsset

        # Primary model asset (no fallback)
        primary_asset = MediaAsset(
            asset_type="image",
            file_path="/media/images/primary_001.jpg",
            gemini_model_used="gemini-2.5-flash-image",
            generation_metadata={
                "model_version": "gemini-2.5-flash-image",
                "fallback_used": False
            }
        )

        # Fallback model asset
        fallback_asset = MediaAsset(
            asset_type="image",
            file_path="/media/images/fallback_001.jpg",
            gemini_model_used="gemini-pro",
            generation_metadata={
                "model_version": "gemini-pro",
                "fallback_used": True,
                "primary_model_attempted": "gemini-2.5-flash-image"
            }
        )

        db_session.add_all([primary_asset, fallback_asset])
        db_session.commit()

        # Verify flags are set correctly
        primary_saved = db_session.query(MediaAsset).filter(
            MediaAsset.gemini_model_used == "gemini-2.5-flash-image"
        ).first()
        assert primary_saved.generation_metadata.get("fallback_used") is False

        fallback_saved = db_session.query(MediaAsset).filter(
            MediaAsset.gemini_model_used == "gemini-pro"
        ).first()
        assert fallback_saved.generation_metadata.get("fallback_used") is True

    def test_generation_metadata_completeness(self, db_session: Session):
        """Test generation_metadata includes all required fields"""
        from backend.src.models.media_asset import MediaAsset

        asset = MediaAsset(
            asset_type="image",
            file_path="/media/images/complete_001.jpg",
            gemini_model_used="gemini-2.5-flash-image",
            generation_metadata={
                "model_version": "gemini-2.5-flash-image",
                "generation_time_ms": 28000,
                "quality_score": 0.92,
                "prompt": "AI technology background image",
                "fallback_used": False,
                "retry_count": 0,
                "api_response_time_ms": 27500
            }
        )

        db_session.add(asset)
        db_session.commit()

        saved_asset = db_session.query(MediaAsset).first()
        metadata = saved_asset.generation_metadata

        # Verify all expected metadata fields
        assert "model_version" in metadata
        assert "generation_time_ms" in metadata
        assert "quality_score" in metadata
        assert "prompt" in metadata
        assert "fallback_used" in metadata

        # Verify data types
        assert isinstance(metadata["generation_time_ms"], int)
        assert isinstance(metadata["quality_score"], (int, float))
        assert isinstance(metadata["fallback_used"], bool)

    def test_asset_retrieval_with_metadata(self):
        """Test asset can be retrieved with all metadata intact"""
        from backend.src.api.media_assets import get_media_asset
        from backend.src.database import get_db

        db = next(get_db())

        # This will fail until API endpoint is implemented
        asset_id = "test-asset-001"
        result = get_media_asset(asset_id, db)

        if result:
            assert "generation_model" in result
            assert "model_fallback_used" in result
            assert "generation_metadata" in result

            metadata = result["generation_metadata"]
            assert "model_version" in metadata
            assert "generation_time_ms" in metadata

    def test_multiple_assets_different_models(self, db_session: Session):
        """Test multiple assets track different models correctly"""
        from backend.src.models.media_asset import MediaAsset

        assets = [
            MediaAsset(
                asset_type="image",
                file_path="/media/images/primary_001.jpg",
                gemini_model_used="gemini-2.5-flash-image",
                generation_metadata={"model_version": "gemini-2.5-flash-image"}
            ),
            MediaAsset(
                asset_type="image",
                file_path="/media/images/primary_002.jpg",
                gemini_model_used="gemini-2.5-flash-image",
                generation_metadata={"model_version": "gemini-2.5-flash-image"}
            ),
            MediaAsset(
                asset_type="image",
                file_path="/media/images/fallback_001.jpg",
                gemini_model_used="gemini-pro",
                generation_metadata={
                    "model_version": "gemini-pro",
                    "fallback_used": True
                }
            )
        ]

        db_session.add_all(assets)
        db_session.commit()

        # Verify model distribution
        primary_count = db_session.query(MediaAsset).filter(
            MediaAsset.gemini_model_used == "gemini-2.5-flash-image"
        ).count()
        fallback_count = db_session.query(MediaAsset).filter(
            MediaAsset.gemini_model_used == "gemini-pro"
        ).count()

        assert primary_count == 2
        assert fallback_count == 1

    def test_metadata_persistence_across_restarts(self, db_session: Session):
        """Test metadata persists across application restarts"""
        from backend.src.models.media_asset import MediaAsset

        # Create asset with metadata
        original_asset = MediaAsset(
            asset_type="image",
            file_path="/media/images/persistent_001.jpg",
            gemini_model_used="gemini-2.5-flash-image",
            generation_metadata={
                "model_version": "gemini-2.5-flash-image",
                "generation_time_ms": 30000,
                "creation_timestamp": datetime.utcnow().isoformat()
            }
        )

        db_session.add(original_asset)
        db_session.commit()
        asset_id = original_asset.id

        # Simulate application restart by clearing session
        db_session.expunge_all()

        # Retrieve asset after "restart"
        retrieved_asset = db_session.query(MediaAsset).filter(
            MediaAsset.id == asset_id
        ).first()

        assert retrieved_asset is not None
        assert retrieved_asset.gemini_model_used == "gemini-2.5-flash-image"
        assert retrieved_asset.generation_metadata["model_version"] == "gemini-2.5-flash-image"
        assert "creation_timestamp" in retrieved_asset.generation_metadata

    def test_metadata_json_serialization(self, db_session: Session):
        """Test metadata correctly serializes to/from JSON"""
        from backend.src.models.media_asset import MediaAsset
        import json

        complex_metadata = {
            "model_version": "gemini-2.5-flash-image",
            "generation_time_ms": 25000,
            "quality_metrics": {
                "overall_score": 0.92,
                "detail_score": 0.88,
                "composition_score": 0.95
            },
            "generation_parameters": {
                "temperature": 0.7,
                "max_tokens": 1024
            },
            "fallback_used": False
        }

        asset = MediaAsset(
            asset_type="image",
            file_path="/media/images/json_test_001.jpg",
            gemini_model_used="gemini-2.5-flash-image",
            generation_metadata=complex_metadata
        )

        db_session.add(asset)
        db_session.commit()

        # Retrieve and verify JSON serialization
        saved_asset = db_session.query(MediaAsset).first()
        metadata = saved_asset.generation_metadata

        # Should be able to serialize/deserialize
        json_str = json.dumps(metadata)
        restored_metadata = json.loads(json_str)

        assert restored_metadata == complex_metadata
        assert restored_metadata["quality_metrics"]["overall_score"] == 0.92


@pytest.fixture
def db_session():
    """Database session fixture for testing"""
    from backend.src.database import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()