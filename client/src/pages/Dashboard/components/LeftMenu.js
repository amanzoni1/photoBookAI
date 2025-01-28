// LeftMenu.js

import React, { useState, useEffect } from 'react';
import './LeftMenu.css';
import CreationForm from './CreationForm';
import ModelForm from './ModelForm';
import modelPlaceholder from './images/bab.png';
import { useModel } from '../../../hooks/useModel';
import { useCredits } from '../../../contexts/CreditsContext';
import BuyCreditsModal from '../../BuyCreditsModal/BuyCreditsModal';

function LeftMenu() {
  const [showModelForm, setShowModelForm] = useState(false);
  const [models, setModels] = useState([]);
  const [currentTrainingModel, setCurrentTrainingModel] = useState(null);
  const [selectedModel, setSelectedModel] = useState(null);
  const [showBuyCreditsModal, setShowBuyCreditsModal] = useState(false);

  const {
    checkModelStatus,
    fetchModels,
    loading: modelLoading,
    error: modelError
  } = useModel();

  const { credits } = useCredits();

  /**
   * Handle "Create New Model" button.
   * If user has model credits, show the training form; otherwise open BuyCreditsModal.
   */
  const handleCreateModelClick = () => {
    if (credits.model_credits > 0) {
      setShowModelForm(true);
    } else {
      // Instead of confirm(...) we open the buy-credits popup
      setShowBuyCreditsModal(true);
    }
  };

  /**
   * After user uploads/trains a new model, we poll the training job status.
   */
  const handleTrainingStart = async (modelName, trainingInfo) => {
    setShowModelForm(false);

    // Create a placeholder for the "in progress" model
    const newModel = {
      id: trainingInfo.modelId,
      name: modelName,
      isTraining: true,
      jobId: trainingInfo.jobId
    };
    setCurrentTrainingModel(newModel);

    // Poll job status every 5 seconds until COMPLETED/FAILED
    const pollInterval = setInterval(async () => {
      try {
        const status = await checkModelStatus(trainingInfo.modelId);

        if (status.status === 'COMPLETED') {
          clearInterval(pollInterval);
          setModels(prevModels => [
            { ...newModel, isTraining: false, ...status },
            ...prevModels
          ]);
          setCurrentTrainingModel(null);
        } else if (status.status === 'FAILED') {
          clearInterval(pollInterval);
          setCurrentTrainingModel(null);
          alert(`Training failed: ${status.error_message || 'Unknown error'}`);
        }
      } catch (error) {
        console.error('Error checking training status:', error);
        clearInterval(pollInterval);
        setCurrentTrainingModel(null);
      }
    }, 5000);
  };

  /**
   * Handle user clicking on a model to manage it.
   */
  const handleModelClick = (model) => {
    setSelectedModel(model);
  };

  const handleCloseModelForm = () => {
    setSelectedModel(null);
  };

  /**
   * Fetch user’s completed models on mount
   */
  useEffect(() => {
    const loadUserModels = async () => {
      try {
        let fetchedModels = await fetchModels();
        fetchedModels = fetchedModels.filter(m => m.status === 'COMPLETED');
        // Example: only show the first 3 (??) 
        fetchedModels = fetchedModels.slice(0, 3);
        setModels(fetchedModels);
      } catch (err) {
        console.error('Error fetching models:', err);
      }
    };
    loadUserModels();
  }, [fetchModels]);

  /**
   * Determine if user has any existing or training models
   */
  const hasModels = models.length > 0 || currentTrainingModel !== null;

  return (
    <div className="left-menu">
      {/* Show loading or error states if needed */}
      {modelLoading && <p className="loading-text">Loading your models...</p>}
      {modelError && <p className="error-message">{modelError}</p>}

      {/* If no form is active, show main menu */}
      {!showModelForm && !selectedModel && (
        <>
          {/* Show the "training in progress" placeholder */}
          {currentTrainingModel && (
            <div key={currentTrainingModel.id} className="model-box training-model">
              <div className="loading-indicator">
                <div className="spinner"></div>
                <p>Training in progress...</p>
              </div>
            </div>
          )}

          {/* Existing completed models */}
          {models.map(model => (
            <div
              key={model.id}
              className="model-box"
              onClick={() => handleModelClick(model)}
            >
              <img src={modelPlaceholder} alt="Model" className="model-image" />
              <div className="model-info">
                <p className="model-name">{model.name}</p>
              </div>
            </div>
          ))}

          {/* Create Model button */}
          <button
            className={`create-button ${!hasModels ? 'margin-top-10' : 'margin-top-auto'}`}
            onClick={handleCreateModelClick}
          >
            <span className="button-icon">
              <svg
                width="35" height="35"
                viewBox="0 0 20 20"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M13.2632 15.934C12.9123 15.8729 12.9123 15.3691 13.2632 15.3081C14.5346 15.0869 15.5457 14.1185 15.8217 12.8579L15.8428 12.7613C15.9188 12.4145 16.4126 12.4123 16.4915 12.7585L16.5172 12.8711C16.8034 14.1257 17.8148 15.0859 19.0827 15.3065C19.4354 15.3678 19.4354 15.8742 19.0827 15.9356C17.8148 16.1561 16.8034 17.1163 16.5172 18.371L16.4915 18.4836C16.4126 18.8297 15.9188 18.8276 15.8428 18.4807L15.8217 18.3841C15.5457 17.1235 14.5346 16.1551 13.2632 15.934Z"
                  stroke="currentColor"
                  strokeWidth="1.3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  d="M1.99989 9.46036C1.21618 9.32161 1.21618 8.1776 1.99989 8.03896C4.83915 7.53668 7.09738 5.33761 7.71365 2.47491L7.76088 2.25547C7.93045 1.46786 9.03338 1.46295 9.20958 2.24903L9.26698 2.50475C9.90613 5.35396 12.1648 7.53443 14.9964 8.03532C15.784 8.17467 15.784 9.32456 14.9964 9.46399C12.1648 9.96473 9.90613 12.1452 9.26698 14.9945L9.20958 15.2502C9.03338 16.0362 7.93045 16.0314 7.76088 15.2437L7.71365 15.0243C7.09738 12.1616 4.83915 9.96245 1.99989 9.46036Z"
                  stroke="currentColor"
                  strokeWidth="1.68"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </span>
            <span>Create a new model</span>
          </button>
        </>
      )}

      {/* Show the training form if showModelForm===true */}
      {showModelForm && (
        <div className="model-creation-container">
          <button
            className="close-button"
            onClick={() => setShowModelForm(false)}
          >
            ×
          </button>
          <CreationForm
            onClose={() => setShowModelForm(false)}
            onTrainingStart={handleTrainingStart}
          />
        </div>
      )}

      {/* Show ModelForm for selected model */}
      {selectedModel && (
        <div className="model-form-container">
          <button className="close-button" onClick={handleCloseModelForm}>
            ×
          </button>
          <ModelForm
            model={selectedModel}
            onClose={handleCloseModelForm}
          />
        </div>
      )}

      {/* The same buy-credits modal approach as in Navbar */}
      <BuyCreditsModal
        isOpen={showBuyCreditsModal}
        onClose={() => setShowBuyCreditsModal(false)}
      />
    </div>
  );
}

export default LeftMenu;