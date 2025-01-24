// client/src/components/PhotoRow/PhotoRow.js

import React from 'react';
import './PhotoRow.css';

// Example usage with default images:
// If you want each PhotoRow to have dynamic images, accept them as props.
import img1 from './images/ex.png';
import img2 from './images/ex1.png';
import img3 from './images/ex2.png';
import img4 from './images/ex3.png';
// import img5 from './images/img5.png';

function PhotoRow() {
  return (
    <div className="photo-row">
      <img className="photo-1" src={img1} alt="Example photo 1" />
      <img className="photo-2" src={img2} alt="Example photo 2" />
      <img className="photo-3" src={img3} alt="Example photo 3" />
      <img className="photo-4" src={img4} alt="Example photo 4" />
      <img className="photo-5" src={img1} alt="Example photo 5" />
      <img className="photo-6" src={img2} alt="Example photo 6" />
    </div>
  );
}

export default PhotoRow;