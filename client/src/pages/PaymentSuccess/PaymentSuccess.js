// client/src/pages/PaymentSuccess.js

import React, { useEffect } from "react";
import { useCredits } from "../../contexts/CreditsContext";
import { useNavigate } from "react-router-dom";

const PaymentSuccess = () => {
  const navigate = useNavigate();
  const { refreshCredits } = useCredits();

  useEffect(() => {
    // Refresh the user's credits so that any changes from the webhook are reflected.
    refreshCredits();

    // Auto-redirect to the dashboard after 5 seconds.
    const timer = setTimeout(() => {
      navigate("/dashboard");
    }, 5000);
    return () => clearTimeout(timer);
  }, [refreshCredits, navigate]);

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
