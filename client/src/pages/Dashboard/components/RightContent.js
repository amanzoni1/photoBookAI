// RightContent.js

import React, { useState, useEffect } from "react";
import axios from "axios";
import { useModel } from "../../../hooks/useModel";
import { usePhotoshoot } from "../../../hooks/usePhotoshoot";
import "./RightContent.css";

function RightContent({ photobooks, onPhotobooksUpdate }) {
  const { fetchModels } = useModel();
  const {
    fetchPhotobookImages,
    deletePhotobook,
    deletePhotobookImage,
    loading,
    error,
  } = usePhotoshoot();
  const [models, setModels] = useState([]);
  const [imagesByPhotobook, setImagesByPhotobook] = useState({});
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteType, setDeleteType] = useState(null);
  const [itemToDelete, setItemToDelete] = useState(null);
  const [lightbox, setLightbox] = useState({
    photobookId: null,
    currentIndex: 0,
    isOpen: false,
  });

  const openDeleteModal = (type, id) => {
    setDeleteType(type);
    setItemToDelete(id);
    setShowDeleteModal(true);
  };

  // Load models once on mount
  useEffect(() => {
    const loadModels = async () => {
      try {
        const fetchedModels = await fetchModels();
        setModels(fetchedModels);
      } catch (err) {
        console.error("Error loading models:", err);
      }
    };
    loadModels();
  }, [fetchModels]);

  // When the photobooks prop changes, fetch the images for the unlocked ones.
  useEffect(() => {
    const loadImagesForUnlocked = async () => {
      const completedUnlocked = photobooks.filter(
        (pb) => pb.status === "COMPLETED" && pb.is_unlocked
      );
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
      results.forEach((r) => {
        newImages[r.photobookId] = r.images;
      });
      setImagesByPhotobook(newImages);
    };
    if (photobooks.length > 0) {
      loadImagesForUnlocked();
    }
  }, [photobooks, fetchPhotobookImages]);

  // Delete handler: if deleting an image, update local state;
  // if deleting an entire photobook, trigger a refresh via onPhotobooksUpdate.
  const handleDelete = async () => {
    try {
      if (deleteType === "image") {
        await deletePhotobookImage(lightbox.photobookId, itemToDelete);
        setImagesByPhotobook((prev) => ({
          ...prev,
          [lightbox.photobookId]: prev[lightbox.photobookId].filter(
            (img) => img.id !== itemToDelete
          ),
        }));
        closeLightbox();
      } else {
        await deletePhotobook(itemToDelete);
        onPhotobooksUpdate(); // refresh photobooks in the parent Dashboard
      }
    } catch (err) {
      console.error("Error during deletion:", err);
    } finally {
      setShowDeleteModal(false);
    }
  };

  // Lightbox helper functions
  const openLightbox = (photobookId, index) => {
    setLightbox({ photobookId, currentIndex: index, isOpen: true });
  };
  const closeLightbox = () => {
    setLightbox({ photobookId: null, currentIndex: 0, isOpen: false });
  };
  const prevImage = () => {
    const arr = imagesByPhotobook[lightbox.photobookId] || [];
    setLightbox((prev) => ({
      ...prev,
      currentIndex: (prev.currentIndex - 1 + arr.length) % arr.length,
    }));
  };
  const nextImage = () => {
    const arr = imagesByPhotobook[lightbox.photobookId] || [];
    setLightbox((prev) => ({
      ...prev,
      currentIndex: (prev.currentIndex + 1) % arr.length,
    }));
  };

  const downloadImage = async (url) => {
    try {
      const response = await axios.get(url, { responseType: "blob" });
      const blobUrl = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = "my_image.png";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(blobUrl);
    } catch (err) {
      console.error("Download error:", err);
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
        photobooks.map((book) => {
          if (book.status !== "COMPLETED" || !book.is_unlocked) return null;
          const images = imagesByPhotobook[book.id] || [];
          if (images.length === 0) return null;
          const bigCover = images[0];
          const otherImages = images.slice(1);
          return (
            <div key={book.id} className="photobook-container">
              <div className="photobook-header">
                <h3 className="photobook-title">
                  {models.find((m) => m.id === book.model_id)?.name} -{" "}
                  {book.theme_name}
                </h3>
                <button
                  onClick={() => openDeleteModal("photoshoot", book.id)}
                  className="album-delete-button"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    height="24px"
                    viewBox="0 -960 960 960"
                    width="24px"
                    fill="#fff"
                  >
                    <path d="M267.33-120q-27.5 0-47.08-19.58-19.58-19.59-19.58-47.09V-740H160v-66.67h192V-840h256v33.33h192V-740h-40.67v553.33q0 27-19.83 46.84Q719.67-120 692.67-120H267.33Zm425.34-620H267.33v553.33h425.34V-740Zm-328 469.33h66.66v-386h-66.66v386Zm164 0h66.66v-386h-66.66v386ZM267.33-740v553.33V-740Z" />
                  </svg>
                </button>
              </div>
              <div className="photobook-inner">
                <div className="big-cover-area">
                  <img
                    src={bigCover.url}
                    alt="Big cover"
                    className="big-cover"
                    onClick={() => openLightbox(book.id, 0)}
                  />
                </div>
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
                  {otherImages.length > 4 && (
                    <div
                      className="more-overlay"
                      onClick={() => openLightbox(book.id, 0)}
                    >
                      +{otherImages.length - 4} more
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })
      )}

      {lightbox.isOpen && currentImage && (
        <div className="lightbox-overlay">
          <div className="lightbox-content">
            <button className="close-button" onClick={closeLightbox}>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                height="40px"
                viewBox="0 -960 960 960"
                width="40px"
                fill="#fff"
              >
                <path d="m251.33-204.67-46.66-46.66L433.33-480 204.67-708.67l46.66-46.66L480-526.67l228.67-228.66 46.66 46.66L526.67-480l228.66 228.67-46.66 46.66L480-433.33 251.33-204.67Z" />
              </svg>
            </button>

            <button
              onClick={() => openDeleteModal("image", currentImage.id)}
              className="delete-button"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                height="40px"
                viewBox="0 -960 960 960"
                width="40px"
                fill="#fff"
              >
                <path d="M267.33-120q-27.5 0-47.08-19.58-19.58-19.59-19.58-47.09V-740H160v-66.67h192V-840h256v33.33h192V-740h-40.67v553.33q0 27-19.83 46.84Q719.67-120 692.67-120H267.33Zm425.34-620H267.33v553.33h425.34V-740Zm-328 469.33h66.66v-386h-66.66v386Zm164 0h66.66v-386h-66.66v386ZM267.33-740v553.33V-740Z" />
              </svg>
            </button>

            <button
              className="download-button"
              onClick={() => downloadImage(currentImage.url)}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                height="40px"
                viewBox="0 -960 960 960"
                width="40px"
                fill="#fff"
              >
                <path d="M480-315.33 284.67-510.67l47.33-48L446.67-444v-356h66.66v356L628-558.67l47.33 48L480-315.33ZM226.67-160q-27 0-46.84-19.83Q160-199.67 160-226.67V-362h66.67v135.33h506.66V-362H800v135.33q0 27-19.83 46.84Q760.33-160 733.33-160H226.67Z" />
              </svg>
            </button>

            <img
              src={currentImage.url}
              alt="Enlarged"
              className="enlarged-image"
            />

            <button className="nav-button left" onClick={prevImage}>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                height="40px"
                viewBox="0 -960 960 960"
                width="40px"
                fill="#fff"
              >
                <path d="M650-80 250-480l400-400 61 61.67L372.67-480 711-141.67 650-80Z" />
              </svg>
            </button>
            <button className="nav-button right" onClick={nextImage}>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                height="40px"
                viewBox="0 -960 960 960"
                width="40px"
                fill="#fff"
              >
                <path d="m309.67-81.33-61-61.67L587-481.33 248.67-819.67l61-61.66 400 400-400 400Z" />
              </svg>
            </button>

            <div className="lightbox-preview-strip">
              {imagesByPhotobook[lightbox.photobookId]?.map((img, idx) => (
                <img
                  key={img.id || idx}
                  src={img.url}
                  alt={`Preview ${idx + 1}`}
                  className={`preview-thumb ${
                    idx === lightbox.currentIndex ? "active" : ""
                  }`}
                  onClick={() =>
                    setLightbox((prev) => ({ ...prev, currentIndex: idx }))
                  }
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {showDeleteModal && deleteType === "photoshoot" && (
        <div className="modal-overlay">
          <div className="delete-modal">
            <div className="delete-modal-header">
              <h3>Delete Photoshoot</h3>
              <button
                className="modal-close"
                onClick={() => setShowDeleteModal(false)}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  height="24px"
                  viewBox="0 -960 960 960"
                  width="24px"
                  fill="#fff"
                >
                  <path d="M251.33-204.67-46.66-46.66L433.33-480 204.67-708.67l46.66-46.66L480-526.67l228.67-228.66 46.66 46.66L526.67-480l228.66 228.67-46.66 46.66L480-433.33 251.33-204.67Z" />
                </svg>
              </button>
            </div>
            <p>
              This action is irreversible. Are you sure you want to delete this
              photoshoot?
            </p>
            <div className="delete-modal-actions">
              <button
                className="modal-cancel"
                onClick={() => setShowDeleteModal(false)}
              >
                Cancel
              </button>
              <button className="modal-delete-btn" onClick={handleDelete}>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  height="24px"
                  viewBox="0 -960 960 960"
                  width="24px"
                  fill="#fff"
                >
                  <path d="M267.33-120q-27.5 0-47.08-19.58-19.58-19.59-19.58-47.09V-740H160v-66.67h192V-840h256v33.33h192V-740h-40.67v553.33q0 27-19.83 46.84Q719.67-120 692.67-120H267.33Zm425.34-620H267.33v553.33h425.34V-740Zm-328 469.33h66.66v-386h-66.66v386Zm164 0h66.66v-386h-66.66v386ZM267.33-740v553.33V-740Z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default RightContent;
