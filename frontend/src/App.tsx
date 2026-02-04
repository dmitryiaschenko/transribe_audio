import { useState, useEffect, useCallback } from 'react';
import { FileUpload } from './components/FileUpload';
import { ProgressBar } from './components/ProgressBar';
import { TranscriptionResult } from './components/TranscriptionResult';
import { useWebSocket } from './hooks/useWebSocket';
import {
  fetchConfig,
  uploadFile,
  Config,
  TranscriptionResult as Result,
} from './api/client';

type AppState = 'idle' | 'uploading' | 'processing' | 'completed' | 'error';

function App() {
  const [config, setConfig] = useState<Config | null>(null);
  const [state, setState] = useState<AppState>('idle');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [language, setLanguage] = useState<string>('');
  const [conversationType, setConversationType] = useState<string>('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [stage, setStage] = useState<string>('pending');
  const [progress, setProgress] = useState<number>(0);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load config on mount
  useEffect(() => {
    fetchConfig()
      .then((cfg) => {
        setConfig(cfg);
        if (cfg.languages.length > 0) {
          setLanguage(cfg.languages[0]);
        }
        if (cfg.conversation_types.length > 0) {
          setConversationType(cfg.conversation_types[0]);
        }
      })
      .catch((err) => {
        setError('Failed to load configuration. Is the server running?');
        console.error(err);
      });
  }, []);

  const handleProgress = useCallback((newStage: string, newPercent: number) => {
    setStage(newStage);
    setProgress(newPercent);
  }, []);

  const handleCompleted = useCallback((newResult: Result) => {
    setResult(newResult);
    setState('completed');
    setStage('completed');
    setProgress(100);
  }, []);

  const handleError = useCallback((message: string) => {
    setError(message);
    setState('error');
    setStage('failed');
  }, []);

  // WebSocket connection
  useWebSocket(state === 'processing' ? jobId : null, {
    onProgress: handleProgress,
    onCompleted: handleCompleted,
    onError: handleError,
  });

  const handleSubmit = async () => {
    if (!selectedFile || !language || !conversationType) {
      return;
    }

    setState('uploading');
    setError(null);
    setResult(null);
    setStage('uploading');
    setProgress(0);

    try {
      const response = await uploadFile(selectedFile, language, conversationType);
      setJobId(response.job_id);
      setState('processing');
      setStage('processing');
      setProgress(10);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
      setState('error');
    }
  };

  const handleReset = () => {
    setState('idle');
    setSelectedFile(null);
    setJobId(null);
    setStage('pending');
    setProgress(0);
    setResult(null);
    setError(null);
  };

  const isProcessing = state === 'uploading' || state === 'processing';

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <div className="container mx-auto px-4 py-8 max-w-3xl">
        <header className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">Audio Transcription App</h1>
          <p className="text-gray-400">
            Upload an audio file and get a transcription with AI analysis
          </p>
        </header>

        <main className="space-y-6">
          {/* File Upload */}
          <section>
            <FileUpload
              onFileSelected={setSelectedFile}
              selectedFile={selectedFile}
              disabled={isProcessing}
              supportedExtensions={config?.supported_extensions || []}
            />
          </section>

          {/* Options */}
          {config && (
            <section className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Language
                </label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  disabled={isProcessing}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2
                           text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500
                           disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {config.languages.map((lang) => (
                    <option key={lang} value={lang}>
                      {lang}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Conversation Type
                </label>
                <select
                  value={conversationType}
                  onChange={(e) => setConversationType(e.target.value)}
                  disabled={isProcessing}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2
                           text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500
                           disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {config.conversation_types.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>
            </section>
          )}

          {/* Submit Button */}
          <section>
            {state === 'completed' ? (
              <button
                onClick={handleReset}
                className="w-full bg-gray-700 hover:bg-gray-600 text-white font-semibold
                         py-3 px-6 rounded-lg transition-colors"
              >
                Start New Transcription
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={!selectedFile || isProcessing}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700
                         disabled:cursor-not-allowed text-white font-semibold
                         py-3 px-6 rounded-lg transition-colors"
              >
                {isProcessing ? 'Processing...' : 'Start Transcription'}
              </button>
            )}
          </section>

          {/* Progress */}
          <section>
            <ProgressBar
              stage={stage}
              percent={progress}
              isActive={isProcessing}
            />
          </section>

          {/* Error */}
          {error && (
            <section className="bg-red-900/30 border border-red-700 rounded-lg p-4">
              <p className="text-red-400">{error}</p>
            </section>
          )}

          {/* Result */}
          {result && (
            <section>
              <TranscriptionResult result={result} />
            </section>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
