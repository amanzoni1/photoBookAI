// client/src/pages/LandingPage/components/HowItWorksSection.js

import React from "react";
import { Link } from "react-router-dom";
import "./HowItWorksSection.css";

function HowItWorksSection() {
  return (
    <section className="how-it-works-section">
      <div className="how-it-works-inner">
        <h2 className="section-title">How It Works</h2>
        <p className="section-subtitle">
          In just four simple steps, transform everyday photos of your kids into
          gorgeous, keepsake-worthy portraits—no photography skills required.
        </p>

        <div className="how-steps">
          {/* Step 1 */}
          <div className="how-step">
            <div className="step-content left">
              <svg
                className="step-icon"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
              >
                <path
                  fill="currentColor"
                  d="M3 4V1h2v3h3v2H5v3H3V6H0V4h3zm3 6V7h3V4h7l1.83 2H21c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H5c-1.1 0-2-.9-2-2V10h3zm7 9c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5z"
                />
              </svg>
              <div className="step-text">
                <h3>1. Upload Your Child's Photos</h3>
                <p>
                  Select a few clear snapshots and let our AI learn the
                  distinctive features of your child to produce a custom model.
                  No special equipment or angles needed.
                </p>
              </div>
            </div>
          </div>

          {/* Step 2 */}
          <div className="how-step">
            <div className="step-content">
              <div className="step-text">
                <h3>2. Let Our AI Train Your Model</h3>
                <p>
                  Our system works its magic behind the scenes, preparing a
                  custom model unique to your child. It only takes a few
                  hours—feel free to relax while we do the heavy lifting.
                </p>
              </div>
              <svg
                className="step-icon"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
              >
                <path
                  d="M13.2632 15.934C12.9123 15.8729 12.9123 15.3691 13.2632 15.3081C14.5346 15.0869 15.5457 14.1185 15.8217 12.8579L15.8428 12.7613C15.9188 12.4145 16.4126 12.4123 16.4915 12.7585L16.5172 12.8711C16.8034 14.1257 17.8148 15.0859 19.0827 15.3065C19.4354 15.3678 19.4354 15.8742 19.0827 15.9356C17.8148 16.1561 16.8034 17.1163 16.5172 18.371L16.4915 18.4836C16.4126 18.8297 15.9188 18.8276 15.8428 18.4807L15.8217 18.3841C15.5457 17.1235 14.5346 16.1551 13.2632 15.934Z"
                  fill="currentColor"
                  strokeWidth="1.3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  d="M1.99989 9.46036C1.21618 9.32161 1.21618 8.1776 1.99989 8.03896C4.83915 7.53668 7.09738 5.33761 7.71365 2.47491L7.76088 2.25547C7.93045 1.46786 9.03338 1.46295 9.20958 2.24903L9.26698 2.50475C9.90613 5.35396 12.1648 7.53443 14.9964 8.03532C15.784 8.17467 15.784 9.32456 14.9964 9.46399C12.1648 9.96473 9.90613 12.1452 9.26698 14.9945L9.20958 15.2502C9.03338 16.0362 7.93045 16.0314 7.76088 15.2437L7.71365 15.0243C7.09738 12.1616 4.83915 9.96245 1.99989 9.46036Z"
                  fill="currentColor"
                  strokeWidth="1.68"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          </div>

          {/* Step 3 */}
          <div className="how-step">
            <div className="step-content left">
              <svg
                className="step-icon"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 -960 960 960"
              >
                <path
                  fill="currentColor"
                  d="M546.59-493.33q49.41 0 84.08-34.59 34.66-34.59 34.66-84T630.74-696q-34.58-34.67-84-34.67-49.41 0-84.07 34.59-34.67 34.59-34.67 84T462.59-528q34.59 34.67 84 34.67ZM280-282.67q49-61 118.67-95.83 69.66-34.83 148-34.83 78.33 0 148 34.83 69.66 34.83 118.66 95.83v-530.66H280v530.66Zm0 69.34q-27.5 0-47.08-19.59-19.59-19.58-19.59-47.08v-533.33q0-27.5 19.59-47.09Q252.5-880 280-880h533.33q27.5 0 47.09 19.58Q880-840.83 880-813.33V-280q0 27.5-19.58 47.08-19.59 19.59-47.09 19.59H280ZM146.67-80q-27.5 0-47.09-19.58Q80-119.17 80-146.67v-566.66h66.67v566.66h566.66V-80H146.67Zm400-480q-21.67 0-36.84-15.17-15.16-15.16-15.16-36.83 0-21.67 15.16-36.83Q525-664 546.67-664q21.66 0 36.83 15.17 15.17 15.16 15.17 36.83 0 21.67-15.17 36.83Q568.33-560 546.67-560ZM378-280h337.33q-33.66-32.67-77.33-49.67t-91.33-17q-47.67 0-91.34 17-43.66 17-77.33 49.67Zm168.67-268.33Z"
                />
              </svg>
              <div className="step-text">
                <h3>3. Choose Your Photoshoot</h3>
                <p>
                  Browse a variety of imaginative scenes, outfits, and lighting
                  options. Pick favorites or try them all—each scenario is
                  crafted to look hyper-realistic.
                </p>
              </div>
            </div>
          </div>

          {/* Step 4 */}
          <div className="how-step">
            <div className="step-content">
              <div className="step-text">
                <h3>4. Download &amp; Create</h3>
                <p>
                  Once your photoshoots are ready, preview and download the ones
                  you love. Print them, share them, or use them to design
                  calendars, photo books, and more.
                </p>
              </div>
              <svg
                className="step-icon"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
              >
                <path
                  fill="currentColor"
                  d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm3.5-9c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5zm-7 0c.83 0 1.5-.67 1.5-1.5S9.33 8 8.5 8 7 8.67 7 9.5 7.67 11 8.5 11zm3.5 6.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z"
                />
              </svg>
            </div>
          </div>

          {/* Call-to-action */}
          <div className="how-cta">
            <Link to="/login" className="cta-button-hw">
              Start Creating
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

export default HowItWorksSection;
