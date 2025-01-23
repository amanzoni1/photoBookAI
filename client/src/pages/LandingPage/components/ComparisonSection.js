// client/src/pages/LandingPage/components/ComparisonSection.js
import React from 'react';
import './ComparisonSection.css';
import relaxed from './images/relaxed.jpeg';
import messySchedule from './images/messySchedule.webp';

function ComparisonSection() {
  return (
    <section className="comparison-section">
      <div className="comparison-inner">
        <h2 className="section-title">AI Photoshoot vs. Traditional Photography</h2>
        <p className="section-subtitle">
          Discover how our AI approach compares to hiring a conventional photography studio.
        </p>

        <div className="comparison-wrapper">
          {/* AI Photoshoot Column */}
          <div className="comparison-column">
            <div className="comparison-image">
              <img
                src={relaxed}
                alt="AI-generated portrait variations"
                className="comparison-img"
              />
            </div>
            <h3 className="comparison-heading">AI Photoshoot</h3>
            <ul>
              <li>Upload your child’s photos any time—no strict scheduling</li>
              <li>Avoid travel and pricey studio fees</li>
              <li>Receive final results in just a few hours</li>
              <li>Explore multiple themes and styles in a single session</li>
              <li>All from the comfort of home</li>
            </ul>
          </div>

          {/* Traditional Photoshoot Column */}
          <div className="comparison-column">
            <div className="comparison-image">
              <img
                src={messySchedule}
                alt="AI-generated portrait variations"
                className="comparison-img"
              />
            </div>
            <h3 className="comparison-heading">Traditional Photoshoot</h3>
            <ul>
              <li>Find a child-friendly photographer and align schedules</li>
              <li>Drive or commute to a designated studio</li>
              <li>Wait days or even weeks for final edits</li>
              <li>Limited sets and often fewer outfit changes</li>
              <li>Typically more expensive per session</li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}

export default ComparisonSection;