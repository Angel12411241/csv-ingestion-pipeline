import { Link, Outlet } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

export default function Layout() {
  const { email, logout } = useAuth();

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar__inner">
          <Link to="/" className="brand">
            <img src="/favicon.svg" alt="" width="24" height="24" />
            Sales Ingest
          </Link>
          <div className="topbar__user">
            <span className="muted">{email}</span>
            <button type="button" className="button button--secondary" onClick={logout}>
              Log out
            </button>
          </div>
        </div>
      </header>
      <main className="container">
        <Outlet />
      </main>
    </div>
  );
}
