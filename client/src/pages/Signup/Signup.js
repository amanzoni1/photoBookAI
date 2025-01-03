// client/src/pages/Signup/Signup.js

import React, { useState } from 'react';
import axios from '../../utils/axiosConfig';
import { useNavigate, Link } from 'react-router-dom';
import { FcGoogle } from 'react-icons/fc';
import { AiFillApple } from 'react-icons/ai';
import { BsFacebook } from 'react-icons/bs';
import { FiEye, FiEyeOff } from 'react-icons/fi';
import './Signup.css';

function Signup() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [errorMessage, setErrorMessage] = useState('');
  const [validations, setValidations] = useState({
    length: false,
    combination: false,
    special: false
  });
  const [showPassword, setShowPassword] = useState(false);

  const validatePassword = (password) => {
    const hasCharacterCombination = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/.test(password);

    setValidations({
      length: password.length >= 8,
      combination: hasCharacterCombination,
      special: /[\W_]/.test(password)
    });
  };

  const onChange = e => {
    const { name, value } = e.target;
    setFormData(prev => {
      const newData = { ...prev, [name]: value };
      if (name === 'password' || name === 'confirmPassword') {
        validatePassword(
          name === 'password' ? value : newData.password,
          name === 'confirmPassword' ? value : newData.confirmPassword
        );
      }
      return newData;
    });
  };

  const isFormValid = () => {
    return Object.values(validations).every(v => v) &&
      formData.email &&
      formData.password === formData.confirmPassword;
  };

  const onSubmit = async e => {
    e.preventDefault();
    if (!isFormValid()) return;

    try {
      const response = await axios.post('/api/auth/register', {
        email: formData.email,
        password: formData.password
      });
      navigate('/login');
    } catch (err) {
      setErrorMessage(err?.response?.data?.message || 'Registration failed');
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
    <div className="signup-container">
      <h1>Sign Up</h1>
      {errorMessage && <p className="error-message">{errorMessage}</p>}

      <form onSubmit={onSubmit} className="signup-form">
        <div className="form-group">
          <label>Email address</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={onChange}
            required
          />
        </div>

        <div className="form-group">
          <label>Password</label>
          <div className="password-field">
            <input
              type={showPassword ? "text" : "password"}
              name="password"
              value={formData.password}
              onChange={onChange}
              required
            />
            <button
              type="button"
              className="show-password-btn"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? <FiEyeOff /> : <FiEye />}
            </button>
          </div>
          <ul className={`password-requirements ${formData.password ? 'show' : ''}`}>
            <li>
              <span className={validations.length ? 'valid' : 'invalid'}>
                {validations.length ? '✓' : '✘'}
              </span>
              <span className="requirement-text">Must be at least 8 characters</span>
            </li>
            <li>
              <span className={validations.combination ? 'valid' : 'invalid'}>
                {validations.combination ? '✓' : '✘'}
              </span>
              <span className="requirement-text">Must contain uppercase, lowercase letters, and numbers</span>
            </li>
            <li>
              <span className={validations.special ? 'valid' : 'invalid'}>
                {validations.special ? '✓' : '✘'}
              </span>
              <span className="requirement-text">Must contain special character</span>
            </li>
          </ul>

        </div>

        <div className="form-group">
          <label>Confirm Password</label>
          <div className="password-field">
            <input
              type={showPassword ? "text" : "password"}
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={onChange}
              required
            />
            <button
              type="button"
              className="show-password-btn"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? <FiEyeOff /> : <FiEye />}
            </button>
          </div>
        </div>

        <button type="submit" disabled={!isFormValid()}>Register</button>

        <div className="signup-link">
          Already have an account? <Link to="/login">Log In</Link>
        </div>
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

export default Signup;