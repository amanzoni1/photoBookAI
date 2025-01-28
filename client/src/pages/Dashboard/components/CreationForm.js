// CreationForm.js

import React, { useState } from 'react';
import { useModel } from '../../../hooks/useModel';
import './CreationForm.css';
import FileUploadModal from './FileUploadModal';

function CreationForm({ onClose, onTrainingStart }) {
  const { createModel } = useModel();

  const [formData, setFormData] = useState({
    name: '',
    ageYears: '',
    ageMonths: '',
    sex: '',
    files: []
  });

  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [message, setMessage] = useState('');

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Basic validations
    if (!formData.name) {
      setMessage('Name is required');
      return;
    }

    if (!formData.ageYears && !formData.ageMonths) {
      setMessage('Please provide either age in years or months');
      return;
    }

    if (!formData.sex) {
      setMessage('Please select sex');
      return;
    }

    if (!formData.files.length) {
      setMessage('Please upload images');
      return;
    }

    if (formData.files.length < 5) {
      setMessage('Please upload at least 5 images');
      return;
    }

    // Prepare form data
    const data = new FormData();
    data.append('name', formData.name);
    data.append('ageYears', formData.ageYears);
    data.append('ageMonths', formData.ageMonths);
    data.append('sex', formData.sex);

    Array.from(formData.files).forEach(file => {
      data.append('files', file);
    });

    try {
      const result = await createModel(data, (progress) => {
        setUploadProgress(progress);
        setMessage(`Uploading: ${progress}%`);
      });

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
        {/* TOP ROW: Name & Sex side-by-side */}
        <div className="top-row">
          {/* Name Field */}
          <div className="name-field">
            <label>Name:</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              required
            />
          </div>

          {/* Sex Field */}
          <div className="sex-field">
            <label>Sex:</label>
            <select
              name="sex"
              value={formData.sex}
              onChange={handleInputChange}
              required
            >
              <option value="">--</option>
              <option value="M">M</option>
              <option value="F">F</option>
            </select>
          </div>
        </div>

        {/* AGE */}
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

        {/* UPLOAD PHOTOS */}
        <label>Upload Photos (5-40 images):</label>
        <button
          type="button"
          className="upload-button"
          onClick={() => setIsUploadModalOpen(true)}
        >
          <span className="upload-icon">
            <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#cccccc">
              <path d="M450-313v-371L330-564l-43-43 193-193 193 193-43 43-120-120v371h-60ZM220-160q-24 0-42-18t-18-42v-143h60v143h520v-143h60v143q0 24-18 42t-42 18H220Z" />
            </svg>
          </span>
          Upload Photos
        </button>

        <FileUploadModal
          isOpen={isUploadModalOpen}
          onClose={() => {
            if (formData.files.length > 0 && formData.files.length < 5) {
              setMessage('Please upload at least 5 images');
            }
            setIsUploadModalOpen(false);
          }}
          files={formData.files}
          onFilesChange={(files) => {
            if (files.length > 40) {
              setMessage('Maximum 40 images allowed');
              return;
            }
            setFormData(prev => ({ ...prev, files }));
          }}
        />
        <div className="file-message">
          {formData.files.length > 0 ? (
            <span>
              <span className="file-success">✓</span> {formData.files.length} files selected
            </span>
          ) : (
            'No files uploaded'
          )}
        </div>

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

export default CreationForm;