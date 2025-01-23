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
            <div className="step-content left">
              <svg className="step-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                <path fill="currentColor" d="M3 4V1h2v3h3v2H5v3H3V6H0V4h3zm3 6V7h3V4h7l1.83 2H21c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H5c-1.1 0-2-.9-2-2V10h3zm7 9c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5z" />
              </svg>
              <div className="step-text">
                <h3>1. Upload Your Child's Photos</h3>
                <p>
                  Gather a handful of casual snapshots—new or old.
                  Our AI learns your child’s unique features from these images to produce a custom model.
                </p>
              </div>
            </div>
          </div>

          <div className="how-step">
            <div className="step-content">
              <div className="step-text">
                <h3>2. Our AI Does the Rest</h3>
                <p>
                  Within a few hours, we generate an array of stylized portraits.
                  Enjoy multiple poses, outfits, and backdrops—all automatically created.
                </p>
              </div>
              <svg className="step-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                <path fill="currentColor" d="M20 6h-4V4c0-1.11-.89-2-2-2h-4c-1.11 0-2 .89-2 2v2H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-6 0h-4V4h4v2z" />
              </svg>
            </div>
          </div>

          <div className="how-step">
            <div className="step-content left">
              <svg className="step-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                <path fill="currentColor" d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm3.5-9c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5zm-7 0c.83 0 1.5-.67 1.5-1.5S9.33 8 8.5 8 7 8.67 7 9.5 7.67 11 8.5 11zm3.5 6.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z" />
              </svg>
              <div className="step-text">
                <h3>3. Preview & Download</h3>
                <p>
                  Browse through dozens of professional-quality options
                  and save your favorites. It’s that simple and fast.
                </p>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section >
  );
}

export default HowItWorksSection;