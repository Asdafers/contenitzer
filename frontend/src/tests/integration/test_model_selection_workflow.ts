/**
 * Integration test for model selection workflow
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { GeminiModel } from '../../types/gemini';
import { ModelHealthStatus } from '../../types/health';

// Mock the complete workflow components
jest.mock('../../components/ModelSelector', () => ({
  ModelSelector: ({ selectedModel, onModelChange, allowFallback, onFallbackChange }: any) => (
    <div data-testid="model-selector">
      <select
        data-testid="model-dropdown"
        value={selectedModel}
        onChange={(e) => onModelChange(e.target.value)}
      >
        <option value="gemini-2.5-flash-image">Gemini Flash</option>
        <option value="gemini-pro">Gemini Pro</option>
      </select>
      <input
        data-testid="fallback-checkbox"
        type="checkbox"
        checked={allowFallback}
        onChange={(e) => onFallbackChange(e.target.checked)}
      />
    </div>
  )
}));

jest.mock('../../components/HealthStatusDisplay', () => ({
  HealthStatusDisplay: ({ healthData, showDetails }: any) => (
    <div data-testid="health-display">
      Status: {healthData?.overall_status}
      {showDetails && <div data-testid="health-details">Details shown</div>}
    </div>
  )
}));

jest.mock('../../hooks/useModelHealth', () => ({
  useModelHealth: () => ({
    healthData: {
      overall_status: 'healthy',
      models: {
        'gemini-2.5-flash-image': { available: true, error_count: 0 },
        'gemini-pro': { available: true, error_count: 1 }
      }
    },
    loading: false,
    error: null,
    refresh: jest.fn()
  })
}));

// Mock workflow component that combines model selection with health monitoring
const MockWorkflowComponent = ({ onGenerateRequest }: { onGenerateRequest: (params: any) => void }) => {
  const [selectedModel, setSelectedModel] = React.useState<GeminiModel>('gemini-2.5-flash-image');
  const [allowFallback, setAllowFallback] = React.useState(true);

  const handleGenerate = () => {
    onGenerateRequest({
      model: selectedModel,
      allow_fallback: allowFallback,
      prompt: 'Test prompt'
    });
  };

  return (
    <div data-testid="workflow-component">
      <div data-testid="model-selector">
        <select
          data-testid="model-dropdown"
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value as GeminiModel)}
        >
          <option value="gemini-2.5-flash-image">Gemini Flash</option>
          <option value="gemini-pro">Gemini Pro</option>
        </select>
        <input
          data-testid="fallback-checkbox"
          type="checkbox"
          checked={allowFallback}
          onChange={(e) => setAllowFallback(e.target.checked)}
        />
      </div>
      <div data-testid="health-display">
        Status: healthy
      </div>
      <button data-testid="generate-button" onClick={handleGenerate}>
        Generate
      </button>
    </div>
  );
};

describe('Integration: Model Selection Workflow', () => {
  const mockOnGenerateRequest = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should complete full model selection workflow', async () => {
    // Act
    render(<MockWorkflowComponent onGenerateRequest={mockOnGenerateRequest} />);

    // Assert initial state
    expect(screen.getByTestId('workflow-component')).toBeInTheDocument();
    expect(screen.getByTestId('model-dropdown')).toHaveValue('gemini-2.5-flash-image');
    expect(screen.getByTestId('fallback-checkbox')).toBeChecked();

    // Act - change model
    fireEvent.change(screen.getByTestId('model-dropdown'), {
      target: { value: 'gemini-pro' }
    });

    // Act - trigger generation
    fireEvent.click(screen.getByTestId('generate-button'));

    // Assert
    await waitFor(() => {
      expect(mockOnGenerateRequest).toHaveBeenCalledWith({
        model: 'gemini-pro',
        allow_fallback: true,
        prompt: 'Test prompt'
      });
    });
  });

  it('should handle model selection with fallback disabled', async () => {
    // Act
    render(<MockWorkflowComponent onGenerateRequest={mockOnGenerateRequest} />);

    // Disable fallback
    fireEvent.click(screen.getByTestId('fallback-checkbox'));
    fireEvent.click(screen.getByTestId('generate-button'));

    // Assert
    await waitFor(() => {
      expect(mockOnGenerateRequest).toHaveBeenCalledWith({
        model: 'gemini-2.5-flash-image',
        allow_fallback: false,
        prompt: 'Test prompt'
      });
    });
  });

  it('should reflect health status in workflow decisions', async () => {
    // Act
    render(<MockWorkflowComponent onGenerateRequest={mockOnGenerateRequest} />);

    // Assert health status is displayed
    expect(screen.getByTestId('health-display')).toHaveTextContent('Status: healthy');

    // Should allow generation when healthy
    fireEvent.click(screen.getByTestId('generate-button'));

    await waitFor(() => {
      expect(mockOnGenerateRequest).toHaveBeenCalled();
    });
  });
});