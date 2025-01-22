// client/src/pages/LandingPage/components/WhyIsGoodSection.js
import React from 'react';
import './WhyIsGoodSection.css';

function WhyIsGoodSection() {
  return (
    <section className="why-good-section">
      <div className="why-good-inner">
        <h2 className="section-title">Why Our AI Photoshoots Are Perfect for Kids</h2>
        <p className="section-subtitle">
          Say goodbye to expensive studio bookings and scheduling headaches.
          Our advanced AI turns everyday snapshots into unforgettable portraits—in hours, not days.
        </p>

        <div className="benefits-grid">
          <div className="benefit-card">
            <h3>Kid-Friendly & Safe</h3>
            <p>We train our model on your child's photos securely. Privacy and safety are our top priorities.</p>
          </div>
          <div className="benefit-card">
            <h3>Ultra-Fast Turnaround</h3>
            <p>Get professional-quality images in a fraction of the time it takes a traditional studio.</p>
          </div>
          <div className="benefit-card">
            <h3>Budget-Conscious</h3>
            <p>Enjoy premium results without the premium price tag. It’s a studio experience for less.</p>
          </div>
          <div className="benefit-card">
            <h3>Endless Variety</h3>
            <p>
              Choose from countless themes, outfits, or backgrounds—so each portrait truly captures 
              your child's personality.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

export default WhyIsGoodSection;