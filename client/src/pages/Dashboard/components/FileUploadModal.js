// FileUploadZone.js

import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import './FileUploadModal.css';

function FileUploadModal({ isOpen, onClose, files, onFilesChange }) {
  const onDrop = useCallback(acceptedFiles => {
    const newFiles = [...files, ...acceptedFiles];
    onFilesChange(newFiles);
  }, [files, onFilesChange]);

  const removeFile = (index) => {
    const newFiles = files.filter((_, i) => i !== index);
    onFilesChange(newFiles);
  };

  const clearAll = () => {
    onFilesChange([]);
  };


  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png']
    },
    minSize: 0,
    maxSize: 5242880, // 5MB
  });

  if (!isOpen) return null;

  return (
    <div className="file-modal-overlay">
      <div className="file-modal">
        <button className="modal-close" onClick={onClose}>×</button>
        <h3>Upload Images</h3>

        <div {...getRootProps()} className={`modal-dropzone ${isDragActive ? 'active' : ''}`}>
          <input {...getInputProps()} />
          <div className="upload-icon">
            <svg xmlns="http://www.w3.org/2000/svg" height="40px" viewBox="0 -960 960 960" width="40px" fill="#ffffff">
              <path d="M450-313v-371L330-564l-43-43 193-193 193 193-43 43-120-120v371h-60ZM220-160q-24 0-42-18t-18-42v-143h60v143h520v-143h60v143q0 24-18 42t-42 18H220Z" />
            </svg>
          </div>
          <p>Drag & drop images here, or click to select</p>
          <span className="file-requirements">5-40 images (PNG, JPG)</span>
        </div>

        <div className="modal-file-list-header">
          {files.length > 0 && (
            <button
              type="button"
              className="clear-all-button"
              onClick={clearAll}
            >
              Clear All
            </button>
          )}
        </div>

        <div className="modal-file-list">
          {files.map((file, index) => (
            <div key={`${file.name}-${index}`} className="file-item">
              <img
                src={URL.createObjectURL(file)}
                alt={`Preview ${index}`}
                className="file-thumbnail"
              />
              {/* <div className="file-info">
                <span className="file-name">{file.name}</span>
                <span className="file-size">{(file.size / 1024).toFixed(1)} KB</span>
              </div> */}
              <button
                type="button"
                className="remove-file"
                onClick={() => removeFile(index)}
              >
                ×
              </button>
            </div>
          ))}
        </div>

        <div className="modal-actions">
          <button onClick={onClose} className="modal-done">Done</button>
        </div>
      </div>
    </div>
  );
}

export default FileUploadModal;