// client/src/pages/Login/Login.js

import React, { useState } from 'react';
import axios from '../../utils/axiosConfig';
import { useNavigate } from 'react-router-dom';
import './Login.css';

function Login({ setIsAuthenticated }) {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const [errorMessage, setErrorMessage] = useState('');

  const { email, password } = formData;

  const onChange = e => setFormData({ ...formData, [e.target.name]: e.target.value });

  const onSubmit = async e => {
    e.preventDefault();
    setErrorMessage('');
    try {
      const res = await axios.post('/api/auth/login', formData);
      console.log(res.data);
      // Save the token in localStorage
      localStorage.setItem('token', res.data.token);
      // Update authentication state
      setIsAuthenticated(true);
      // Redirect to dashboard
      navigate('/dashboard');
    } catch (err) {
      console.error(err.response.data);
      setErrorMessage(err.response.data.message || 'An error occurred');
    }
  };

  return (
    <div className="login-container">
      <h1>Login</h1>
      {errorMessage && <p className="error-message">{errorMessage}</p>}
      <form onSubmit={onSubmit} className="login-form">
        <label>Email:</label>
        <input type="email" name="email" value={email} onChange={onChange} required />

        <label>Password:</label>
        <input type="password" name="password" value={password} onChange={onChange} required />

        <button type="submit">Login</button>
      </form>
    </div>
  );
}

export default Login;