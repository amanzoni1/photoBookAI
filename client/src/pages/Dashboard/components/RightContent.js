import React, { useState, useEffect } from 'react';
import axios from 'axios'; // For the blob download
import { useModel } from '../../../hooks/useModel';
import { usePhotoshoot } from '../../../hooks/usePhotoshoot';
import './RightContent.css';

function RightContent() {
  const { fetchModels } = useModel();
  const { fetchAllPhotobooks, fetchPhotobookImages, loading, error } = usePhotoshoot();
  const [models, setModels] = useState([]);
  const [photobooks, setPhotobooks] = useState([]);
  const [imagesByPhotobook, setImagesByPhotobook] = useState({});
  const [lightbox, setLightbox] = useState({ photobookId: null, currentIndex: 0, isOpen: false });

  useEffect(() => {
    const loadModels = async () => {
      try {
        const fetchedModels = await fetchModels();
        setModels(fetchedModels);
      } catch (err) {
        console.error('Error loading models:', err);
      }
    };
    loadModels();
  }, [fetchModels]);

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
      {loading && <p>Loading photobooks or images...</p>}
      {error && <p className="error-message">{error}</p>}

      {photobooks.length === 0 ? (
        <div className="image-placeholder">
          <h2 className="right-title">Your PhotoShoots</h2>
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
              <h3 className='photobook-title'>
                {models.find(m => m.id === book.model_id)?.name} - {book.theme_name}
              </h3>

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
                  {otherImages.slice(0, 4).map((img, idx) => (
                    <img
                      key={img.id || idx}
                      src={img.url}
                      alt={`Thumb ${idx + 1}`}
                      className="small-thumb"
                      onClick={() => openLightbox(book.id, idx + 1)}
                    />
                  ))}
                  {extraCount > 0 && (
                    <div
                      className="more-overlay"
                      onClick={() => openLightbox(book.id, 0)}
                    >
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
            <button className="close-button" onClick={closeLightbox}>
              <svg xmlns="http://www.w3.org/2000/svg" height="40px" viewBox="0 -960 960 960" width="40px" fill="#fff">
                <path d="m251.33-204.67-46.66-46.66L433.33-480 204.67-708.67l46.66-46.66L480-526.67l228.67-228.66 46.66 46.66L526.67-480l228.66 228.67-46.66 46.66L480-433.33 251.33-204.67Z" />
              </svg>
            </button>
            <button className="nav-button left" onClick={prevImage}>
              <svg xmlns="http://www.w3.org/2000/svg" height="40px" viewBox="0 -960 960 960" width="40px" fill="#fff">
                <path d="M650-80 250-480l400-400 61 61.67L372.67-480 711-141.67 650-80Z" />
              </svg>
            </button>

            <img
              src={currentImage.url}
              alt="Enlarged"
              className="enlarged-image"
            />

            <button className="download-button" onClick={() => downloadImage(currentImage.url)}>
              <svg xmlns="http://www.w3.org/2000/svg" height="40px" viewBox="0 -960 960 960" width="40px" fill="#fff">
                <path d="M480-315.33 284.67-510.67l47.33-48L446.67-444v-356h66.66v356L628-558.67l47.33 48L480-315.33ZM226.67-160q-27 0-46.84-19.83Q160-199.67 160-226.67V-362h66.67v135.33h506.66V-362H800v135.33q0 27-19.83 46.84Q760.33-160 733.33-160H226.67Z" />
              </svg>
            </button>

            <button className="nav-button right" onClick={nextImage}>
              <svg xmlns="http://www.w3.org/2000/svg" height="40px" viewBox="0 -960 960 960" width="40px" fill="#fff">
                <path d="m309.67-81.33-61-61.67L587-481.33 248.67-819.67l61-61.66 400 400-400 400Z" />
              </svg>
            </button>

            <div className="lightbox-preview-strip">
              {imagesByPhotobook[lightbox.photobookId]?.map((img, idx) => (
                <img
                  key={img.id || idx}
                  src={img.url}
                  alt={`Preview ${idx + 1}`}
                  className={`preview-thumb ${idx === lightbox.currentIndex ? 'active' : ''}`}
                  onClick={() => setLightbox(prev => ({ ...prev, currentIndex: idx }))}
                />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default RightContent;