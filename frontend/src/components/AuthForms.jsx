import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";

export function Login({ onRegisterLink, onSuccess, onForgotPassword }) {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password, rememberMe);
      if (onSuccess) onSuccess();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Invalid email or password. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-card-wrapper">
      <div className="auth-card glass-panel">
        <div className="brand">
          <span className="brand-logo">📊</span>
          <h2 className="auth-title">Welcome to MarketBeacon AI</h2>
        </div>
        <p className="auth-subtitle">Analyze companies, track news and research investments.</p>
        
        {error && <div className="auth-error-banner">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <div className="label-row">
              <label htmlFor="password">Password</label>
              <button
                type="button"
                className="btn-link"
                onClick={onForgotPassword}
              >
                Forgot Password?
              </button>
            </div>
            <input
              type="password"
              id="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <div className="form-checkbox-row">
            <label className="checkbox-container">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
              />
              <span className="checkmark"></span>
              Remember Me
            </label>
          </div>

          <button
            type="submit"
            className="btn-primary btn-full"
            disabled={loading}
          >
            {loading ? "Authenticating..." : "Sign In"}
          </button>
        </form>

        <div className="auth-divider">
          <span>or continue with</span>
        </div>

        <div className="oauth-buttons">
          <button
            className="btn-oauth"
            disabled
            style={{ cursor: "not-allowed", opacity: 0.6 }}
          >
            <span className="oauth-logo">G</span> Google (Coming Soon)
          </button>
        </div>

        <p className="auth-footer-text">
          Don't have an account?{" "}
          <button className="btn-link" onClick={onRegisterLink}>
            Create an Account
          </button>
        </p>
      </div>
    </div>
  );
}

export function Register({ onLoginLink, onSuccess }) {
  const { register } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // Validation
    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (!acceptTerms) {
      setError("You must accept the terms of service and privacy policy.");
      return;
    }

    setLoading(true);
    try {
      await register(fullName, email, password, confirmPassword);
      if (onSuccess) onSuccess();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Registration failed. Email may already be in use."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-card-wrapper">
      <div className="auth-card glass-panel">
        <div className="brand">
          <span className="brand-logo">📊</span>
          <h2 className="auth-title">Create Account</h2>
        </div>
        <p className="auth-subtitle">Get started with MarketBeacon AI financial terminal.</p>
        
        {error && <div className="auth-error-banner">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="fullName">Full Name</label>
            <input
              type="text"
              id="fullName"
              placeholder="Sujan"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password (min. 8 characters)</label>
            <input
              type="password"
              id="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>

          <div className="form-checkbox-row">
            <label className="checkbox-container">
              <input
                type="checkbox"
                checked={acceptTerms}
                onChange={(e) => setAcceptTerms(e.target.checked)}
              />
              <span className="checkmark"></span>
              I agree to the Terms of Service & Privacy Policy
            </label>
          </div>

          <button
            type="submit"
            className="btn-primary btn-full"
            disabled={loading}
          >
            {loading ? "Creating Account..." : "Create Account"}
          </button>
        </form>

        <p className="auth-footer-text">
          Already have an account?{" "}
          <button className="btn-link" onClick={onLoginLink}>
            Sign In Instead
          </button>
        </p>
      </div>
    </div>
  );
}

export function ForgotPassword({ onBackToLogin }) {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    // Sandbox / Mock Forgot Password behaviour (Architecture Ready)
    setSubmitted(true);
  };

  return (
    <div className="auth-card-wrapper">
      <div className="auth-card glass-panel">
        <h2 className="auth-title">Reset Password</h2>
        
        {submitted ? (
          <div className="forgot-success-state">
            <div className="success-icon">✉️</div>
            <p className="success-text">
              If an account matches <strong>{email}</strong>, a password reset link has been dispatched with further instructions.
            </p>
            <button className="btn-primary btn-full" onClick={onBackToLogin}>
              Back to Login
            </button>
          </div>
        ) : (
          <>
            <p className="auth-subtitle">
              Enter your email address and we'll dispatch a link to reset your password.
            </p>
            <form onSubmit={handleSubmit} className="auth-form">
              <div className="form-group">
                <label htmlFor="email">Email Address</label>
                <input
                  type="email"
                  id="email"
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="btn-primary btn-full">
                Send Reset Link
              </button>
              <button
                type="button"
                className="btn-secondary btn-full"
                onClick={onBackToLogin}
                style={{ marginTop: "0.75rem" }}
              >
                Cancel
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
