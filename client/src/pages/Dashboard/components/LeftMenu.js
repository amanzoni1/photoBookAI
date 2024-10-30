// LeftMenu.js

import React, { useState } from 'react';
import './LeftMenu.css';
import ModelCreationForm from './ModelCreationForm';

function LeftMenu() {
  const [hasAccess, setHasAccess] = useState(false);
  const [showModelForm, setShowModelForm] = useState(false);
  const [models, setModels] = useState([]);
  const [currentTrainingModel, setCurrentTrainingModel] = useState(null);

  const handleCreateModelClick = () => {
    if (hasAccess) {
      setShowModelForm(true);
    } else {
      const confirmed = window.confirm('You need to purchase access to create a model. Proceed to payment?');
      if (confirmed) {
        setHasAccess(true);
        alert('Payment successful! You can now create a model.');
        setShowModelForm(true);
      }
    }
  };

  const handleTrainingStart = (modelName) => {
    setShowModelForm(false);

    // Create a placeholder for the model being trained
    const newModel = {
      id: Date.now(),
      name: modelName,
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

  return (
    <div className="left-menu">
      {/* Hide the main content when the model creation form is open */}
      {!showModelForm ? (
        <>
          {/* Models at the top */}
          {models.map(model => (
            <div key={model.id} className="model-box">
              <p>{model.name}</p>
              {/* Add other model details or images */}
            </div>
          ))}

          {/* Model in training */}
          {currentTrainingModel && (
            <div key={currentTrainingModel.id} className="model-box">
              <p>{currentTrainingModel.name}</p>
              <div className="loading-indicator">
                <div className="spinner"></div>
                <p>Training in progress...</p>
              </div>
            </div>
          )}

          {/* Create New Model button at the bottom */}
          <button className="create-button" onClick={handleCreateModelClick}>
            <span className="plus-icon">+</span>
            <span>Create a model</span>
          </button>
        </>
      ) : (
        /* Model creation form with close button */
        <div className="model-creation-container">
          <button className="close-button" onClick={() => setShowModelForm(false)}>
            ×
          </button>
          <ModelCreationForm
            onClose={() => setShowModelForm(false)}
            onTrainingStart={handleTrainingStart}
          />
        </div>
      )}
    </div>
  );
}

export default LeftMenu;