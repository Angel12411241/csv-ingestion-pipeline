import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { getErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";

const COPY = {
  login: {
    title: "Sign in",
    submit: "Sign in",
    switchText: "No account yet?",
    switchLink: "/register",
    switchLabel: "Create one",
  },
  register: {
    title: "Create an account",
    submit: "Create account",
    switchText: "Already registered?",
    switchLink: "/login",
    switchLabel: "Sign in",
  },
};

/** Login and registration share one form; `mode` selects the action and copy. */
export default function AuthPage({ mode }) {
  const copy = COPY[mode];
  const { isAuthenticated, login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  if (isAuthenticated) return <Navigate to="/" replace />;

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await (mode === "login" ? login : register)(email, password);
      navigate(location.state?.from?.pathname ?? "/", { replace: true });
    } catch (err) {
      setError(getErrorMessage(err));
      setSubmitting(false);
    }
  }

  return (
    <div className="auth">
      <form className="card auth__card" onSubmit={handleSubmit}>
        <div className="brand brand--center">
          <img src="/favicon.svg" alt="" width="28" height="28" />
          Sales Ingest
        </div>
        <h1 className="auth__title">{copy.title}</h1>

        <label className="field">
          <span>Email</span>
          <input
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>
        <label className="field">
          <span>Password</span>
          <input
            type="password"
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            required
            minLength={mode === "register" ? 8 : undefined}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          {mode === "register" && <small className="muted">At least 8 characters.</small>}
        </label>

        {error && (
          <p className="alert alert--error" role="alert">
            {error}
          </p>
        )}

        <button type="submit" className="button button--block" disabled={submitting}>
          {submitting ? "Please wait…" : copy.submit}
        </button>
        <p className="muted auth__switch">
          {copy.switchText} <Link to={copy.switchLink}>{copy.switchLabel}</Link>
        </p>
      </form>
    </div>
  );
}
