// client/src/components/Navbar/Navbar.js

import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './Navbar.css'; // Import styles

function Navbar({ isAuthenticated, setIsAuthenticated }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    // Remove token from localStorage
    localStorage.removeItem('token');
    // Update authentication state
    setIsAuthenticated(false);
    // Redirect to home or login page
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="navbar-logo">
        {/* Logo placeholder */}
        <Link to="/">YourLogo</Link>
      </div>
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
        {isAuthenticated && (
          <li>
            <Link to="/dashboard">Dashboard</Link>
          </li>
        )}
      </ul>
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
          <button onClick={handleLogout} className="auth-button logout-btn">
            Logout
          </button>
        )}
      </div>
    </nav>
  );
}

export default Navbar;