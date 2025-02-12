// client/src/pages/PaymentCancel.js

import React from "react";
import { useNavigate } from "react-router-dom";

const PaymentCancel = () => {
  const navigate = useNavigate();

  return (
    <div style={{ padding: "2rem", textAlign: "center" }}>
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
