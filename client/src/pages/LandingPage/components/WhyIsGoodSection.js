// client/src/pages/LandingPage/components/WhyIsGoodSection.js
import React from "react";
import "./WhyIsGoodSection.css";

function WhyIsGoodSection() {
  return (
    <section className="why-good-section">
      <div className="why-good-inner">
        <h2 className="section-title">
          Why TinyMemories Is the Perfect Choice
        </h2>
        <p className="section-subtitle">
          Traditional photo sessions can be stressful and pricey. Our AI
          technology transforms everyday pictures into cherished
          keepsakes—quickly, easily, and affordably.
        </p>

        <div className="benefits-grid">
          <div className="benefit-card">
            <div className="icon-wrapper">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                height="48px"
                viewBox="0 -960 960 960"
                width="48px"
                fill="#555"
              >
                <path d="m436-347 228-228-42-41-183 183-101-101-44 44 142 143Zm44 266q-140-35-230-162.5T160-523v-238l320-120 320 120v238q0 152-90 279.5T480-81Zm0-62q115-38 187.5-143.5T740-523v-196l-260-98-260 98v196q0 131 72.5 236.5T480-143Zm0-337Z" />
              </svg>
            </div>
            <div className="benefit-text">
              <h3>Kid-Friendly &amp; Safe</h3>
              <p>
                Upload photos with peace of mind: our secure AI model is
                designed specifically for children’s images, ensuring top-level
                privacy and safety standards.
              </p>
            </div>
          </div>

          <div className="benefit-card">
            <div className="icon-wrapper">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                height="48px"
                viewBox="0 -960 960 960"
                width="48px"
                fill="#555"
              >
                <path d="M360-860v-60h240v60H360Zm90 447h60v-230h-60v230Zm30 332q-74 0-139.5-28.5T226-187q-49-49-77.5-114.5T120-441q0-74 28.5-139.5T226-695q49-49 114.5-77.5T480-801q67 0 126 22.5T711-716l51-51 42 42-51 51q36 40 61.5 97T840-441q0 74-28.5 139.5T734-187q-49 49-114.5 77.5T480-81Zm0-60q125 0 212.5-87.5T780-441q0-125-87.5-212.5T480-741q-125 0-212.5 87.5T180-441q0 125 87.5 212.5T480-141Zm0-299Z" />
              </svg>
            </div>
            <div className="benefit-text">
              <h3>Lightning-Fast Results</h3>
              <p>
                No more waiting weeks for edits. Our AI engine delivers
                polished, share-ready portraits in just a few hours.
              </p>
            </div>
          </div>

          <div className="benefit-card">
            <div className="icon-wrapper">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                height="48px"
                viewBox="0 -960 960 960"
                width="48px"
                fill="#555"
              >
                <path d="M640-520q17 0 28.5-11.5T680-560q0-17-11.5-28.5T640-600q-17 0-28.5 11.5T600-560q0 17 11.5 28.5T640-520ZM320-620h200v-60H320v60ZM180-120q-34-114-67-227.5T80-580q0-92 64-156t156-64h200q29-38 70.5-59t89.5-21q25 0 42.5 17.5T720-820q0 6-1.5 12t-3.5 11q-4 11-7.5 22.5T702-751l91 91h87v279l-113 37-67 224H480v-80h-80v80H180Zm45-60h115v-80h200v80h115l63-210 102-35v-175h-52L640-728q1-25 6.5-48.5T658-824q-38 10-72 29.5T534-740H300q-66.29 0-113.14 46.86Q140-646.29 140-580q0 103.16 29 201.58Q198-280 225-180Zm255-322Z" />
              </svg>
            </div>
            <div className="benefit-text">
              <h3>Easy on Your Wallet</h3>
              <p>
                Get premium, studio-like images without breaking the bank. Our
                flexible plans offer top-tier results for every budget.
              </p>
            </div>
          </div>

          <div className="benefit-card">
            <div className="icon-wrapper">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                height="48px"
                viewBox="0 -960 960 960"
                width="48px"
                fill="#555"
              >
                <path d="M539.88-480q49.12 0 83.62-34.38 34.5-34.38 34.5-83.5t-34.38-83.62q-34.38-34.5-83.5-34.5t-83.62 34.38q-34.5 34.38-34.5 83.5t34.38 83.62q34.38 34.5 83.5 34.5ZM260-259q51-65 124-103t156-38q83 0 156 38t124 103v-561H260v561Zm0 59q-24.75 0-42.37-17.63Q200-235.25 200-260v-560q0-24.75 17.63-42.38Q235.25-880 260-880h560q24.75 0 42.38 17.62Q880-844.75 880-820v560q0 24.75-17.62 42.37Q844.75-200 820-200H260ZM140-80q-24.75 0-42.37-17.63Q80-115.25 80-140v-570h60v570h570v60H140Zm400-460q-24 0-41-17t-17-41q0-24 17-41t41-17q24 0 41 17t17 41q0 24-17 41t-41 17ZM353-260h374q-36-39-84.5-59.5T540-340q-54 0-102.5 20.5T353-260Zm187-280Z" />
              </svg>
            </div>
            <div className="benefit-text">
              <h3>Infinite Themes &amp; Styles</h3>
              <p>
                From fairytale backdrops to sporty scenes, choose from a vast
                range of scenarios that capture your child’s unique personality.
                Update anytime to keep the memories growing.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default WhyIsGoodSection;
