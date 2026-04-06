import React from "react";
import { Link } from "react-router-dom";

const Navbar = ({ currentUser, onLogout }) => {
  const providerLabel =
    currentUser?.role === "professional" ? "Manage Services" : "Become a Provider";

  return (
    <nav className="market-nav">
      <div className="nav-brand">
        <Link className="navbar-brand" to="/">
          ServiceApp
        </Link>
        <span className="nav-caption">Demo customer and provider marketplace</span>
      </div>

      <div className="nav-links">
        <Link className="nav-link" to="/">
          Services
        </Link>
        <Link className="nav-link" to="/bookings">
          My Bookings
        </Link>
        <Link className="nav-link" to="/register-provider">
          {providerLabel}
        </Link>
      </div>

      <div className="nav-user">
        {currentUser ? (
          <>
            <span className="user-pill">
              {currentUser.username} ({currentUser.role})
            </span>
            <button className="btn btn-outline-secondary" onClick={onLogout} type="button">
              Logout
            </button>
          </>
        ) : (
          <>
            <Link className="btn btn-outline-secondary" to="/login">
              Login
            </Link>
            <Link className="btn btn-primary" to="/register">
              Register
            </Link>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
