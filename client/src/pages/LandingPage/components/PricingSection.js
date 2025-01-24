// client/src/pages/LandingPage/components/PricingSection.js

import React from 'react';
import './PricingSection.css';

function PricingSection({ id }) {
  return (
    <section id={id} className="pricing-section">
      <div className="pricing-inner">

        {/* Heading area */}
        <h2 className="section-title">Affordable AI Photoshoots for Kids</h2>
        <p className="section-subtitle">
          Traditional children’s photoshoots can easily cost $200 or more. Our packages start 
          at just $19.99—so you save both time and money without sacrificing quality.
        </p>

        {/* COMPLETE BUNDLES */}
        <h3 className="pricing-category-title">Bundle Deals</h3>
        <div className="pricing-grid bundle-grid">
          {/* 1) 1 Model + 2 Photoshoots */}
          <div className="price-card bundle-card">
            <h4 className="plan-title">1 Model + 2 Photoshoot Credits</h4>
            <p className="plan-price">$19.99</p>
            <ul className="plan-features">
              <li><span className="checkmark">✓</span> Perfect for one child</li>
              <li><span className="checkmark">✓</span> Train 1 unique model</li>
              <li><span className="checkmark">✓</span> Generate 2 separate AI photoshoots</li>
              <li><span className="checkmark">✓</span> Enjoy lifelike results within couple hours</li>
            </ul>
            <button className="cta-button-credits">Buy Now</button>
          </div>

          {/* 2) 2 Models + 5 Photoshoots */}
          <div className="price-card bundle-card">
            <h4 className="plan-title">2 Models + 5 Photoshoot Credits</h4>
            <p className="plan-price">$34.99</p>
            <ul className="plan-features">
              <li><span className="checkmark">✓</span> Great for siblings or best friends</li>
              <li><span className="checkmark">✓</span> Train 2 separate models</li>
              <li><span className="checkmark">✓</span> 5 photoshoot sets in total</li>
              <li><span className="checkmark">✓</span> Fast, flexible, and cost-effective</li>
            </ul>
            <button className="cta-button-credits">Buy Now</button>
          </div>
        </div>

        {/* PHOTOSHOOT CREDIT PACKS */}
        <h3 className="pricing-category-title">Extra Photoshoot Credits</h3>
        <div className="pricing-grid credits-grid">
          {/* 1) 1 Photoshoot Credit */}
          <div className="price-card credit-pack-card">
            <h4 className="plan-title">1 Photoshoot Credit</h4>
            <p className="plan-price">$2.49</p>
            <ul className="plan-features">
              <li>Perfect add-on</li>
              <li>Generate a single new photoshoot</li>
              <li>Use anytime once purchased</li>
            </ul>
            {/* <button className="cta-button">Buy Now</button> */}
          </div>

          {/* 2) 3 Photoshoot Credits */}
          <div className="price-card credit-pack-card">
            <h4 className="plan-title">3 Photoshoot Credits</h4>
            <p className="plan-price">$4.99</p>
            <ul className="plan-features">
            <li>Ideal for mini updates</li>
              <li>Use credits flexibly for any model</li>
              <li>Cost-effective bundle</li>
            </ul>
            {/* <button className="cta-button">Buy Now</button> */}
          </div>

          {/* 3) 7 Photoshoot Credits */}
          <div className="price-card credit-pack-card">
            <h4 className="plan-title">7 Photoshoot Credits</h4>
            <p className="plan-price">$9.99</p>
            <ul className="plan-features">
              <li>Best value for frequent updates</li>
              <li>Perfect for frequent updates</li>
              <li>Plan multiple themed shoots</li>
            </ul>
            {/* <button className="cta-button">Buy Now</button> */}
          </div>
        </div>

      </div>
    </section>
  );
}

export default PricingSection;