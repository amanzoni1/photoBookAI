// client/src/components/Navbar/Navbar.js

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCredits } from '../../contexts/CreditsContext';
import BuyCreditsModal from '../BuyCreditsModal/BuyCreditsModal';
import './Navbar.css';

function Navbar({ isAuthenticated, onLogout }) {
  const [showDropdown, setShowDropdown] = useState(false);
  const [showBuyCreditsModal, setShowBuyCreditsModal] = useState(false);
  const navigate = useNavigate();
  const { credits, loading } = useCredits();

  useEffect(() => {
    if (!isAuthenticated) {
      setShowDropdown(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showDropdown && !event.target.closest('.user-menu')) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showDropdown]);

  return (
    <nav className="navbar">
      <div className="navbar-logo">
        {isAuthenticated ? (
          <Link to="/dashboard">YourLogo</Link>
        ) : (
          <Link to="/">YourLogo</Link>
        )}
      </div>

      {/* If not authenticated, show public links */}
      {!isAuthenticated && (
        <ul className="navbar-links">
          <li><Link to="/description">Description</Link></li>
          <li><Link to="/faq">FAQ</Link></li>
          <li><Link to="/pricing">Pricing</Link></li>
        </ul>
      )}

      <div className="navbar-auth">
        {/* If not logged in, show login/signup */}
        {!isAuthenticated && (
          <>
            <Link to="/login" className="auth-button">
              Login
            </Link>
            <Link to="/signup" className="auth-button signup-btn">
              Sign Up
            </Link>
          </>
        )}

        {/* If logged in */}
        {isAuthenticated && (
          <div className="user-section">
            {/* BUY CREDITS Button => opens modal */}
            <button
              className="buy-credits-btn"
              onClick={() => setShowBuyCreditsModal(true)}
            >
              Buy Credits
            </button>

            {/* Credits display */}
            {!loading && credits && (
              <div className="credits-display">
                <div className="credit-item">
                  <span className="credit-icon">🎨</span>
                  <span className="credit-value">{credits.model_credits}</span>
                </div>
                <div className="credit-item">
                  <span className="credit-icon">📚</span>
                  <span className="credit-value">{credits.photoshoot_credits}</span>
                </div>
              </div>
            )}

            {/* User dropdown */}
            <div className="user-menu">
              <button
                className="user-button"
                onClick={() => setShowDropdown(!showDropdown)}
              >
                <span className="user-icon">👤</span>
              </button>
              {showDropdown && (
                <div className="dropdown-menu">
                  <Link to="/dashboard" className="dropdown-item">Dashboard</Link>
                  <Link to="/profile" className="dropdown-item">Profile</Link>
                  <button
                    onClick={() => {
                      onLogout();
                      setShowDropdown(false);
                      navigate('/');
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

      {/* The big BuyCreditsModal (popup) */}
      <BuyCreditsModal
        isOpen={showBuyCreditsModal}
        onClose={() => setShowBuyCreditsModal(false)}
      />
    </nav>
  );
}

export default Navbar;