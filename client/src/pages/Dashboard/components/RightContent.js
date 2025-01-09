// src/components/RightContent.js

import React, { useState, useEffect } from 'react';
import { usePhotoshoot } from '../../../hooks/usePhotoshoot';
import './RightContent.css';

/**
 * Helper function to group photobooks by model_id
 */
function groupPhotobooksByModel(photobooks) {
  const grouped = {};

  photobooks.forEach((book) => {
    const modelId = book.model_id || 'unknown';
    if (!grouped[modelId]) {
      grouped[modelId] = {
        model_id: modelId,
        model_name: book.model_name || 'Unnamed Model',
        photobooks: []
      };
    }
    grouped[modelId].photobooks.push(book);
  });

  // Convert the object into an array and sort if you want
  return Object.values(grouped).sort((a, b) =>
    a.model_name.localeCompare(b.model_name)
  );
}

function RightContent() {
  const [groupedPhotobooks, setGroupedPhotobooks] = useState([]);
  const { fetchAllPhotobooks, loading, error } = usePhotoshoot();

  // Where your images are actually stored
  // e.g. baseURL = 'https://my-cdn.com' or from .env
  const baseUrl = process.env.REACT_APP_STORAGE_URL || 'https://my-cdn.com';

  // If your PhotoBook returns 'storage_path' as "bucket/path/to/file.png",
  // we just need to prefix baseUrl + '/' + storage_path to form a URL.
  const getImageUrl = (storagePath) => `${baseUrl}/${storagePath}`;

  useEffect(() => {
    const loadPhotobooks = async () => {
      try {
        const allBooks = await fetchAllPhotobooks();

        // Filter only COMPLETED & unlocked
        const completedUnlocked = allBooks.filter(
          (b) => b.status === 'COMPLETED' 
          // && b.is_unlocked
        );

        // Group them by model
        const byModel = groupPhotobooksByModel(completedUnlocked);
        setGroupedPhotobooks(byModel);
      } catch (err) {
        console.error('Error loading photobooks:', err);
      }
    };
    loadPhotobooks();
  }, [fetchAllPhotobooks]);

  return (
    <div className="right-content">
      <h2 className="right-title">Your PhotoShoots</h2>

      {loading && <p className="loading-text">Loading your photobooks...</p>}
      {error && <p className="error-message">{error}</p>}

      {/* If we have groupedPhotobooks, we show them; otherwise show placeholder */}
      {groupedPhotobooks.length > 0 ? (
        <div className="photobook-gallery">
          {groupedPhotobooks.map((group) => (
            <div key={group.model_id} className="model-photobooks">
              <h3 className="model-title">
                Model: {group.model_name} (ID: {group.model_id})
              </h3>

              {group.photobooks.map((book) => (
                <div key={book.id} className="photobook-container">
                  <h4>{book.name}</h4>
                  <p>Theme: {book.theme_name}</p>

                  {/* Show the images */}
                  <div className="images-grid">
                    {book.images?.map((img, idx) => (
                      <img
                        key={img.id || idx}
                        src={getImageUrl(img.storage_path)}
                        alt={`Photobook ${book.name} - image ${idx + 1}`}
                        className="photobook-image"
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      ) : (
        !loading && (
          <div className="image-placeholder">
            <p>Your photobooks will be displayed here once available.</p>
          </div>
        )
      )}
    </div>
  );
}

export default RightContent;