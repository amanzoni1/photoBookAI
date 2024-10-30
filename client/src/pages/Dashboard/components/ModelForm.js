// src/components/ModelForm.js

import React from 'react';
import './ModelForm.css';
import modelPlaceholder from './images/bab.png';

function ModelForm({ model, onClose }) {
  return (
    <div className="model-form">
      <h2>Manage Model: {model.name}</h2>
      <img src={modelPlaceholder} alt="Model" className="model-form-image" />
      <p>Age: {model.age}</p>
      <p>This is a placeholder for managing the model.</p>
      {/* Add more options and functionalities as needed */}
      <div className="photobook-list">
        <label>
          <input type="radio" name="photobook" value="Photobook 1" />
          Photobook 1
        </label>
        <label>
          <input type="radio" name="photobook" value="Photobook 2" />
          Photobook 2
        </label>
        {/* Add more photobook options as needed */}
      </div>
      <button className="create-photobook-button">Create Photobook</button>
    </div>
  );
}

export default ModelForm;