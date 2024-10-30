import React, { useState, useEffect } from 'react';
import axios from '../../../utils/axiosConfig';
import './RightContent.css';

function RightContent() {
  const [images, setImages] = useState([]);

  useEffect(() => {
    // Fetch generated images from the server
    const fetchImages = async () => {
      try {
        const res = await axios.get('/api/generated-images');
        setImages(res.data.images);
      } catch (err) {
        console.error(err.response?.data);
      }
    };

    fetchImages();
  }, []);

  return (
    <div className="right-content">
      <h2 className='right-title'>Your Photobooks</h2>
      {images.length > 0 ? (
        <div className="image-gallery">
          {images.map(image => (
            <img key={image.id} src={image.url} alt="Generated" />
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