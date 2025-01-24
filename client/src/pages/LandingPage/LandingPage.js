// client/src/pages/LandingPage/LandingPage.js

import React from 'react';
import './LandingPage.css';
import HeroSection from './components/HeroSection';
import WhyIsGoodSection from './components/WhyIsGoodSection';
import HowItWorksSection from './components/HowItWorksSection';
import ComparisonSection from './components/ComparisonSection';
import PricingSection from './components/PricingSection';
import FAQSection from './components/FAQSection';
import PhotoRow from './components/PhotoRow';

function LandingPage() {
  return (
    <div className="landing-container">
      <HeroSection />
      <WhyIsGoodSection />
      <PhotoRow />
      <HowItWorksSection />
      <ComparisonSection />
      <PhotoRow />
      <PricingSection id="pricing-section" />
      <FAQSection id="faq-section" />
    </div>
  );
}

export default LandingPage;