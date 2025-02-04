// client/src/hooks/usePhotoshoot.js

import { useState, useCallback } from "react";
import axios from "../utils/axiosConfig";

export const usePhotoshoot = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchAllPhotobooks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get("/api/photoshoot/photobooks");
      return res.data.photobooks || [];
    } catch (err) {
      const errorMessage =
        err.response?.data?.message || "Error fetching photobooks";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchPhotobooksByModel = useCallback(async (modelId) => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(
        `/api/photoshoot/model/${modelId}/photobooks`
      );
      return res.data.photobooks || [];
    } catch (err) {
      const errorMessage =
        err.response?.data?.message || "Error fetching model photobooks";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchPhotobookImages = useCallback(async (photobookId) => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(
        `/api/photoshoot/photobooks/${photobookId}/images`
      );
      return res.data;
    } catch (err) {
      const errorMessage =
        err.response?.data?.message || "Error fetching photobook images";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const createPhotobook = useCallback(async (modelId, themeName) => {
    setLoading(true);
    setError(null);
    try {
      const payload = { theme_name: themeName };
      const res = await axios.post(
        `/api/photoshoot/model/${modelId}/photobooks`,
        payload
      );
      return res.data;
    } catch (err) {
      const errorMessage =
        err.response?.data?.message || "Error creating photobook";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const unlockPhotobook = useCallback(async (photobookId) => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.post(
        `/api/photoshoot/photobooks/${photobookId}/unlock`
      );
      return res.data; // e.g. { message: 'Photobook unlocked successfully' }
    } catch (err) {
      const errorMessage =
        err.response?.data?.message || "Error unlocking photobook";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    fetchAllPhotobooks,
    fetchPhotobooksByModel,
    fetchPhotobookImages,
    createPhotobook,
    unlockPhotobook,
    loading,
    error,
  };
};
