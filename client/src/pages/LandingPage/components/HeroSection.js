// client/src/pages/LandingPage/components/HeroSection.js
import React from "react";
import { Link } from "react-router-dom";
import GradientBackground from "./GradientBackground";
import "./HeroSection.css";

// Example: two images for the right column
import childImgTop from "./images/img9M.png";
import childImgBottom from "./images/img5.png";

function HeroSection() {
  return (
    <section className="hero-section">
      <GradientBackground />

      <div className="hero-inner">
        {/* Left column: text content */}
        <div className="hero-text">
          <p className="hero-tagline">No Photographer Needed</p>
          <h1 className="hero-title">
            Professional Quality Photoshoots for Your Little Ones
          </h1>
          <h2 className="hero-subtitle">
            Get professional, share-worthy portraits in minutes. Skip the
            scheduling, travel, and costs of a physical studio — our AI photo
            generator does it all from your favorite device.
          </h2>
          <Link to="/login" className="cta-button">
            Get Started Now
          </Link>
        </div>

        {/* Right column: 2 images stacked with tilt */}
        <div className="hero-images">
          {/* Top (smaller, tilted) */}
          <img
            className="top-photo"
            src={childImgTop}
            alt="Child photoshoot top"
          />
          {/* Bottom (bigger, slight tilt) */}
          <img
            className="bottom-photo"
            src={childImgBottom}
            alt="Child photoshoot bottom"
          />
        </div>
      </div>
    </section>
  );
}

export default HeroSection;
