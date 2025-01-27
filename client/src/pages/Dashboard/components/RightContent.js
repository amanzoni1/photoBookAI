import React, { useState, useEffect } from 'react';
import axios from 'axios'; // For the blob download
import { usePhotoshoot } from '../../../hooks/usePhotoshoot';
import './RightContent.css';

function RightContent() {
  const [photobooks, setPhotobooks] = useState([]);
  const [imagesByPhotobook, setImagesByPhotobook] = useState({});
  const [lightbox, setLightbox] = useState({ photobookId: null, currentIndex: 0, isOpen: false });
  const { fetchAllPhotobooks, fetchPhotobookImages, loading, error } = usePhotoshoot();

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

  useEffect(() => {
    const loadImagesForUnlocked = async () => {
      const completedUnlocked = photobooks.filter(pb => pb.status === 'COMPLETED' && pb.is_unlocked);
      const requests = completedUnlocked.map(async (book) => {
        try {
          const res = await fetchPhotobookImages(book.id);
          return { photobookId: book.id, images: res.images };
        } catch (err) {
          console.error(`Error fetching images for photobook ${book.id}`, err);
          return { photobookId: book.id, images: [] };
        }
      });
      const results = await Promise.all(requests);

      const newImages = {};
      results.forEach(r => {
        newImages[r.photobookId] = r.images;
      });
      setImagesByPhotobook(newImages);
    };

    if (photobooks.length > 0) {
      loadImagesForUnlocked();
    }
  }, [photobooks, fetchPhotobookImages]);

  // Lightbox
  const openLightbox = (photobookId, index) => {
    setLightbox({ photobookId, currentIndex: index, isOpen: true });
  };
  const closeLightbox = () => {
    setLightbox({ photobookId: null, currentIndex: 0, isOpen: false });
  };
  const prevImage = () => {
    const arr = imagesByPhotobook[lightbox.photobookId] || [];
    setLightbox(prev => ({
      ...prev,
      currentIndex: (prev.currentIndex - 1 + arr.length) % arr.length
    }));
  };
  const nextImage = () => {
    const arr = imagesByPhotobook[lightbox.photobookId] || [];
    setLightbox(prev => ({
      ...prev,
      currentIndex: (prev.currentIndex + 1) % arr.length
    }));
  };
  const downloadImage = async (url) => {
    try {
      const response = await axios.get(url, { responseType: 'blob' });
      const blobUrl = URL.createObjectURL(response.data);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = 'my_image.png';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(blobUrl);
    } catch (err) {
      console.error('Download error:', err);
    }
  };

  let currentImage = null;
  if (lightbox.isOpen && lightbox.photobookId) {
    const arr = imagesByPhotobook[lightbox.photobookId] || [];
    currentImage = arr[lightbox.currentIndex];
  }

  return (
    <div className="right-content">
      <h2 className="right-title">Your PhotoShoots</h2>
      {loading && <p>Loading photobooks or images...</p>}
      {error && <p className="error-message">{error}</p>}

      {photobooks.length === 0 ? (
        <div className="image-placeholder">
          <p>Your photoshoots will be displayed here.</p>
        </div>
      ) : (
        photobooks.map(book => {
          if (book.status !== 'COMPLETED' || !book.is_unlocked) return null;

          const images = imagesByPhotobook[book.id] || [];
          if (images.length === 0) return null;

          // We'll treat the first image as big cover, the rest as thumbs
          const bigCover = images[0];
          const otherImages = images.slice(1);

          // limit the displayed thumbs to 6
          const maxThumbs = 6;
          const thumbsToShow = otherImages.slice(0, maxThumbs);
          const extraCount = otherImages.length - thumbsToShow.length;

          return (
            <div key={book.id} className="photobook-container">
              <h3 className='photobook-title'>{book.theme_name}</h3>

              <div className="photobook-inner">
                {/* Left side: big cover area */}
                <div className="big-cover-area">
                  <img
                    src={bigCover.url}
                    alt="Big cover"
                    className="big-cover"
                    onClick={() => openLightbox(book.id, 0)}
                  />
                </div>

                {/* Right side: thumbs column */}
                <div className="thumbs-column">
                  {thumbsToShow.map((img, idx) => (
                    <img
                      key={img.id || idx}
                      src={img.url}
                      alt={`Thumb ${idx + 1}`}
                      className="small-thumb"
                      onClick={() => openLightbox(book.id, idx + 1)} 
                    />
                  ))}

                  {extraCount > 0 && (
                    <div className="more-label">
                      +{extraCount} more
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })
      )}

      {/* Lightbox Overlay */}
      {lightbox.isOpen && currentImage && (
        <div className="lightbox-overlay">
          <div className="lightbox-content">
            <button className="close-button" onClick={closeLightbox}>×</button>
            <button className="nav-button left" onClick={prevImage}>←</button>

            <img 
              src={currentImage.url}
              alt="Enlarged"
              className="enlarged-image"
            />

            <button
              className="download-button"
              onClick={() => downloadImage(currentImage.url)}
            >
              Download
            </button>

            <button className="nav-button right" onClick={nextImage}>→</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default RightContent;