// src/components/LeftMenu.js

import React, { useState, useEffect } from 'react';
import './LeftMenu.css';
import ModelCreationForm from './ModelCreationForm';
import ModelForm from './ModelForm';
import createIcon from './images/create1.png';
import modelPlaceholder from './images/bab.png';
import { useModel } from '../../../hooks/useModel';
import { useCredits } from '../../../hooks/useCredits';

function LeftMenu() {
  const [showModelForm, setShowModelForm] = useState(false);
  const [models, setModels] = useState([]);
  const [currentTrainingModel, setCurrentTrainingModel] = useState(null);
  const [selectedModel, setSelectedModel] = useState(null);

  const {
    checkModelStatus,
    fetchModels,
    loading: modelLoading,
    error: modelError
  } = useModel();

  const { credits, purchaseCredits } = useCredits();

  /**
   * Handle clicking the "Create New Model" button.
   * Checks user credits, and optionally prompts to purchase more.
   */
  const handleCreateModelClick = async () => {
    if (credits.model_credits > 0) {
      setShowModelForm(true);
    } else {
      try {
        const confirmed = window.confirm(
          'You need to purchase credits to create a model. Would you like to purchase 1 model credit for $24.99?'
        );
        if (confirmed) {
          const result = await purchaseCredits('MODEL', 1);
          if (result.message === 'Purchase successful') {
            alert('Credits purchased successfully! You can now create a model.');
            setShowModelForm(true);
          } else {
            throw new Error('Purchase failed');
          }
        }
      } catch (error) {
        console.error('Purchase error:', error);
        alert(error.response?.data?.message || 'Failed to purchase credits. Please try again.');
      }
    }
  };

  /**
   * After the user creates/starts training a new model:
   * - We create a placeholder for that model (showing "in progress").
   * - We poll the model’s status until it’s COMPLETE or FAILED.
   */
  const handleTrainingStart = async (modelName, trainingInfo) => {
    setShowModelForm(false);

    // Create a placeholder for the model being trained
    const newModel = {
      id: trainingInfo.modelId,
      name: modelName,
      isTraining: true,
      jobId: trainingInfo.jobId
    };
    setCurrentTrainingModel(newModel);

    // Start polling for training status every 5 seconds
    const pollInterval = setInterval(async () => {
      try {
        const status = await checkModelStatus(trainingInfo.modelId);

        if (status.status === 'COMPLETED') {
          clearInterval(pollInterval);
          setModels((prevModels) => [
            {
              ...newModel,
              isTraining: false,
              ...status
            },
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
   * When user clicks on a model in the list, open the "ModelForm" for it.
   */
  const handleModelClick = (model) => {
    setSelectedModel(model);
  };

  /**
   * Close the ModelForm panel
   */
  const handleCloseModelForm = () => {
    setSelectedModel(null);
  };

  /**
   * Fetch all user models on component mount
   */
  useEffect(() => {
    const loadUserModels = async () => {
      try {
        let fetchedModels = await fetchModels();
        fetchedModels = fetchedModels.filter(m => m.status === 'COMPLETED');
        fetchedModels = fetchedModels.slice(0, 3) //////////
        setModels(fetchedModels);
      } catch (err) {
        console.error('Error fetching models:', err);
      }
    };
    loadUserModels();
  }, [fetchModels]);

  /**
   * If we have either currentTrainingModel or models.length > 0,
   * we consider that "we have models".
   */
  const hasModels = models.length > 0 || currentTrainingModel !== null;

  return (
    <div className="left-menu">
      {/* Optionally, you can show loading/error states */}
      {modelLoading && <p className="loading-text">Loading your models...</p>}
      {modelError && <p className="error-message">{modelError}</p>}

      {/* Show the main menu if no form is active */}
      {!showModelForm && !selectedModel && (
        <>
          {/* Model in training */}
          {currentTrainingModel && (
            <div key={currentTrainingModel.id} className="model-box training-model">
              <div className="loading-indicator">
                <div className="spinner"></div>
                <p>Training in progress...</p>
              </div>
            </div>
          )}

          {/* Existing models */}
          {models.map((model) => (
            <div
              key={model.id}
              className="model-box"
              onClick={() => handleModelClick(model)}
            >
              <img src={modelPlaceholder} alt="Model" className="model-image" />
              <div className="model-info">
                <p className="model-name">{model.name}</p>

                {/* If you want to show the model's age from config */}
                <p className="model-age">
                  {model.config?.age_years
                    ? `${model.config.age_years} yrs`
                    : ''}
                  {model.config?.age_months
                    ? ` ${model.config.age_months} mos`
                    : ''}
                </p>

                {/* Example showing the model's status */}
                <p className="model-status">Status: {model.status}</p>
              </div>
            </div>
          ))}

          {/* Create New Model button */}
          <button
            className={`create-button ${!hasModels ? 'margin-top-10' : 'margin-top-auto'}`}
            onClick={handleCreateModelClick}
          >
            <img src={createIcon} alt="Create Icon" className="button-icon" />
            <span>Create a new model</span>
          </button>
        </>
      )}

      {/* Show ModelCreationForm */}
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
    </div>
  );
}

export default LeftMenu;