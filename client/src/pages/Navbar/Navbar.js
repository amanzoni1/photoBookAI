// client/src/pages/Navbar/Navbar.js

import React, { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useCredits } from "../../contexts/CreditsContext";
import BuyCreditsModal from "../BuyCreditsModal/BuyCreditsModal";
import "./Navbar.css";
import logo from "./logo.png";

function Navbar({ isAuthenticated, onLogout }) {
  const [showDropdown, setShowDropdown] = useState(false);
  const [showBuyCreditsModal, setShowBuyCreditsModal] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { credits, loading } = useCredits();

  useEffect(() => {
    if (!isAuthenticated) {
      setShowDropdown(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showDropdown && !event.target.closest(".user-menu")) {
        setShowDropdown(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showDropdown]);

  // Smooth scrolling function
  const handleSmoothScroll = (sectionId) => {
    const section = document.getElementById(sectionId);
    if (section) {
      section.scrollIntoView({ behavior: "smooth" });
    }
  };

  // Hide all links/buttons when not LandingPage
  const isAuthPage =
    location.pathname === "/login" ||
    location.pathname === "/signup" ||
    location.pathname === "/forgot-password";

  return (
    <nav className="navbar">
      <div className="navbar-logo">
        <Link to={isAuthenticated ? "/dashboard" : "/"} className="logo-text">
          <img src={logo} alt="tinyMemories Logo" className="logo-img" />
          tinyMemories
        </Link>
      </div>

      {/* If on login or signup page, show only the logo */}
      {!isAuthPage && (
        <>
          {/* If not authenticated, show public links */}
          {!isAuthenticated && (
            <ul className="navbar-links">
              <li>
                <Link
                  to="/"
                  onClick={() => handleSmoothScroll("pricing-section")}
                >
                  Pricing
                </Link>
              </li>
              <li>
                <Link to="/" onClick={() => handleSmoothScroll("faq-section")}>
                  FAQ
                </Link>
              </li>
              <li>
                <Link to="/contact-us">Contact</Link>
              </li>
            </ul>
          )}

          <div className="navbar-auth">
            {!isAuthenticated && (
              <>
                <Link to="/signup" className="auth-button signup-btn">
                  Sign Up
                </Link>
                <Link to="/login" className="auth-button login">
                  Login
                </Link>
              </>
            )}

            {isAuthenticated && (
              <div className="user-section">
                <button
                  className="buy-credits-btn"
                  onClick={() => setShowBuyCreditsModal(true)}
                >
                  Buy Credits
                </button>

                {!loading && credits && (
                  <div className="credits-display">
                    <div className="credit-item">
                      <span className="credit-label">Model</span>
                      <span className="credit-value">
                        {credits.model_credits}
                      </span>
                    </div>
                    <div className="credit-item">
                      <span className="credit-label">Photoshoot</span>
                      <span className="credit-value">
                        {credits.photoshoot_credits}
                      </span>
                    </div>
                  </div>
                )}

                <div className="user-menu">
                  <button
                    className="user-button"
                    onClick={() => setShowDropdown(!showDropdown)}
                  >
                    <span className="user-icon">👤</span>
                  </button>
                  {showDropdown && (
                    <div className="dropdown-menu">
                      <button
                        onClick={() => {
                          onLogout();
                          setShowDropdown(false);
                          navigate("/");
                        }}
                        className="dropdown-item"
                      >
                        Logout
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </>
      )}

      <BuyCreditsModal
        isOpen={showBuyCreditsModal}
        onClose={() => setShowBuyCreditsModal(false)}
      />
    </nav>
  );
}

export default Navbar;
