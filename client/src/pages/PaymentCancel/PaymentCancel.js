// client/src/pages/PaymentCancel.js

import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./PaymentCancel.css";

const PaymentCancel = () => {
  const navigate = useNavigate();

  useEffect(() => {
    document.body.classList.add("logged-in");
    return () => {
      document.body.classList.remove("logged-in");
    };
  }, []);

  return (
    <div className="payment-page">
      <h2>Payment Cancelled</h2>
      <p>
        Your payment was cancelled. If you would like to try again, please
        return to your dashboard.
      </p>
      <button onClick={() => navigate("/dashboard")}>
        Return to Dashboard
      </button>
    </div>
  );
};

export default PaymentCancel;
