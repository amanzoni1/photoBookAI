// client/src/pages/Dashboard/Dashboard.js

import React, { useEffect, useState } from 'react';
import axios from '../../utils/axiosConfig';
import './Dashboard.css';

function Dashboard() {
  const [user, setUser] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const res = await axios.get('/api/user');
        setUser(res.data.user);
      } catch (err) {
        console.error(err.response.data);
        setErrorMessage(err.response.data.message || 'An error occurred');
      }
    };

    fetchUser();
  }, []);

  if (errorMessage) {
    return <p className="error-message">{errorMessage}</p>;
  }

  if (!user) {
    return <p>Loading...</p>;
  }

  return (
    <div className="dashboard-container">
      <h1>Welcome, {user.username}!</h1>
      <p>Email: {user.email}</p>
      {/* Add more personalized content here */}
    </div>
  );
}

export default Dashboard;