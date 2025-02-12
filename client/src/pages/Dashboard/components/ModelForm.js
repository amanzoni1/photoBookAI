// ModelForm.js

import React, { useState, useEffect } from "react";
import modelPlaceholder from "./images/bab.png";
import { usePhotoshoot } from "../../../hooks/usePhotoshoot";
import { useCredits } from "../../../contexts/CreditsContext";
import BuyCreditsModal from "../../BuyCreditsModal/BuyCreditsModal";
import "./ModelForm.css";

function ModelForm({ model, onClose, onPhotobooksUpdate }) {
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
        console.error("Error fetching photobooks:", err);
      }
    };
    loadPhotobooks();
  }, [model.id, fetchPhotobooksByModel]);

  const handleSelect = (photobookId, isUnlocked) => {
    if (!isUnlocked) {
      setSelectedPhotobook(photobookId);
    }
  };

  const handleUnlock = async () => {
    if (!selectedPhotobook) return;

    if (credits.photoshoot_credits < 1) {
      setShowBuyCreditsModal(true);
      return;
    }

    try {
      const response = await unlockPhotobook(selectedPhotobook);

      // We now call refresh functions regardless of error to update the UI.
      const updated = await fetchPhotobooksByModel(model.id);
      setPhotobooks(updated);
      setSelectedPhotobook(null);
      await refreshCredits();
      onPhotobooksUpdate();
    } catch (error) {
      console.error("Error unlocking photobook:", error);
      alert(
        error.response?.data?.message || "Unlock failed. Please try again."
      );
    }
  };

  const sortedPhotobooks = [...photobooks].sort((a, b) => {
    if (a.is_unlocked === b.is_unlocked) return 0;
    return a.is_unlocked ? -1 : 1;
  });

  return (
    <div className="model-form">
      <div className="content-wrapper">
        <h2>Manage Model</h2>

        <div className="model-info-container">
          <img
            src={modelPlaceholder}
            alt="Model"
            className="model-form-image"
          />
          <div className="model-info">
            <p>{model.name}</p>
            <p>
              Age:
              {model.config?.age_years
                ? ` ${model.config.age_years} years`
                : ""}
              {model.config?.age_months
                ? ` ${model.config.age_months} months`
                : ""}
            </p>
          </div>
        </div>

        <div className="photobook-list">
          {sortedPhotobooks.map((book) => {
            const isUnlocked = book.is_unlocked;
            const isSelected = selectedPhotobook === book.id;
            return (
              <div
                key={book.id}
                className={`photobook-item ${isUnlocked ? "unlocked" : "locked"}
                          ${!isUnlocked && isSelected ? "selected" : ""}`}
                onClick={() => handleSelect(book.id, isUnlocked)}
              >
                <div>
                  <div className="theme-name">{book.theme_name}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <button
        className="unlock-button"
        onClick={handleUnlock}
        disabled={!selectedPhotobook}
      >
        Unlock Photobook
      </button>

      <BuyCreditsModal
        isOpen={showBuyCreditsModal}
        onClose={() => setShowBuyCreditsModal(false)}
      />
    </div>
  );
}

export default ModelForm;
