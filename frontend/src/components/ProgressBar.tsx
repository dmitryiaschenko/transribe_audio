interface ProgressBarProps {
  stage: string;
  percent: number;
  isActive: boolean;
}

const stageLabels: Record<string, string> = {
  pending: 'Waiting...',
  uploading: 'Uploading file...',
  initializing: 'Initializing AI model...',
  processing: 'Processing...',
  transcribing: 'Transcribing audio...',
  completed: 'Completed!',
  failed: 'Failed',
};

export function ProgressBar({ stage, percent, isActive }: ProgressBarProps) {
  const label = stageLabels[stage] || stage;

  if (!isActive) {
    return null;
  }

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-gray-300">{label}</span>
        <span className="text-gray-400">{percent}%</span>
      </div>
      <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ease-out ${
            stage === 'failed' ? 'bg-red-500' : 'bg-blue-500'
          }`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
