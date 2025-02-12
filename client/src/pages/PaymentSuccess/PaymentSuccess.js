// client/src/pages/PaymentSuccess.js

import React, { useEffect } from "react";
import { useCredits } from "../../contexts/CreditsContext";
import { useNavigate } from "react-router-dom";
import "./PaymentSuccess.css";

const PaymentSuccess = () => {
  const navigate = useNavigate();
  const { refreshCredits } = useCredits();

  useEffect(() => {
    document.body.classList.add("logged-in");

    // Refresh credits to update any changes from the payment
    refreshCredits();

    // Auto-redirect to the dashboard after 5 seconds.
    const timer = setTimeout(() => {
      navigate("/dashboard");
    }, 3000);

    // Cleanup: remove the class and clear the timer
    return () => {
      document.body.classList.remove("logged-in");
      clearTimeout(timer);
    };
  }, [refreshCredits, navigate]);

  return (
    <div className="payment-page">
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
