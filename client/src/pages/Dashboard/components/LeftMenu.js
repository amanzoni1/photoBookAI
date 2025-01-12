// LeftMenu.js

import React, { useState, useEffect } from 'react';
import './LeftMenu.css';
import ModelCreationForm from './ModelCreationForm';
import ModelForm from './ModelForm';
import createIcon from './images/create1.png';
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
                <p className="model-age">
                  {model.config?.age_years ? `${model.config.age_years} yrs` : ''}
                  {model.config?.age_months ? ` ${model.config.age_months} mos` : ''}
                </p>
                <p className="model-status">Status: {model.status}</p>
              </div>
            </div>
          ))}

          {/* "Create Model" button */}
          <button
            className={`create-button ${!hasModels ? 'margin-top-10' : 'margin-top-auto'}`}
            onClick={handleCreateModelClick}
          >
            <img src={createIcon} alt="Create Icon" className="button-icon" />
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
          <ModelCreationForm
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