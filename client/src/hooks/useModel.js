// client/src/hooks/useModel.js

import { useState } from 'react';
import axios from '../utils/axiosConfig';

export const useModel = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const createModel = async (formData, onProgress) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/api/model/training', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress?.(percentCompleted);
        }
      });
      
      return response.data;
    } catch (err) {
      const errorMessage = err.response?.data?.message || 'An error occurred';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const checkModelStatus = async (modelId) => {
    try {
      const response = await axios.get(`/api/model/${modelId}`);
      return response.data;
    } catch (err) {
      const errorMessage = err.response?.data?.message || 'Error checking model status';
      setError(errorMessage);
      throw err;
    }
  };

  return {
    createModel,
    checkModelStatus,
    loading,
    error
  };
};