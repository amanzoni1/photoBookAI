// ModelCreationForm.js

import React, { useState } from 'react';
import axios from '../../../utils/axiosConfig';
import './ModelCreationForm.css';

function ModelCreationForm({ onClose, onTrainingStart }) {
  const [formData, setFormData] = useState({
    name: '',
    ageYears: '',
    ageMonths: '',
    files: [],
  });
  const [fileMessage, setFileMessage] = useState('No files uploaded');
  const [message, setMessage] = useState('');

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleFileChange = (e) => {
    const files = e.target.files;
    if (files.length < 5 || files.length > 30) {
      alert('Please upload between 5 and 30 pictures.');
      e.target.value = ''; // Reset file input
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

    // Validate that name is provided
    if (!formData.name) {
      alert('Name is required');
      return;
    }

    // Validate that at least one of ageYears or ageMonths is provided
    if (!formData.ageYears && !formData.ageMonths) {
      alert('Please provide either age in years or months');
      return;
    }

    // Combine ageYears and ageMonths into a string
    let ageString = '';
    if (formData.ageYears) {
      ageString += `${formData.ageYears} year(s) `;
    }
    if (formData.ageMonths) {
      ageString += `${formData.ageMonths} month(s)`;
    }

    // Notify parent component that training has started
    onTrainingStart(formData.name, ageString.trim());

    // Prepare form data
    const data = new FormData();
    data.append('name', formData.name);
    data.append('ageYears', formData.ageYears);
    data.append('ageMonths', formData.ageMonths);
    for (let i = 0; i < formData.files.length; i++) {
      data.append('files', formData.files[i]);
    }

    try {
      const res = await axios.post('/api/create-model', data, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setMessage(res.data.message);
      // Close the form after submission
      onClose();
    } catch (err) {
      console.error(err.response?.data);
      setMessage(err.response?.data?.message || 'An error occurred.');
    }
  };

  return (
    <div className="model-creation-form">
      <h2>Create New Model</h2>
      {message && <p>{message}</p>}
      <form onSubmit={handleSubmit}>
        <label>Name:</label>
        <input type="text" name="name" onChange={handleInputChange} required />

        <label>Age:</label>
        <div className="age-inputs">
          <input
            type="number"
            name="ageYears"
            placeholder="Years"
            onChange={handleInputChange}
          />
          <input
            type="number"
            name="ageMonths"
            placeholder="Months"
            onChange={handleInputChange}
          />
        </div>

        <label>Upload Photos (5-30 images):</label>
        <label htmlFor="file-upload" className="custom-file-upload">
          <span className="upload-icon">⬆</span> Upload Photos (PNG, JPG)
        </label>
        <input
          id="file-upload"
          type="file"
          name="files"
          multiple
          accept=".png,.jpg,.jpeg"
          onChange={handleFileChange}
          required
        />
        <div className="file-message">{fileMessage}</div>

        <button type="submit">Start Training</button>
      </form>
    </div>
  );
}

export default ModelCreationForm;