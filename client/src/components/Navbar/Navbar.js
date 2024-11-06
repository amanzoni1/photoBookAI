// client/src/components/Navbar/Navbar.js

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCredits } from '../../hooks/useCredits';
import './Navbar.css';

function Navbar({ isAuthenticated, onLogout }) {
  const [showDropdown, setShowDropdown] = useState(false);
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

      {!isAuthenticated && (
        <ul className="navbar-links">
          <li>
            <Link to="/faq">FAQ</Link>
          </li>
          <li>
            <Link to="/pricing">Pricing</Link>
          </li>
          <li>
            <Link to="/description">Description</Link>
          </li>
        </ul>
      )}

      <div className="navbar-auth">
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

        {isAuthenticated && (
          <div className="user-section">
            {/* Credits Display */}
            {!loading && credits && (
              <div className="credits-display">
                <div className="credit-item">
                  <span className="credit-icon">🎨</span>
                  <span className="credit-value">{credits.model_credits}</span>
                </div>
                <div className="credit-item">
                  <span className="credit-icon">🖼️</span>
                  <span className="credit-value">{credits.image_credits}</span>
                </div>
                <div className="credit-item">
                  <span className="credit-icon">📚</span>
                  <span className="credit-value">{credits.available_photobooks}</span>
                </div>
              </div>
            )}

            {/* User Menu */}
            <div className="user-menu">
              <button
                className="user-button"
                onClick={() => setShowDropdown(!showDropdown)}
              >
                <span className="user-icon">👤</span>
              </button>

              {showDropdown && (
                <div className="dropdown-menu">
                  <Link to="/dashboard" className="dropdown-item">
                    Dashboard
                  </Link>
                  <Link to="/profile" className="dropdown-item">
                    Profile
                  </Link>
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
    </nav>
  );
}

export default Navbar;