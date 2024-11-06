// client/src/hooks/useCredits.js

import { useState, useEffect } from 'react';
import axios from '../utils/axiosConfig';
import { useAuth } from './useAuth';

export const useCredits = () => {
  const { isAuthenticated } = useAuth();
  const [credits, setCredits] = useState({
    model_credits: 0,
    image_credits: 0,
    available_photobooks: 0
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

  const purchaseCredits = async (type, quantity = 1) => {
    try {
      // Simulate payment ID for now
      const payment_id = `sim_${Date.now()}`;
      
      const response = await axios.post('/api/credits/purchase', {
        type,
        quantity,
        payment_id
      });

      // Update credits after purchase
      setCredits(response.data.new_balance);
      
      return response.data;
    } catch (error) {
      throw error?.response?.data || error;
    }
  };

  useEffect(() => {
    fetchCredits();
  }, [isAuthenticated]);

  return { 
    credits, 
    loading, 
    refreshCredits: fetchCredits,
    purchaseCredits
  };
};