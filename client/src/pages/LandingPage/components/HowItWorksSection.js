// client/src/pages/LandingPage/components/HowItWorksSection.js
import React from 'react';
import './HowItWorksSection.css';

function HowItWorksSection() {
  return (
    <section className="how-it-works-section">
      <div className="how-it-works-inner">
        <h2 className="section-title">How It Works</h2>
        <p className="section-subtitle">
          Transform ordinary kid photos into studio-quality portraits 
          in three easy steps—no photography skills needed.
        </p>

        <div className="how-steps">
          <div className="how-step">
            <h3>1. Upload Your Child's Photos</h3>
            <p>
              Gather a handful of casual snapshots—new or old. 
              Our AI learns your child’s unique features from these images to produce a custom model.
            </p>
          </div>

          <div className="how-step">
            <h3>2. Our AI Does the Rest</h3>
            <p>
              Within a few hours, we generate an array of stylized portraits. 
              Enjoy multiple poses, outfits, and backdrops—all automatically created.
            </p>
          </div>

          <div className="how-step">
            <h3>3. Preview & Download</h3>
            <p>
              Browse through dozens of professional-quality options 
              and save your favorites. It’s that simple and fast.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

export default HowItWorksSection;