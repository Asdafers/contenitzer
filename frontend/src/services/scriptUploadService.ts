// API Response Types
export interface UploadResponse {
  script_id: string;
  status: 'PENDING' | 'VALID' | 'INVALID';
  message: string;
  file_name?: string;
  content_length: number;
  upload_timestamp: string;
}

export interface ScriptResponse {
  script_id: string;
  content: string;
  file_name?: string;
  validation_status: 'PENDING' | 'VALID' | 'INVALID';
  upload_timestamp: string;
  workflow_id: string;
}

export interface WorkflowResponse {
  workflow_id: string;
  mode: 'GENERATE' | 'UPLOAD';
  status: string;
  script_source?: string;
  skip_research: boolean;
  skip_generation: boolean;
  uploaded_script_id?: string;
  created_at: string;
  updated_at?: string;
}

export interface WorkflowCreateResponse {
  workflow_id: string;
  status: string;
  created_at: string;
}

export interface ApiError {
  error: string;
  message: string;
  timestamp: string;
  details?: Array<{
    field: string;
    issue: string;
  }>;
}

// Upload Options
export interface UploadOptions {
  workflowId: string;
  content?: string;
  file?: File;
}

export interface WorkflowCreateOptions {
  title?: string;
  description?: string;
}

class ScriptUploadService {
  private baseUrl: string;

  constructor(baseUrl: string = '') {
    this.baseUrl = baseUrl;
  }

  /**
   * Upload script content (file or text)
   */
  async uploadScript(options: UploadOptions): Promise<UploadResponse> {
    const { workflowId, content, file } = options;

    if (!content && !file) {
      throw new Error('Either content or file must be provided');
    }

    if (content && file) {
      throw new Error('Provide either content or file, not both');
    }

    const formData = new FormData();
    formData.append('workflow_id', workflowId);

    if (file) {
      formData.append('file', file);
    } else if (content) {
      formData.append('content', content);
    }

    const response = await fetch(`${this.baseUrl}/api/v1/scripts/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData: ApiError = await response.json();
      throw new Error(errorData.message || 'Upload failed');
    }

    return response.json();
  }

  /**
   * Get uploaded script by ID
   */
  async getScript(scriptId: string): Promise<ScriptResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/scripts/${scriptId}`, {
      method: 'GET',
    });

    if (!response.ok) {
      const errorData: ApiError = await response.json();
      throw new Error(errorData.message || 'Failed to retrieve script');
    }

    return response.json();
  }

  /**
   * Delete uploaded script by ID
   */
  async deleteScript(scriptId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/v1/scripts/${scriptId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const errorData: ApiError = await response.json();
      throw new Error(errorData.message || 'Failed to delete script');
    }
  }

  /**
   * Create a new workflow
   */
  async createWorkflow(options: WorkflowCreateOptions = {}): Promise<WorkflowCreateResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/workflows`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(options),
    });

    if (!response.ok) {
      const errorData: ApiError = await response.json();
      throw new Error(errorData.message || 'Failed to create workflow');
    }

    return response.json();
  }

  /**
   * Get workflow by ID
   */
  async getWorkflow(workflowId: string): Promise<WorkflowResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/workflows/${workflowId}`, {
      method: 'GET',
    });

    if (!response.ok) {
      const errorData: ApiError = await response.json();
      throw new Error(errorData.message || 'Failed to retrieve workflow');
    }

    return response.json();
  }

  /**
   * Set workflow mode
   */
  async setWorkflowMode(workflowId: string, mode: 'GENERATE' | 'UPLOAD'): Promise<{ workflow_id: string; mode: string; updated_at: string }> {
    const response = await fetch(`${this.baseUrl}/api/v1/workflows/${workflowId}/mode`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ mode }),
    });

    if (!response.ok) {
      const errorData: ApiError = await response.json();
      throw new Error(errorData.message || 'Failed to set workflow mode');
    }

    return response.json();
  }

  /**
   * Validate script content before upload (client-side validation)
   */
  validateContent(content: string): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];
    const maxSize = 51200; // 50KB

    // Check if empty
    if (!content || !content.trim()) {
      errors.push('Script content cannot be empty');
    }

    // Check size limit
    if (content.length > maxSize) {
      errors.push(`Content exceeds 50KB limit (${content.length} characters)`);
    }

    // Check for potentially harmful content
    const harmfulPatterns = [
      /<script[^>]*>.*?<\/script>/gi,
      /<\?php.*?\?>/gi,
      /#!/gi
    ];

    for (const pattern of harmfulPatterns) {
      if (pattern.test(content)) {
        errors.push('Content contains potentially harmful code');
        break;
      }
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Validate file before upload
   */
  validateFile(file: File): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];
    const maxSize = 51200; // 50KB
    const allowedTypes = ['text/plain', 'text/markdown', 'application/octet-stream'];

    // Check file size
    if (file.size > maxSize) {
      errors.push(`File size exceeds 50KB limit (${Math.round(file.size / 1024)}KB)`);
    }

    // Check file type
    if (!allowedTypes.includes(file.type) && !file.type.startsWith('text/')) {
      errors.push(`Invalid file type: ${file.type}. Only text files are supported.`);
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Get content statistics
   */
  getContentStats(content: string): {
    characterCount: number;
    wordCount: number;
    lineCount: number;
    paragraphCount: number;
    estimatedReadingTime: number;
  } {
    const characterCount = content.length;
    const words = content.trim().split(/\s+/).filter(word => word.length > 0);
    const wordCount = words.length;
    const lineCount = content.split('\n').length;
    const paragraphCount = content.split(/\n\s*\n/).length;
    const estimatedReadingTime = Math.ceil(wordCount / 150); // 150 words per minute

    return {
      characterCount,
      wordCount,
      lineCount,
      paragraphCount,
      estimatedReadingTime
    };
  }
}

// Export singleton instance
export const scriptUploadService = new ScriptUploadService();

// Export class for custom instances
export default ScriptUploadService;