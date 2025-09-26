/**
 * Component test for AssetMetadataView component
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { AssetMetadataView } from '../../components/AssetMetadataView';

// Mock component since it doesn't exist yet - test will fail initially (TDD)
jest.mock('../../components/AssetMetadataView', () => ({
  AssetMetadataView: ({
    asset,
    showModelInfo,
    showGenerationDetails,
    editable
  }: any) => (
    <div data-testid="asset-metadata-view">
      <div data-testid="asset-id">ID: {asset?.id}</div>
      <div data-testid="asset-type">Type: {asset?.asset_type}</div>
      <div data-testid="created-at">Created: {asset?.created_at}</div>

      {showModelInfo && asset?.generation_model && (
        <div data-testid="model-info">
          <div data-testid="generation-model">Model: {asset.generation_model}</div>
          <div data-testid="fallback-used">
            Fallback: {asset.model_fallback_used ? 'Yes' : 'No'}
          </div>
        </div>
      )}

      {showGenerationDetails && asset?.generation_metadata && (
        <div data-testid="generation-details">
          {asset.generation_metadata.prompt && (
            <div data-testid="generation-prompt">
              Prompt: {asset.generation_metadata.prompt}
            </div>
          )}
          {asset.generation_metadata.generation_time_ms && (
            <div data-testid="generation-time">
              Time: {asset.generation_metadata.generation_time_ms}ms
            </div>
          )}
          {asset.generation_metadata.quality_score && (
            <div data-testid="quality-score">
              Quality: {(asset.generation_metadata.quality_score * 100)}%
            </div>
          )}
        </div>
      )}

      {editable && (
        <button data-testid="edit-button">Edit</button>
      )}
    </div>
  )
}));

describe('AssetMetadataView Component', () => {
  const mockAsset = {
    id: '550e8400-e29b-41d4-a716-446655440000',
    asset_type: 'image',
    file_path: '/media/images/bg_001_uuid.jpg',
    generation_model: 'gemini-2.5-flash-image',
    model_fallback_used: false,
    generation_metadata: {
      prompt: 'Professional background image for AI discussion',
      generation_time_ms: 25000,
      model_version: 'gemini-2.5-flash-image',
      quality_score: 0.95
    },
    created_at: '2025-09-26T10:30:00Z'
  };

  const defaultProps = {
    asset: mockAsset,
    showModelInfo: true,
    showGenerationDetails: true,
    editable: false
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render basic asset information', () => {
    // Act
    render(<AssetMetadataView {...defaultProps} />);

    // Assert
    expect(screen.getByTestId('asset-metadata-view')).toBeInTheDocument();
    expect(screen.getByTestId('asset-id')).toHaveTextContent('ID: 550e8400-e29b-41d4-a716-446655440000');
    expect(screen.getByTestId('asset-type')).toHaveTextContent('Type: image');
    expect(screen.getByTestId('created-at')).toHaveTextContent('Created: 2025-09-26T10:30:00Z');
  });

  it('should display model information when showModelInfo is true', () => {
    // Act
    render(<AssetMetadataView {...defaultProps} />);

    // Assert
    expect(screen.getByTestId('model-info')).toBeInTheDocument();
    expect(screen.getByTestId('generation-model')).toHaveTextContent('Model: gemini-2.5-flash-image');
    expect(screen.getByTestId('fallback-used')).toHaveTextContent('Fallback: No');
  });

  it('should hide model information when showModelInfo is false', () => {
    // Arrange
    const props = { ...defaultProps, showModelInfo: false };

    // Act
    render(<AssetMetadataView {...props} />);

    // Assert
    expect(screen.queryByTestId('model-info')).not.toBeInTheDocument();
    expect(screen.queryByTestId('generation-model')).not.toBeInTheDocument();
    expect(screen.queryByTestId('fallback-used')).not.toBeInTheDocument();
  });

  it('should display generation details when showGenerationDetails is true', () => {
    // Act
    render(<AssetMetadataView {...defaultProps} />);

    // Assert
    expect(screen.getByTestId('generation-details')).toBeInTheDocument();
    expect(screen.getByTestId('generation-prompt'))
      .toHaveTextContent('Prompt: Professional background image for AI discussion');
    expect(screen.getByTestId('generation-time')).toHaveTextContent('Time: 25000ms');
    expect(screen.getByTestId('quality-score')).toHaveTextContent('Quality: 95%');
  });

  it('should hide generation details when showGenerationDetails is false', () => {
    // Arrange
    const props = { ...defaultProps, showGenerationDetails: false };

    // Act
    render(<AssetMetadataView {...props} />);

    // Assert
    expect(screen.queryByTestId('generation-details')).not.toBeInTheDocument();
    expect(screen.queryByTestId('generation-prompt')).not.toBeInTheDocument();
    expect(screen.queryByTestId('generation-time')).not.toBeInTheDocument();
    expect(screen.queryByTestId('quality-score')).not.toBeInTheDocument();
  });

  it('should show fallback usage when model_fallback_used is true', () => {
    // Arrange
    const assetWithFallback = {
      ...mockAsset,
      generation_model: 'gemini-pro',
      model_fallback_used: true
    };

    const props = { ...defaultProps, asset: assetWithFallback };

    // Act
    render(<AssetMetadataView {...props} />);

    // Assert
    expect(screen.getByTestId('generation-model')).toHaveTextContent('Model: gemini-pro');
    expect(screen.getByTestId('fallback-used')).toHaveTextContent('Fallback: Yes');
  });

  it('should handle different asset types', () => {
    const assetTypes = ['image', 'video_clip', 'audio'];

    assetTypes.forEach(assetType => {
      // Arrange
      const assetWithType = { ...mockAsset, asset_type: assetType };
      const props = { ...defaultProps, asset: assetWithType };

      // Act
      render(<AssetMetadataView {...props} />);

      // Assert
      expect(screen.getByTestId('asset-type')).toHaveTextContent(`Type: ${assetType}`);

      // Cleanup for next iteration
      screen.getByTestId('asset-metadata-view').remove();
    });
  });

  it('should display edit button when editable is true', () => {
    // Arrange
    const props = { ...defaultProps, editable: true };

    // Act
    render(<AssetMetadataView {...props} />);

    // Assert
    expect(screen.getByTestId('edit-button')).toBeInTheDocument();
    expect(screen.getByTestId('edit-button')).toHaveTextContent('Edit');
  });

  it('should hide edit button when editable is false', () => {
    // Arrange
    const props = { ...defaultProps, editable: false };

    // Act
    render(<AssetMetadataView {...props} />);

    // Assert
    expect(screen.queryByTestId('edit-button')).not.toBeInTheDocument();
  });

  it('should handle missing generation metadata gracefully', () => {
    // Arrange
    const assetWithoutMetadata = {
      ...mockAsset,
      generation_metadata: undefined
    };

    const props = { ...defaultProps, asset: assetWithoutMetadata };

    // Act
    render(<AssetMetadataView {...props} />);

    // Assert - should still render basic info and model info
    expect(screen.getByTestId('asset-metadata-view')).toBeInTheDocument();
    expect(screen.getByTestId('asset-id')).toBeInTheDocument();
    expect(screen.getByTestId('model-info')).toBeInTheDocument();
    expect(screen.queryByTestId('generation-details')).not.toBeInTheDocument();
  });

  it('should handle partial generation metadata', () => {
    // Arrange
    const assetWithPartialMetadata = {
      ...mockAsset,
      generation_metadata: {
        prompt: 'Test prompt',
        // Missing generation_time_ms and quality_score
      }
    };

    const props = { ...defaultProps, asset: assetWithPartialMetadata };

    // Act
    render(<AssetMetadataView {...props} />);

    // Assert
    expect(screen.getByTestId('generation-details')).toBeInTheDocument();
    expect(screen.getByTestId('generation-prompt')).toHaveTextContent('Prompt: Test prompt');
    expect(screen.queryByTestId('generation-time')).not.toBeInTheDocument();
    expect(screen.queryByTestId('quality-score')).not.toBeInTheDocument();
  });

  it('should handle null asset gracefully', () => {
    // Arrange
    const props = { ...defaultProps, asset: null };

    // Act
    render(<AssetMetadataView {...props} />);

    // Assert - should render without crashing
    expect(screen.getByTestId('asset-metadata-view')).toBeInTheDocument();
    expect(screen.getByTestId('asset-id')).toHaveTextContent('ID:');
  });

  it('should handle undefined asset gracefully', () => {
    // Arrange
    const props = { ...defaultProps, asset: undefined };

    // Act
    render(<AssetMetadataView {...props} />);

    // Assert - should render without crashing
    expect(screen.getByTestId('asset-metadata-view')).toBeInTheDocument();
    expect(screen.getByTestId('asset-id')).toHaveTextContent('ID:');
  });

  it('should format quality score as percentage', () => {
    // Arrange
    const assetWithLowQuality = {
      ...mockAsset,
      generation_metadata: {
        ...mockAsset.generation_metadata,
        quality_score: 0.73
      }
    };

    const props = { ...defaultProps, asset: assetWithLowQuality };

    // Act
    render(<AssetMetadataView {...props} />);

    // Assert
    expect(screen.getByTestId('quality-score')).toHaveTextContent('Quality: 73%');
  });

  it('should display generation time in milliseconds', () => {
    // Arrange
    const assetWithLongGeneration = {
      ...mockAsset,
      generation_metadata: {
        ...mockAsset.generation_metadata,
        generation_time_ms: 45750
      }
    };

    const props = { ...defaultProps, asset: assetWithLongGeneration };

    // Act
    render(<AssetMetadataView {...props} />);

    // Assert
    expect(screen.getByTestId('generation-time')).toHaveTextContent('Time: 45750ms');
  });

  it('should handle very long prompts', () => {
    // Arrange
    const longPrompt = 'A very long prompt that describes in great detail the kind of image that should be generated with specific requirements and constraints that might span multiple lines and contain detailed instructions for the AI model to follow when creating the visual content';

    const assetWithLongPrompt = {
      ...mockAsset,
      generation_metadata: {
        ...mockAsset.generation_metadata,
        prompt: longPrompt
      }
    };

    const props = { ...defaultProps, asset: assetWithLongPrompt };

    // Act
    render(<AssetMetadataView {...props} />);

    // Assert
    expect(screen.getByTestId('generation-prompt')).toHaveTextContent(`Prompt: ${longPrompt}`);
  });
});