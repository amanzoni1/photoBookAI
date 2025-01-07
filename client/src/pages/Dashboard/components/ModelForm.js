// src/components/ModelForm.js

import React, { useState, useEffect } from 'react';
import './ModelForm.css';
import modelPlaceholder from './images/bab.png';
import { usePhotoshoot } from '../../../hooks/usePhotoshoot';

function ModelForm({ model, onClose }) {
  const [photobooks, setPhotobooks] = useState([]);
  const [selectedPhotobook, setSelectedPhotobook] = useState(null);
  const { fetchPhotobooksByModel } = usePhotoshoot();

  useEffect(() => {
    const loadPhotobooks = async () => {
      try {
        const books = await fetchPhotobooksByModel(model.id);
        setPhotobooks(books);
      } catch (err) {
        console.error('Error fetching photobooks:', err);
      }
    };
    loadPhotobooks();
  }, [model.id, fetchPhotobooksByModel]);

  return (
    <div className="model-form">
      <h2>Manage Model: {model.name}</h2>
      <img src={modelPlaceholder} alt="Model" className="model-form-image" />
      <p>Age: {model.config?.age_years ? `${model.config.age_years} years` : ''} 
          {model.config?.age_months ? ` ${model.config.age_months} months` : ''}</p>
      <p>ModelId: {model.id}</p>

      <div className="photobook-list">
        {photobooks.map((book) => (
          <div 
            key={book.id} 
            className={`photobook-item ${selectedPhotobook === book.id ? 'selected' : ''}`}
            onClick={() => setSelectedPhotobook(book.id)}
          >
            {book.theme_name}
          </div>
        ))}
      </div>

      <button 
        className="create-photobook-button"
        onClick={() => {
          if (selectedPhotobook) {
            console.log('Unlocking photobook:', selectedPhotobook);
            // Add unlock logic here
          } else {
            console.log('Please select a photobook first');
          }
        }}
      >
        {selectedPhotobook ? 'Unlock Photobook' : 'Select a Photobook'}
      </button>
    </div>
  );
}

export default ModelForm;