// client/src/pages/Signup/Signup.js

import React, { useState } from 'react';
import axios from '../../utils/axiosConfig';
import { useNavigate } from 'react-router-dom';
import './Signup.css';

function Signup() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
  });

  const [errorMessage, setErrorMessage] = useState('');

  const { email, username, password } = formData;

  const onChange = e => setFormData({ ...formData, [e.target.name]: e.target.value });

  const onSubmit = async e => {
    e.preventDefault();
    setErrorMessage('');
    try {
      const res = await axios.post('/api/register', formData);
      console.log(res.data);
      // Redirect to login page or dashboard after successful signup
      navigate('/login');
    } catch (err) {
      if (err.response && err.response.data) {
        console.error(err.response.data);
        setErrorMessage(err.response.data.message || 'An error occurred');
      } else {
        console.error(err);
        setErrorMessage('An error occurred. Please try again later.');
      }
    }
  };

  return (
    <div className="signup-container">
      <h1>Sign Up</h1>
      {errorMessage && <p className="error-message">{errorMessage}</p>}
      <form onSubmit={onSubmit} className="signup-form">
        <label>Email:</label>
        <input type="email" name="email" value={email} onChange={onChange} required />

        <label>Username:</label>
        <input type="text" name="username" value={username} onChange={onChange} required />

        <label>Password:</label>
        <input type="password" name="password" value={password} onChange={onChange} required />

        <button type="submit">Register</button>
      </form>
    </div>
  );
}

export default Signup;