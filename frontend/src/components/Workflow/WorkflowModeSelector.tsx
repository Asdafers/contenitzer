import React, { useState } from 'react';

interface WorkflowModeSelectorProps {
  onModeSelect: (mode: 'GENERATE' | 'UPLOAD') => void;
  currentMode?: 'GENERATE' | 'UPLOAD';
  disabled?: boolean;
}

export const WorkflowModeSelector: React.FC<WorkflowModeSelectorProps> = ({
  onModeSelect,
  currentMode,
  disabled = false,
}) => {
  const [selectedMode, setSelectedMode] = useState<'GENERATE' | 'UPLOAD' | null>(currentMode || null);

  const handleModeSelect = (mode: 'GENERATE' | 'UPLOAD') => {
    if (disabled) return;

    setSelectedMode(mode);
    onModeSelect(mode);
  };

  const modes = [
    {
      id: 'GENERATE' as const,
      title: 'Generate Script',
      icon: (
        <svg data-testid="generate-mode-icon" className="w-12 h-12 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      ),
      description: 'Generate script from YouTube research',
      features: [
        'YouTube Research',
        'AI Script Generation',
        'Topic Analysis',
        'Automated Content Creation'
      ],
      timeEstimate: '~5-10 minutes',
      steps: ['YouTube research', 'AI script generation']
    },
    {
      id: 'UPLOAD' as const,
      title: 'Upload Script',
      icon: (
        <svg data-testid="upload-mode-icon" className="w-12 h-12 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
      ),
      description: 'Upload your own existing script',
      features: [
        'Script Upload',
        'Content Validation',
        'Skip Research & Generation',
        'Faster Processing'
      ],
      timeEstimate: '~1-2 minutes',
      steps: ['Script upload']
    }
  ];

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Choose Content Creation Method
        </h2>
        <p className="text-gray-600">
          Select how you want to create your content script
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {modes.map((mode) => (
          <button
            key={mode.id}
            onClick={() => handleModeSelect(mode.id)}
            disabled={disabled}
            className={`
              relative p-6 rounded-xl border-2 transition-all duration-200 text-left
              ${disabled
                ? 'opacity-50 cursor-not-allowed border-gray-200'
                : 'cursor-pointer hover:shadow-lg hover:scale-105'
              }
              ${selectedMode === mode.id
                ? 'border-blue-500 bg-blue-50 selected'
                : 'border-gray-200 hover:border-blue-300 hover'
              }
            `}
            role="button"
            aria-label={`Select ${mode.title} mode`}
          >
            {selectedMode === mode.id && (
              <div className="absolute top-4 right-4">
                <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              </div>
            )}

            <div className="flex flex-col items-center text-center mb-4">
              {mode.icon}
              <h3 className="text-xl font-semibold text-gray-900 mt-4 mb-2">
                {mode.title}
              </h3>
              <p className="text-gray-600 text-sm">
                {mode.description}
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Features:</span>
                <span className="text-sm text-blue-600 font-medium">
                  {mode.timeEstimate}
                </span>
              </div>

              <ul className="space-y-1">
                {mode.features.map((feature, index) => (
                  <li key={index} className="flex items-center text-sm text-gray-600">
                    <svg className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>

              <div className="pt-3 border-t border-gray-200">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Workflow Steps:
                  </span>
                </div>
                <div className="flex flex-wrap gap-1 mt-2">
                  {mode.steps.map((step, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                    >
                      {step}
                    </span>
                  ))}
                  {mode.id === 'UPLOAD' && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                      Skip research & generation
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-center">
              <div className={`
                px-4 py-2 rounded-md text-sm font-medium transition-colors
                ${selectedMode === mode.id
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700'
                }
              `}>
                {selectedMode === mode.id ? 'Selected' : `Select ${mode.title}`}
              </div>
            </div>
          </button>
        ))}
      </div>

      {selectedMode && (
        <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-blue-500 mr-3 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <h4 className="font-medium text-blue-900 mb-1">
                {selectedMode === 'GENERATE' ? 'AI Generation Mode Selected' : 'Script Upload Mode Selected'}
              </h4>
              <p className="text-sm text-blue-800">
                {selectedMode === 'GENERATE'
                  ? 'Your script will be generated using AI based on YouTube research and trending topics.'
                  : 'You can upload your existing script file or paste content directly. Research and generation steps will be skipped.'
                }
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};