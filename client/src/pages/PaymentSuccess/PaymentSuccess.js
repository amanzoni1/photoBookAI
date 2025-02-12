// client/src/pages/PaymentSuccess.js

import React, { useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";

const PaymentSuccess = () => {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // You can parse the query parameters if you need to verify the session.
    const searchParams = new URLSearchParams(location.search);
    const sessionId = searchParams.get("session_id");
    // Optionally: call your API to verify the session using sessionId

    // Auto-redirect to the dashboard after 5 seconds.
    const timer = setTimeout(() => {
      navigate("/dashboard");
    }, 5000);
    return () => clearTimeout(timer);
  }, [location, navigate]);

  return (
    <div style={{ padding: "2rem", textAlign: "center" }}>
      <h2>Payment Successful!</h2>
      <p>Your payment was processed successfully.</p>
      <p>You will be redirected to your dashboard shortly.</p>
      <p>
        If you are not redirected,{" "}
        <button onClick={() => navigate("/dashboard")}>click here</button>
      </p>
    </div>
  );
};

export default PaymentSuccess;
