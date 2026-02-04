import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

interface FileUploadProps {
  onFileSelected: (file: File) => void;
  selectedFile: File | null;
  disabled?: boolean;
  supportedExtensions: string[];
}

export function FileUpload({
  onFileSelected,
  selectedFile,
  disabled = false,
  supportedExtensions,
}: FileUploadProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFileSelected(acceptedFiles[0]);
      }
    },
    [onFileSelected]
  );

  const accept: Record<string, string[]> = {
    'audio/*': supportedExtensions,
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    multiple: false,
    disabled,
  });

  return (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
        transition-colors duration-200
        ${isDragActive ? 'border-blue-500 bg-blue-500/10' : 'border-gray-600 hover:border-gray-500'}
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      <input {...getInputProps()} />
      <div className="space-y-2">
        <div className="text-4xl">
          {selectedFile ? '📄' : '🎵'}
        </div>
        {selectedFile ? (
          <div>
            <p className="text-lg font-medium text-green-400">{selectedFile.name}</p>
            <p className="text-sm text-gray-400">
              {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
            </p>
          </div>
        ) : isDragActive ? (
          <p className="text-lg text-blue-400">Drop the audio file here...</p>
        ) : (
          <div>
            <p className="text-lg">Drag and drop an audio file here</p>
            <p className="text-sm text-gray-400">or click to select</p>
            <p className="text-xs text-gray-500 mt-2">
              Supported formats: {supportedExtensions.join(', ')}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
