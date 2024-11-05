// client/src/hooks/useCredits.js

import { useState, useEffect } from 'react';
import axios from '../utils/axiosConfig';
import { useAuth } from './useAuth';

export const useCredits = () => {
  const { isAuthenticated } = useAuth();
  const [credits, setCredits] = useState({
    model_credits: 0,
    image_credits: 0,
    photobook_credits: 0
  });
  const [loading, setLoading] = useState(true);

  const fetchCredits = async () => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }
    try {
      const response = await axios.get('/api/credits/balance');
      setCredits(response.data);
    } catch (error) {
      console.error('Error fetching credits:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCredits();
  }, [isAuthenticated]);

  return { credits, loading, refreshCredits: fetchCredits };
};