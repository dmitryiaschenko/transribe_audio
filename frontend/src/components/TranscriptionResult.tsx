import { useState } from 'react';
import { TranscriptionResult as Result } from '../api/client';

interface TranscriptionResultProps {
  result: Result;
}

export function TranscriptionResult({ result }: TranscriptionResultProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(result.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Transcription Result</h2>
        <button
          onClick={handleCopy}
          className={`
            px-4 py-2 rounded-lg text-sm font-medium transition-colors
            ${copied
              ? 'bg-green-600 text-white'
              : 'bg-gray-700 hover:bg-gray-600 text-gray-200'
            }
          `}
        >
          {copied ? 'Copied!' : 'Copy to Clipboard'}
        </button>
      </div>

      <div className="bg-gray-800 rounded-lg p-4 max-h-96 overflow-y-auto">
        <pre className="whitespace-pre-wrap text-gray-200 font-mono text-sm">
          {result.text}
        </pre>
      </div>

      <div className="flex flex-wrap gap-4 text-sm text-gray-400">
        <div className="bg-gray-800 rounded-lg px-4 py-2">
          <span className="text-gray-500">Input tokens:</span>{' '}
          <span className="text-gray-200">{result.input_tokens.toLocaleString()}</span>
        </div>
        <div className="bg-gray-800 rounded-lg px-4 py-2">
          <span className="text-gray-500">Output tokens:</span>{' '}
          <span className="text-gray-200">{result.output_tokens.toLocaleString()}</span>
        </div>
        <div className="bg-gray-800 rounded-lg px-4 py-2">
          <span className="text-gray-500">Total cost:</span>{' '}
          <span className="text-green-400">${result.total_cost.toFixed(4)}</span>
        </div>
      </div>
    </div>
  );
}
