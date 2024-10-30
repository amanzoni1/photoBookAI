// src/components/LeftMenu.js

import React, { useState } from 'react';
import './LeftMenu.css';
import ModelCreationForm from './ModelCreationForm';
import ModelForm from './ModelForm';
import createIcon from './images/create1.png';
import modelPlaceholder from './images/bab.png';

function LeftMenu() {
  const [hasAccess, setHasAccess] = useState(false);
  const [showModelForm, setShowModelForm] = useState(false);
  const [models, setModels] = useState([]);
  const [currentTrainingModel, setCurrentTrainingModel] = useState(null);
  const [selectedModel, setSelectedModel] = useState(null);

  // Handle clicking the "Create New Model" button
  const handleCreateModelClick = () => {
    if (hasAccess) {
      setShowModelForm(true);
    } else {
      const confirmed = window.confirm(
        'You need to purchase access to create a model. Proceed to payment?'
      );
      if (confirmed) {
        setHasAccess(true);
        alert('Payment successful! You can now create a model.');
        setShowModelForm(true);
      }
    }
  };

  // Handle starting the training process
  const handleTrainingStart = (modelName, age) => {
    setShowModelForm(false);

    // Create a placeholder for the model being trained
    const newModel = {
      id: Date.now(),
      name: modelName,
      age: age,
      isTraining: true,
    };
    setCurrentTrainingModel(newModel);

    // Simulate training duration (5 seconds)
    setTimeout(() => {
      // Update the model to indicate training is complete
      newModel.isTraining = false;
      setModels([newModel, ...models]);
      setCurrentTrainingModel(null);
    }, 5000);
  };

  // Handle clicking on a model to manage it
  const handleModelClick = (model) => {
    setSelectedModel(model);
  };

  // Close the ModelForm
  const handleCloseModelForm = () => {
    setSelectedModel(null);
  };

  // Determine if there are any models or a model in training
  const hasModels = models.length > 0 || currentTrainingModel !== null;

  return (
    <div className="left-menu">
      {/* Display the main menu if no form is active */}
      {!showModelForm && !selectedModel && (
        <>
          {/* Model in training */}
          {currentTrainingModel && (
            <div
              key={currentTrainingModel.id}
              className="model-box training-model"
            >
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
                <p className="model-age">{model.age}</p>
              </div>
            </div>
          ))}

          {/* Create New Model button */}
          <button
            className={`create-button ${
              !hasModels ? 'margin-top-10' : 'margin-top-auto'
            }`}
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
          <button
            className="close-button"
            onClick={handleCloseModelForm}
          >
            ×
          </button>
          <ModelForm model={selectedModel} onClose={handleCloseModelForm} />
        </div>
      )}
    </div>
  );
}

export default LeftMenu;