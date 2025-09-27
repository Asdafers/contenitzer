/**
 * Integration test for MediaSelection components
 * Tests the complete media selection workflow from browsing to selection.
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { rest } from 'msw';
import { setupServer } from 'msw/node';

import { MediaSelectionModal } from '../../src/components/MediaSelection/MediaSelectionModal';
import { MediaFileInfo, SelectedMediaAsset } from '../../src/components/MediaSelection/types';

// Mock API responses
const mockMediaFiles: MediaFileInfo[] = [
  {
    path: 'images/logo.png',
    name: 'logo.png',
    size: 15360,
    type: 'image',
    format: 'png',
    thumbnail_url: '/api/media/thumbnails/logo.png',
    dimensions: { width: 512, height: 512 },
    created_at: '2025-09-27T10:00:00Z'
  },
  {
    path: 'videos/intro.mp4',
    name: 'intro.mp4',
    size: 5242880,
    type: 'video',
    format: 'mp4',
    duration: 30.0,
    dimensions: { width: 1920, height: 1080 },
    created_at: '2025-09-27T09:30:00Z'
  },
  {
    path: 'audio/background.mp3',
    name: 'background.mp3',
    size: 3145728,
    type: 'audio',
    format: 'mp3',
    duration: 180.0,
    created_at: '2025-09-27T09:00:00Z'
  }
];

// Setup MSW server for API mocking
const server = setupServer(
  rest.get('/api/media/browse', (req, res, ctx) => {
    const fileType = req.url.searchParams.get('file_type');
    const filteredFiles = fileType
      ? mockMediaFiles.filter(file => file.type === fileType)
      : mockMediaFiles;

    return res(ctx.json({
      files: filteredFiles,
      total_count: filteredFiles.length,
      current_path: '',
      parent_path: null
    }));
  }),

  rest.get('/api/media/info/:filePath', (req, res, ctx) => {
    const { filePath } = req.params;
    const file = mockMediaFiles.find(f => f.path === filePath);

    if (!file) {
      return res(ctx.status(404), ctx.json({ detail: 'File not found' }));
    }

    return res(ctx.json(file));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('MediaSelection Integration Tests', () => {
  const mockOnMediaSelected = jest.fn();
  const mockOnMediaRemoved = jest.fn();
  const mockOnClose = jest.fn();

  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    onMediaSelected: mockOnMediaSelected,
    onMediaRemoved: mockOnMediaRemoved,
    selectedAssets: [] as SelectedMediaAsset[]
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should load and display media files from API', async () => {
    render(<MediaSelectionModal {...defaultProps} />);

    // Wait for API call and files to load
    await waitFor(() => {
      expect(screen.getByText('logo.png')).toBeInTheDocument();
      expect(screen.getByText('intro.mp4')).toBeInTheDocument();
      expect(screen.getByText('background.mp3')).toBeInTheDocument();
    });

    // Check file type indicators
    expect(screen.getByText('image')).toBeInTheDocument();
    expect(screen.getByText('video')).toBeInTheDocument();
    expect(screen.getByText('audio')).toBeInTheDocument();
  });

  test('should filter files by type', async () => {
    render(<MediaSelectionModal {...defaultProps} />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('logo.png')).toBeInTheDocument();
    });

    // Click image filter
    const imageFilter = screen.getByRole('button', { name: /images/i });
    fireEvent.click(imageFilter);

    // Wait for filtered results
    await waitFor(() => {
      expect(screen.getByText('logo.png')).toBeInTheDocument();
      expect(screen.queryByText('intro.mp4')).not.toBeInTheDocument();
      expect(screen.queryByText('background.mp3')).not.toBeInTheDocument();
    });
  });

  test('should select media file and show selection details', async () => {
    const user = userEvent.setup();
    render(<MediaSelectionModal {...defaultProps} />);

    // Wait for files to load
    await waitFor(() => {
      expect(screen.getByText('logo.png')).toBeInTheDocument();
    });

    // Click on a file to select it
    const logoFile = screen.getByTestId('media-file-logo.png');
    await user.click(logoFile);

    // Should show selection form
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/usage intent/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/scene association/i)).toBeInTheDocument();
  });

  test('should complete media selection workflow', async () => {
    const user = userEvent.setup();
    render(<MediaSelectionModal {...defaultProps} />);

    // Wait for files to load
    await waitFor(() => {
      expect(screen.getByText('logo.png')).toBeInTheDocument();
    });

    // Select a file
    const logoFile = screen.getByTestId('media-file-logo.png');
    await user.click(logoFile);

    // Fill in selection details
    const descriptionInput = screen.getByLabelText(/description/i);
    const usageIntentSelect = screen.getByLabelText(/usage intent/i);
    const sceneAssociationInput = screen.getByLabelText(/scene association/i);

    await user.type(descriptionInput, 'Company logo for branding');
    await user.selectOptions(usageIntentSelect, 'overlay');
    await user.type(sceneAssociationInput, 'intro');

    // Confirm selection
    const confirmButton = screen.getByRole('button', { name: /add to plan/i });
    await user.click(confirmButton);

    // Should call onMediaSelected with correct data
    expect(mockOnMediaSelected).toHaveBeenCalledWith(
      expect.objectContaining({
        file_info: expect.objectContaining({
          path: 'images/logo.png',
          name: 'logo.png',
          type: 'image'
        }),
        description: 'Company logo for branding',
        usage_intent: 'overlay',
        scene_association: 'intro'
      })
    );
  });

  test('should handle file preview', async () => {
    const user = userEvent.setup();
    render(<MediaSelectionModal {...defaultProps} />);

    // Wait for files to load
    await waitFor(() => {
      expect(screen.getByText('intro.mp4')).toBeInTheDocument();
    });

    // Click preview button on video file
    const previewButton = screen.getByTestId('preview-intro.mp4');
    await user.click(previewButton);

    // Should show preview modal or player
    expect(screen.getByTestId('media-preview')).toBeInTheDocument();
    expect(screen.getByText('intro.mp4')).toBeInTheDocument();
  });

  test('should handle pagination', async () => {
    // Mock API with more files for pagination
    server.use(
      rest.get('/api/media/browse', (req, res, ctx) => {
        const offset = parseInt(req.url.searchParams.get('offset') || '0');
        const limit = parseInt(req.url.searchParams.get('limit') || '10');

        const allFiles = [...Array(25)].map((_, i) => ({
          ...mockMediaFiles[0],
          path: `images/file_${i}.jpg`,
          name: `file_${i}.jpg`
        }));

        const paginatedFiles = allFiles.slice(offset, offset + limit);

        return res(ctx.json({
          files: paginatedFiles,
          total_count: allFiles.length,
          current_path: '',
          parent_path: null
        }));
      })
    );

    const user = userEvent.setup();
    render(<MediaSelectionModal {...defaultProps} />);

    // Wait for first page to load
    await waitFor(() => {
      expect(screen.getByText('file_0.jpg')).toBeInTheDocument();
    });

    // Click next page button
    const nextButton = screen.getByRole('button', { name: /next/i });
    await user.click(nextButton);

    // Should load second page
    await waitFor(() => {
      expect(screen.getByText('file_10.jpg')).toBeInTheDocument();
      expect(screen.queryByText('file_0.jpg')).not.toBeInTheDocument();
    });
  });

  test('should handle loading states', async () => {
    // Slow down API response
    server.use(
      rest.get('/api/media/browse', (req, res, ctx) => {
        return res(ctx.delay(1000), ctx.json({
          files: mockMediaFiles,
          total_count: mockMediaFiles.length,
          current_path: '',
          parent_path: null
        }));
      })
    );

    render(<MediaSelectionModal {...defaultProps} />);

    // Should show loading indicator
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    expect(screen.getByText(/loading media files/i)).toBeInTheDocument();

    // Wait for files to load
    await waitFor(() => {
      expect(screen.getByText('logo.png')).toBeInTheDocument();
    }, { timeout: 2000 });

    // Loading indicator should be gone
    expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
  });

  test('should handle API errors gracefully', async () => {
    // Mock API error
    server.use(
      rest.get('/api/media/browse', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ detail: 'Internal server error' }));
      })
    );

    render(<MediaSelectionModal {...defaultProps} />);

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(/error loading media files/i)).toBeInTheDocument();
      expect(screen.getByText(/internal server error/i)).toBeInTheDocument();
    });

    // Should show retry button
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  test('should close modal when cancel is clicked', async () => {
    const user = userEvent.setup();
    render(<MediaSelectionModal {...defaultProps} />);

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await user.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  test('should display selected assets correctly', async () => {
    const selectedAssets: SelectedMediaAsset[] = [
      {
        id: 'asset-1',
        file_info: mockMediaFiles[0],
        description: 'Selected logo',
        usage_intent: 'overlay',
        scene_association: 'intro',
        selected_at: '2025-09-27T10:00:00Z'
      }
    ];

    render(<MediaSelectionModal {...defaultProps} selectedAssets={selectedAssets} />);

    // Should show selected assets section
    expect(screen.getByText(/selected media/i)).toBeInTheDocument();
    expect(screen.getByText('Selected logo')).toBeInTheDocument();
    expect(screen.getByText('overlay')).toBeInTheDocument();
  });
});