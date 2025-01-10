// client/src/contexts/CreditsContext.js

import React, { createContext, useState, useCallback, useEffect, useContext } from 'react';
import axios from '../utils/axiosConfig';
import { useAuth } from '../hooks/useAuth';

/**
 * 1) Create the context
 */
const CreditsContext = createContext();

/**
 * 2) Provider component
 *
 * This will hold the global "credits" state and methods like fetch/purchase,
 * so all children can read & update them in real-time.
 */
export function CreditsProvider({ children }) {
  const { isAuthenticated } = useAuth(); // to know if user is logged in
  const [credits, setCredits] = useState({ model_credits: 0, photoshoot_credits: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  /**
   * Fetch the user's current credits from the server
   */
  const fetchCredits = useCallback(async () => {
    // If not authenticated, skip
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.get('/api/credits/balance');
      setCredits(response.data); // e.g. { model_credits: 0, photoshoot_credits: 0 }
    } catch (err) {
      console.error('Error fetching credits:', err);
      setError(err.response?.data?.message || 'Error fetching credits');
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  /**
   * Purchase credits of a certain type (MODEL or PHOTOSHOOT).
   */
  const purchaseCredits = useCallback(async (type, quantity = 1) => {
    try {
      // Simulate a payment_id for now
      const payment_id = `sim_${Date.now()}`;
      const response = await axios.post('/api/credits/purchase', {
        type,
        quantity,
        payment_id,
      });
      // The server should return { message, new_balance, ... }
      setCredits(response.data.new_balance); // update local state
      return response.data; // pass data back to caller
    } catch (error) {
      throw error.response?.data || error;
    }
  }, []);

  /**
   * Auto-fetch credits on mount or whenever `isAuthenticated` changes
   */
  useEffect(() => {
    fetchCredits();
  }, [fetchCredits]);

  /**
   * The context "value" that other components will see
   */
  const value = {
    credits,       // e.g. { model_credits, photoshoot_credits }
    loading,       // boolean
    error,         // error message or null
    purchaseCredits,
    refreshCredits: fetchCredits,
  };

  return (
    <CreditsContext.Provider value={value}>
      {children}
    </CreditsContext.Provider>
  );
}

/**
 * 3) Hook to consume the CreditsContext
 */
export function useCredits() {
  return useContext(CreditsContext);
}