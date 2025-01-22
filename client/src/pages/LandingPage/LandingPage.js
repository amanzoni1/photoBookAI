// client/src/pages/LandingPage/LandingPage.js

import React from 'react';
import './LandingPage.css';
import HeroSection from './components/HeroSection';
// import WhyIsGood from './components/WhyIsGood';
// import HowItWorksSection from './components/HowItWorksSection';
// import PricingSection from './components/PricingSection';
// import FAQSection from './components/FAQSection';

function LandingPage() {
  return (
    <div className="landing-container">
      {/* Possibly a background component or gradient */}
      <HeroSection />
      {/* <WhyIsGood />
      <HowItWorksSection />
      <PricingSection />
      <FAQSection />  */}
    </div>
  );
}

export default LandingPage;