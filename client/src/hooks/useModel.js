// client/src/hooks/useModel.js

import { useState, useCallback } from 'react';
import axios from '../utils/axiosConfig';

export const useModel = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Create a new model (training)
   * POST /api/model/training
   */
  const createModel = async (formData, onProgress) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post('/api/model/training', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: progressEvent => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress?.(percentCompleted);
        }
      });
      // Response typically: { message, model_id, job_id, training_images }
      return response.data;
    } catch (err) {
      const errorMessage = err.response?.data?.message || 'An error occurred';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Fetch a single model's details by ID
   * GET /api/model/:model_id
   */
  const checkModelStatus = async (modelId) => {
    try {
      const response = await axios.get(`/api/model/${modelId}`);
      // Response: the model’s details from .to_dict()
      return response.data;
    } catch (err) {
      const errorMessage = err.response?.data?.message || 'Error checking model status';
      setError(errorMessage);
      throw err;
    }
  };

  /**
   * Fetch all models belonging to the current user
   * GET /api/model/models
   */
  const fetchModels = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/model/models');
      return response.data.models || [];
    } catch (err) {
      const errorMessage = err.response?.data?.message || 'Error fetching models';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [setLoading, setError]);

  return {
    createModel,
    checkModelStatus,
    fetchModels,
    loading,
    error
  };
};