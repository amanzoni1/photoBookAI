// client/src/pages/LandingPage/components/HeroSection.js

import React from 'react';
import { Link } from 'react-router-dom';
import GradientBackground from './GradientBackground';
import './HeroSection.css';

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
            Get professional, share-worthy portraits in minutes.
            Skip the scheduling, travel, and costs of a physical studio —
            our AI photo generator does it all from your favorite device.
          </h2>

          <Link to="/signup" className="cta-button">
            Get Started Now
          </Link>
        </div>

        {/* Right column: hero image (example) */}
        <div className="hero-image">
          <img
            src="https://via.placeholder.com/500x400.png?text=Your+Hero+Image"
            alt="Example of AI-generated child photoshoot"
          />
        </div>
      </div>
    </section>
  );
}

export default HeroSection;