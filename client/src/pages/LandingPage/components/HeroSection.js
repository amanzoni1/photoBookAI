// client/src/pages/LandingPage/LandingPage.js

import React from 'react';
import './HeroSection.css'; 
import { Link } from 'react-router-dom';
import GradientBackground from './GradientBackground'

function HeroSection() {
  return (
    <div className="landing-container">
      <GradientBackground />
      <div className="landing-content">
        <h1 className="gradient-text">
          Experience Magical AI-Generated Photoshoots for Your Little Ones
        </h1>
        <p className="subtitle">
          Transform your child's moments into stunning art with the power of AI.
        </p>
        <Link to="/signup" className="cta-button">
          Get Started
        </Link>
      </div>
    </div>
  );
}

export default HeroSection;