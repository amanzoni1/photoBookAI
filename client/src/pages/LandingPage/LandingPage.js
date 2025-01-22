// client/src/pages/LandingPage/LandingPage.js

import React from 'react';
import './LandingPage.css';
import HeroSection from './components/HeroSection';
import WhyIsGoodSection from './components/WhyIsGoodSection';
import HowItWorksSection from './components/HowItWorksSection';
import ComparisonSection from './components/ComparisonSection';
import PricingSection from './components/PricingSection';
import FAQSection from './components/FAQSection';

function LandingPage() {
  return (
    <div className="landing-container">
      <HeroSection />
      <WhyIsGoodSection />
      <ComparisonSection />
      <HowItWorksSection />
      <PricingSection />
      <FAQSection /> 
    </div>
  );
}

export default LandingPage;