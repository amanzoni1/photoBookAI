// client/src/pages/Dashboard/Dashboard.js

import React, { useState, useEffect } from 'react';
import axios from '../../utils/axiosConfig';
import './Dashboard.css';
import LeftMenu from './components/LeftMenu';
import RightContent from './components/RightContent';

function Dashboard() {
  const [user, setUser] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const res = await axios.get('/api/user/profile');
        setUser(res.data.user);
      } catch (err) {
        console.error(err.response?.data);
        setErrorMessage(err.response?.data?.message || 'An error occurred');
      }
    };

    fetchUser();
  }, []);

  useEffect(() => {
    document.body.classList.add('logged-in');
    return () => {
      document.body.classList.remove('logged-in');
    };
  }, []);


  if (errorMessage) {
    return <p className="error-message">{errorMessage}</p>;
  }

  if (!user) {
    return <p>Loading...</p>;
  }

  return (
    <div className="dashboard">
      <LeftMenu />
      <RightContent />
    </div>
  );
}

export default Dashboard;