// client/src/pages/ResetPassword/ResetPassword.js

import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { FiEye, FiEyeOff } from "react-icons/fi";
import { useAuth } from "../../hooks/useAuth";
import "./ResetPassword.css";

const ResetPassword = () => {
  const { resetPassword } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  // Extract the token from the URL query parameters (e.g. ?token=abcdef)
  const searchParams = new URLSearchParams(location.search);
  const token = searchParams.get("token");

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [validations, setValidations] = useState({
    length: false,
    combination: false,
    special: false,
  });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Validate password similar to your Signup page requirements
  const validatePassword = (pwd) => {
    const hasCharacterCombination = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/.test(
      pwd
    );
    setValidations({
      length: pwd.length >= 8,
      combination: hasCharacterCombination,
      special: /[\W_]/.test(pwd),
    });
  };

  const handlePasswordChange = (e) => {
    const newPassword = e.target.value;
    setPassword(newPassword);
    validatePassword(newPassword);
  };

  const handleConfirmPasswordChange = (e) => {
    setConfirmPassword(e.target.value);
  };

  const isFormValid = () => {
    return (
      Object.values(validations).every((v) => v) &&
      password &&
      password === confirmPassword
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    if (!isFormValid()) {
      setError("Please ensure passwords meet the requirements and match.");
      return;
    }
    setIsSubmitting(true);
    try {
      const data = await resetPassword(token, password);
      setMessage(data.message || "Password reset successfully.");
      // Redirect to login after 5 seconds
      setTimeout(() => {
        navigate("/login");
      }, 5000);
    } catch (err) {
      setError(err.message || "Password reset failed. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-container">
      <h1>Reset Password</h1>
      {message && <p className="success-message">{message}</p>}
      {error && <p className="error-message">{error}</p>}
      <form onSubmit={handleSubmit} className="auth-form">
        <div className="form-group">
          <label>New Password</label>
          <div className="password-field">
            <input
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={handlePasswordChange}
              required
            />
            <button
              type="button"
              className="show-password-btn"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? <FiEyeOff /> : <FiEye />}
            </button>
          </div>
          {/* Password Requirements */}
          <ul className={`password-requirements ${password ? "show" : ""}`}>
            <li>
              <span className={validations.length ? "valid" : "invalid"}>
                {validations.length ? "✓" : "✘"}
              </span>
              <span className="requirement-text">
                Must be at least 8 characters
              </span>
            </li>
            <li>
              <span className={validations.combination ? "valid" : "invalid"}>
                {validations.combination ? "✓" : "✘"}
              </span>
              <span className="requirement-text">
                Must contain uppercase, lowercase letters, and numbers
              </span>
            </li>
            <li>
              <span className={validations.special ? "valid" : "invalid"}>
                {validations.special ? "✓" : "✘"}
              </span>
              <span className="requirement-text">
                Must contain a special character
              </span>
            </li>
          </ul>
        </div>
        <div className="form-group">
          <label>Confirm New Password</label>
          <div className="password-field">
            <input
              type={showPassword ? "text" : "password"}
              value={confirmPassword}
              onChange={handleConfirmPasswordChange}
              required
            />
            <button
              type="button"
              className="show-password-btn"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? <FiEyeOff /> : <FiEye />}
            </button>
          </div>
        </div>
        <button type="submit" disabled={!isFormValid() || isSubmitting}>
          {isSubmitting ? "Resetting..." : "Reset Password"}
        </button>
      </form>
    </div>
  );
};

export default ResetPassword;
