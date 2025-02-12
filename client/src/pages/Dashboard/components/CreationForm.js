// CreationForm.js

import React, { useState } from "react";
import { useModel } from "../../../hooks/useModel";
import { useCredits } from "../../../contexts/CreditsContext";
import FileUploadModal from "./FileUploadModal";
import "./CreationForm.css";

function CreationForm({ onClose, onTrainingStart }) {
  const { createModel } = useModel();
  const { refreshCredits } = useCredits();

  const [formData, setFormData] = useState({
    name: "",
    ageYears: "",
    ageMonths: "",
    sex: "",
    files: [],
  });

  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [message, setMessage] = useState("");

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // File validation (not covered by HTML5 validation)
    if (formData.files.length < 5) {
      setMessage("Please upload at least 5 images");
      return;
    }

    // Form data preparation
    const data = new FormData();
    data.append("name", formData.name);
    data.append("ageYears", formData.ageYears);
    data.append("ageMonths", formData.ageMonths);
    data.append("sex", formData.sex);

    Array.from(formData.files).forEach((file) => {
      data.append("files", file);
    });

    try {
      const result = await createModel(data, (progress) => {
        setUploadProgress(progress);
        setMessage(`Uploading: ${progress}%`);
      });

      await refreshCredits();

      onTrainingStart(formData.name, {
        modelId: result.model_id,
        jobId: result.job_id,
      });

      setMessage("Training started successfully!");
      setTimeout(onClose, 1500);
    } catch (error) {
      if (error.response?.status === 403) {
        setMessage("Insufficient credits. Please purchase more credits.");
      } else {
        setMessage(error.response?.data?.message || "Failed to start training");
      }
      await refreshCredits();
    }
  };

  return (
    <div className="model-creation-form">
      <h2>Create New Model</h2>

      {message && (
        <p
          className={`message ${
            message.includes("Error") || message.includes("Please upload")
              ? "error"
              : "success"
          }`}
        >
          {message}
        </p>
      )}

      <form onSubmit={handleSubmit}>
        {/* TOP ROW: Name & Sex side-by-side */}
        <div className="top-row">
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
            required={!formData.ageMonths}
          />
          <input
            type="number"
            name="ageMonths"
            placeholder="Months"
            value={formData.ageMonths}
            onChange={handleInputChange}
            min="0"
            max="11"
            required={!formData.ageYears}
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
            <svg
              xmlns="http://www.w3.org/2000/svg"
              height="24px"
              viewBox="0 -960 960 960"
              width="24px"
              fill="#cccccc"
            >
              <path d="M450-313v-371L330-564l-43-43 193-193 193 193-43 43-120-120v371h-60ZM220-160q-24 0-42-18t-18-42v-143h60v143h520v-143h60v143q0 24-18 42t-42 18H220Z" />
            </svg>
          </span>
          Upload Photos
        </button>

        {/* Hidden input for file validation */}
        <input
          type="text"
          style={{ display: "none" }}
          value={formData.files.length ? "has-files" : ""}
          onChange={() => {}}
          required
        />

        <FileUploadModal
          isOpen={isUploadModalOpen}
          onClose={() => {
            if (formData.files.length > 0 && formData.files.length < 5) {
              setMessage("Please upload at least 5 images");
            }
            setIsUploadModalOpen(false);
          }}
          files={formData.files}
          onFilesChange={(files) => {
            if (files.length > 40) {
              setMessage("Maximum 40 images allowed");
              return;
            }
            setFormData((prev) => ({ ...prev, files }));
          }}
        />

        <div className="file-message">
          {formData.files.length > 0 ? (
            formData.files.length >= 5 ? (
              <span>
                <span className="file-success">✓</span> {formData.files.length}{" "}
                files selected
              </span>
            ) : (
              <span className="file-warning">
                {formData.files.length} files selected (minimum 5 required)
              </span>
            )
          ) : (
            "No files uploaded"
          )}
        </div>

        {uploadProgress > 0 && uploadProgress < 100 && (
          <div className="progress-bar">
            <div className="progress" style={{ width: `${uploadProgress}%` }} />
          </div>
        )}

        <button type="submit" disabled={uploadProgress > 0}>
          Start Training
        </button>
      </form>
    </div>
  );
}

export default CreationForm;
