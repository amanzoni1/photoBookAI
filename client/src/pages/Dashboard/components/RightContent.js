import React, { useState, useEffect } from 'react';
import { usePhotoshoot } from '../../../hooks/usePhotoshoot';
import './RightContent.css';

function RightContent() {
  const [photobooks, setPhotobooks] = useState([]);
  const { fetchAllPhotobooks } = usePhotoshoot();

  useEffect(() => {
    const loadPhotobooks = async () => {
      try {
        const books = await fetchAllPhotobooks();
        setPhotobooks(books.filter(book => book.status === 'COMPLETED'));
      } catch (err) {
        console.error('Error loading photobooks:', err);
      }
    };
    loadPhotobooks();
  }, [fetchAllPhotobooks]);

  const getImageUrl = (storagePath) => {
    const baseUrl = process.env.REACT_APP_STORAGE_URL;
    return `${baseUrl}/${storagePath}`;
  };

  return (
    <div className="right-content">
      <h2 className='right-title'>Your PhotoShoots</h2>
      {photobooks.length > 0 ? (
        <div className="image-gallery">
          {photobooks.map(book => (
            <div key={book.id} className="photobook-container">
              <h3>{book.name}</h3>
              <p>Theme: {book.theme_name}</p>
              <div className="images-grid">
                {book.images?.map((image, index) => (
                  <img 
                    key={image.id || index}
                    src={getImageUrl(image.storage_path)}
                    alt={`Photoshoot ${index + 1}`}
                    className="photobook-image"
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="image-placeholder">
          <p>Your photobooks will be displayed here.</p>
        </div>
      )}
    </div>
  );
}

export default RightContent;