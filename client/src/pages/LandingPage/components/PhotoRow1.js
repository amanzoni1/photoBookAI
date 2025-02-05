// client/src/components/PhotoRow/PhotoRow1.js

import React from "react";
import "./PhotoRow1.css";

// Example usage with default images:
import img1 from "./images/img4.png";
import img2 from "./images/img9M.png";
import img3 from "./images/img7.png";
import img4 from "./images/img7M.png";
import img5 from "./images/img9.png";
import img6 from "./images/img5M.png";

function PhotoRow() {
  return (
    <div className="photo-row">
      <img
        className="photo-1"
        src={img1}
        alt="Smiling child in a fairytale-themed AI photoshoot 1"
      />
      <img
        className="photo-2"
        src={img2}
        alt="Smiling child in a fairytale-themed AI photoshoot 2"
      />
      <img
        className="photo-3"
        src={img3}
        alt="Smiling child in a fairytale-themed AI photoshoot 3"
      />
      <img
        className="photo-4"
        src={img4}
        alt="Smiling child in a fairytale-themed AI photoshoot 4"
      />
      <img
        className="photo-5"
        src={img5}
        alt="Smiling child in a fairytale-themed AI photoshoot 5"
      />
      <img
        className="photo-6"
        src={img6}
        alt="Smiling child in a fairytale-themed AI photoshoot 6"
      />
    </div>
  );
}

export default PhotoRow;
