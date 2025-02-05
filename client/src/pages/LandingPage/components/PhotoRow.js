// client/src/components/PhotoRow/PhotoRow.js

import React from "react";
import "./PhotoRow.css";

// Example usage with default images:
import img1 from "./images/img3M.png";
import img2 from "./images/img2.png";
import img3 from "./images/img9M.png";
import img4 from "./images/img1.png";
import img5 from "./images/imgM.png";
import img6 from "./images/img3.png";

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
