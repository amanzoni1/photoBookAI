// ModelCreationForm.js

import React, { useState } from 'react';
import { useModel } from '../../../hooks/useModel';
import './ModelCreationForm.css';

function ModelCreationForm({ onClose, onTrainingStart }) {
  const { createModel } = useModel();
  
  const [formData, setFormData] = useState({
    name: '',
    ageYears: '',
    ageMonths: '',
    files: []
  });
  
  const [fileMessage, setFileMessage] = useState('No files uploaded');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [message, setMessage] = useState('');

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleFileChange = (e) => {
    const files = e.target.files;
    if (files.length < 5 || files.length > 30) {
      alert('Please upload between 5 and 30 pictures.');
      e.target.value = '';
      setFileMessage('No files uploaded');
    } else {
      setFormData({ ...formData, files: files });
      setFileMessage(
        <span>
          <span className="file-success">✓</span> {files.length} files selected
        </span>
      );
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validations
    if (!formData.name) {
      setMessage('Name is required');
      return;
    }

    if (!formData.ageYears && !formData.ageMonths) {
      setMessage('Please provide either age in years or months');
      return;
    }

    if (!formData.files.length) {
      setMessage('Please upload images');
      return;
    }

    // Prepare form data
    const data = new FormData();
    data.append('name', formData.name);
    data.append('ageYears', formData.ageYears);
    data.append('ageMonths', formData.ageMonths);
    
    Array.from(formData.files).forEach(file => {
      data.append('files', file);
    });

    try {
      const result = await createModel(data, (progress) => {
        setUploadProgress(progress);
        setMessage(`Uploading: ${progress}%`);
      });

      // Notify parent component of successful start
      onTrainingStart(formData.name, {
        modelId: result.model_id,
        jobId: result.job_id
      });

      setMessage('Training started successfully!');
      setTimeout(onClose, 1500);

    } catch (error) {
      if (error.response?.status === 403) {
        setMessage('Insufficient credits. Please purchase more credits.');
      } else {
        setMessage(error.response?.data?.message || 'Failed to start training');
      }
    }
  };

  return (
    <div className="model-creation-form">
      <h2>Create New Model</h2>
      
      {message && (
        <p className={`message ${message.includes('Error') ? 'error' : 'success'}`}>
          {message}
        </p>
      )}

      <form onSubmit={handleSubmit}>
        <label>Name:</label>
        <input 
          type="text" 
          name="name" 
          value={formData.name}
          onChange={handleInputChange} 
          required 
        />

        <label>Age:</label>
        <div className="age-inputs">
          <input
            type="number"
            name="ageYears"
            placeholder="Years"
            value={formData.ageYears}
            onChange={handleInputChange}
            min="0"
          />
          <input
            type="number"
            name="ageMonths"
            placeholder="Months"
            value={formData.ageMonths}
            onChange={handleInputChange}
            min="0"
            max="11"
          />
        </div>

        <label>Upload Photos (5-30 images):</label>
        <label htmlFor="file-upload" className="custom-file-upload">
          <span className="upload-icon">⬆</span> Upload Photos (PNG, JPG)
        </label>
        <input
          id="file-upload"
          type="file"
          multiple
          accept=".png,.jpg,.jpeg"
          onChange={handleFileChange}
          required
        />
        <div className="file-message">{fileMessage}</div>

        {uploadProgress > 0 && uploadProgress < 100 && (
          <div className="progress-bar">
            <div 
              className="progress" 
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        )}

        <button 
          type="submit" 
          disabled={!formData.files.length || uploadProgress > 0}
        >
          Start Training
        </button>
      </form>
    </div>
  );
}

export default ModelCreationForm;