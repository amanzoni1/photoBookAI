// ModelForm.js

import React, { useState, useEffect } from 'react';
import './ModelForm.css';
import modelPlaceholder from './images/bab.png';
import { usePhotoshoot } from '../../../hooks/usePhotoshoot';
import { useCredits } from '../../../contexts/CreditsContext';
import BuyCreditsModal from '../../BuyCreditsModal/BuyCreditsModal';

function ModelForm({ model, onClose }) {
  const [photobooks, setPhotobooks] = useState([]);
  const [selectedPhotobook, setSelectedPhotobook] = useState(null);
  const [showBuyCreditsModal, setShowBuyCreditsModal] = useState(false);
  const { fetchPhotobooksByModel, unlockPhotobook } = usePhotoshoot();
  const { credits, refreshCredits } = useCredits();

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

  const handleSelect = (photobookId, isUnlocked) => {
    if (!isUnlocked) {
      setSelectedPhotobook(photobookId);
    }
  };

  /**
   * Attempt to unlock the currently selected photobook.
   * If user has enough `photoshoot_credits`, do it. Otherwise open BuyCreditsModal.
   */
  const handleUnlock = async () => {
    if (!selectedPhotobook) return;

    // 1) Check if user has enough PHOTOSHOOT credits:
    if (credits.photoshoot_credits < 1) {
      setShowBuyCreditsModal(true);
      return;
    }

    // 2) If user DOES have enough credits, call the unlock endpoint
    try {
      const response = await unlockPhotobook(selectedPhotobook);
      alert(response.message || 'Photobook unlocked successfully.');

      // Re-fetch photobooks to show updated is_unlocked
      const updated = await fetchPhotobooksByModel(model.id);
      setPhotobooks(updated);

      // Clear selection
      setSelectedPhotobook(null);

      // Refresh credits in case the server decremented them
      await refreshCredits();

    } catch (error) {
      console.error('Error unlocking photobook:', error);
      alert(error.response?.data?.message || 'Unlock failed. Please try again.');
    }
  };

  return (
    <div className="model-form">
      <h2>Manage Model: {model.name}</h2>
      <img src={modelPlaceholder} alt="Model" className="model-form-image" />

      <p>
        Age:
        {model.config?.age_years ? ` ${model.config.age_years} years` : ''}
        {model.config?.age_months ? ` ${model.config.age_months} months` : ''}
      </p>
      <p>Model ID: {model.id}</p>

      <div className="photobook-list">
        {photobooks.map(book => {
          const isUnlocked = book.is_unlocked;
          const isSelected = selectedPhotobook === book.id;
          return (
            <div
              key={book.id}
              className={`photobook-item ${isUnlocked ? 'unlocked' : 'locked'} 
                          ${!isUnlocked && isSelected ? 'selected' : ''}`}
              onClick={() => handleSelect(book.id, isUnlocked)}
            >
              <div>
                <div className="theme-name">{book.theme_name}</div>
              </div>
              <div>
                {isUnlocked ? (
                  <span className="status-unlocked">Unlocked</span>
                ) : (
                  <span className="status-locked">Locked</span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <button
        className="unlock-button"
        onClick={handleUnlock}
        disabled={!selectedPhotobook}
      >
        Unlock Photobook
      </button>

      {/* Insert the buy credits modal if user doesn't have enough PHOTOSHOOT credits */}
      <BuyCreditsModal
        isOpen={showBuyCreditsModal}
        onClose={() => setShowBuyCreditsModal(false)}
      />
    </div>
  );
}

export default ModelForm;