// client/src/pages/Login/Login.js

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { FcGoogle } from 'react-icons/fc';
import { AiFillApple } from 'react-icons/ai';
import { BsFacebook } from 'react-icons/bs';
import './Login.css';

function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [errorMessage, setErrorMessage] = useState('');

  const onChange = e => setFormData({ ...formData, [e.target.name]: e.target.value });

  const onSubmit = async e => {
    e.preventDefault();
    setErrorMessage('');
    try {
      await login(formData);
      navigate('/dashboard');
    } catch (err) {
      setErrorMessage(err.message || 'Login failed');
    }
  };

  const handleGoogleLogin = () => {
    window.location.href = '/api/auth/google';
  };

  const handleAppleLogin = () => {
    window.location.href = '/api/auth/apple';
  };

  const handleFacebookLogin = () => {
    window.location.href = '/api/auth/facebook';
  };

  return (
    <div className="login-container">
      <h1>Login</h1>
      {errorMessage && <p className="error-message">{errorMessage}</p>}
      <form onSubmit={onSubmit} className="login-form">
        <label>Email address</label>
        <input
          type="email"
          name="email"
          value={formData.email}
          onChange={onChange}
          required
        />
        <label>Password</label>
        <input
          type="password"
          name="password"
          value={formData.password}
          onChange={onChange}
          required
        />
        <button type="submit">Login</button>
      </form>

      <div className="divider">
        <span>or continue with</span>
      </div>

      <div className="social-login">
        <button onClick={handleGoogleLogin} className="social-btn google">
          <FcGoogle /> Google
        </button>
        <button onClick={handleAppleLogin} className="social-btn apple">
          <AiFillApple /> Apple
        </button>
        <button onClick={handleFacebookLogin} className="social-btn facebook">
          <BsFacebook /> Facebook
        </button>
      </div>
    </div>
  );
}

export default Login;