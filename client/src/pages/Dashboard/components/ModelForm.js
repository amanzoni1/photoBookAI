// ModelForm.js

import React, { useState, useEffect } from 'react';
import './ModelForm.css';
import modelPlaceholder from './images/bab.png';
import { usePhotoshoot } from '../../../hooks/usePhotoshoot';
import { useCredits } from '../../../contexts/CreditsContext';

function ModelForm({ model, onClose }) {
  const [photobooks, setPhotobooks] = useState([]);
  const [selectedPhotobook, setSelectedPhotobook] = useState(null);

  const { fetchPhotobooksByModel, unlockPhotobook } = usePhotoshoot();
  const { credits, purchaseCredits, refreshCredits } = useCredits();

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
    // Don’t select if it’s already unlocked
    if (isUnlocked) return;
    setSelectedPhotobook(photobookId);
  };

  /**
   * Attempt to unlock the currently selected photobook.
   * If user doesn't have enough credits, prompt to purchase
   * but do NOT automatically unlock afterwards.
   */
  const handleUnlock = async () => {
    // 0) Must have a selection
    if (!selectedPhotobook) return;

    // 1) Check if user has enough credits first
    if (credits.photoshoot_credits < 1) {
      const confirmBuy = window.confirm(
        'You do not have enough credits. Purchase 1 photoshoot credit for $9.99?'
      );
      if (confirmBuy) {
        try {
          const result = await purchaseCredits('PHOTOSHOOT', 1);
          if (result.message === 'Purchase successful') {
            alert('Credits purchased successfully! You can now unlock the photobook.');
            // Refresh local credit state
            await refreshCredits();
          } else {
            throw new Error('Purchase failed');
          }
        } catch (err) {
          console.error('Purchase error:', err);
          alert(err.response?.data?.message || 'Failed to purchase credits. Please try again.');
        }
      }
      // Either way (bought or canceled), we stop here so user can press Unlock again
      return;
    }

    // 2) If user DOES have credits, proceed with unlock
    try {
      const response = await unlockPhotobook(selectedPhotobook);
      alert(response.message || 'Photobook unlocked successfully.');

      // Re-fetch photobooks to show updated is_unlocked status
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
        {photobooks.map((book) => {
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
    </div>
  );
}

export default ModelForm;