// src/components/RightContent.js

import React, { useState, useEffect } from 'react';
import { usePhotoshoot } from '../../../hooks/usePhotoshoot';
import './RightContent.css';

function RightContent() {
  const [photobooks, setPhotobooks] = useState([]);
  const [imagesByPhotobook, setImagesByPhotobook] = useState({}); 

  const {
    fetchAllPhotobooks,
    fetchPhotobookImages,
    loading,
    error
  } = usePhotoshoot();

  /**
   * 1) Fetch all photobooks on mount
   */
  useEffect(() => {
    const loadPhotobooks = async () => {
      try {
        const books = await fetchAllPhotobooks();
        setPhotobooks(books);
      } catch (err) {
        console.error('Error loading photobooks:', err);
      }
    };
    loadPhotobooks();
  }, [fetchAllPhotobooks]);

  /**
   * 2) Once we have photobooks, filter them to only COMPLETED & unlocked,
   *    then fetch images for those books.
   */
  useEffect(() => {
    const loadImagesForUnlocked = async () => {
      const completedUnlocked = photobooks.filter(pb =>
        pb.status === 'COMPLETED' && pb.is_unlocked
      );

      const requests = completedUnlocked.map(async (book) => {
        try {
          const res = await fetchPhotobookImages(book.id);
          return {
            photobookId: book.id,
            images: res.images 
          };
        } catch (err) {
          console.error(`Error fetching images for photobook ${book.id}`, err);
          return { photobookId: book.id, images: [] };
        }
      });

      // Wait for all image fetches to finish
      const results = await Promise.all(requests);

      // Build { photobookId: images[] }
      const newImagesByPb = {};
      results.forEach(r => {
        newImagesByPb[r.photobookId] = r.images;
      });

      setImagesByPhotobook(newImagesByPb);
    };

    if (photobooks.length > 0) {
      loadImagesForUnlocked();
    }
  }, [photobooks, fetchPhotobookImages]);

  return (
    <div className="right-content">
      <h2 className="right-title">Your PhotoShoots</h2>

      {loading && <p className="loading-text">Loading photobooks or images...</p>}
      {error && <p className="error-message">{error}</p>}

      {photobooks.length === 0 ? (
        <div className="image-placeholder">
          <p>Your photobooks will be displayed here.</p>
        </div>
      ) : (
        photobooks.map((book) => {
          if (book.status !== 'COMPLETED' || !book.is_unlocked) {
            return null;
          }

          const images = imagesByPhotobook[book.id] || [];

          return (
            <div key={book.id} className="photobook-container">
              <h3>{book.theme_name}</h3>
              {/* We know is_unlocked is true here, so no locked message */}

              <div className="images-grid">
                {images.map((img, idx) => (
                  <img
                    key={img.id || idx}
                    src={img.url}
                    alt={`Photoshoot image ${idx + 1}`}
                    className="photobook-image"
                  />
                ))}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}

export default RightContent;