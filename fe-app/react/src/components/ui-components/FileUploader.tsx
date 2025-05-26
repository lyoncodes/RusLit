import React, { useState } from 'react';
import { FileUploadResult } from './FileUploadResult';

type FileUploaderProps = {
  onFilesChange: (files: FileList | null) => void;
};

export const FileUploader = ({ onFilesChange }: FileUploaderProps) => {
  const [files, setFiles] = useState<FileList | null>(null);
  const [status, setStatus] = useState<
    'initial' | 'uploading' | 'success' | 'fail'
  >('initial');

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setStatus('initial');
      setFiles(event.target.files);
      onFilesChange(event.target.files);
    }
  };

  const handleUpload = async () => {
    setStatus('uploading');
    if (files) {
      const formData = new FormData();
      [...files].forEach((file) => {
        formData.append('files', file);
      });
    }
  };

  return (
    <>
      <div className='input-group'>
        <input id='file' type='file' multiple onChange={handleFileChange} />
      </div>
      {files &&
        [...files].map((file, index) => (
          <section key={file.name}>
            File number {index + 1} details:
            <ul>
              <li>Name: {file.name}</li>
              <li>Type: {file.type}</li>
              <li>Size: {file.size} bytes</li>
            </ul>
          </section>
        ))}

      {files && (
        <button onClick={handleUpload} className='submit'>
          Upload {files.length > 1 ? 'files' : 'a file'}
        </button>
      )}
      <FileUploadResult status={status} />
    </>
  );
};
