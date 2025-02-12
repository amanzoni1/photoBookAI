// Dashboard.js

import React, { useState, useEffect, useCallback } from "react";
import axios from "../../utils/axiosConfig";
import LeftMenu from "./components/LeftMenu";
import RightContent from "./components/RightContent";
import { usePhotoshoot } from "../../hooks/usePhotoshoot";
import "./Dashboard.css";

function Dashboard() {
  const { fetchAllPhotobooks } = usePhotoshoot();
  const [user, setUser] = useState(null);
  const [photobooks, setPhotobooks] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const res = await axios.get("/api/user/profile");
        setUser(res.data.user);
      } catch (err) {
        console.error(err.response?.data);
        setErrorMessage(err.response?.data?.message || "An error occurred");
      }
    };

    fetchUser();
  }, []);

  useEffect(() => {
    document.body.classList.add("logged-in");
    return () => {
      document.body.classList.remove("logged-in");
    };
  }, []);

  const loadPhotobooks = useCallback(async () => {
    try {
      const books = await fetchAllPhotobooks();
      setPhotobooks(books);
    } catch (err) {
      console.error("Error loading photobooks:", err);
    }
  }, [fetchAllPhotobooks]);

  useEffect(() => {
    loadPhotobooks();
  }, [loadPhotobooks]);

  if (errorMessage) {
    return <p className="error-message">{errorMessage}</p>;
  }

  if (!user) {
    return <p>Loading...</p>;
  }

  return (
    <div className="dashboard">
      <LeftMenu onPhotobooksUpdate={loadPhotobooks} photobooks={photobooks} />
      <RightContent
        photobooks={photobooks}
        onPhotobooksUpdate={loadPhotobooks}
      />
    </div>
  );
}

export default Dashboard;
