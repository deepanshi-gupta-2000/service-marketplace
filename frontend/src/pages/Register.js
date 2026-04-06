import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import { API_BASE_URL } from "../auth";

const Register = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");

    try {
      const response = await fetch(`${API_BASE_URL}/auth/register/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username,
          email,
          password,
          role: "customer",
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        const firstError = Object.values(data)[0];
        setError(Array.isArray(firstError) ? firstError[0] : "Registration failed.");
        return;
      }

      setMessage("Registration successful. Please log in.");
      setUsername("");
      setEmail("");
      setPassword("");
      setTimeout(() => navigate("/login"), 800);
    } catch (requestError) {
      setError("Could not reach the server. Please make sure the backend is running.");
    }
  };

  return (
    <div className="container mt-4">
      <h2>Create Account</h2>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Username"
          className="form-control mb-2"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />

        <input
          type="email"
          placeholder="Email"
          className="form-control mb-2"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <input
          type="password"
          placeholder="Password"
          className="form-control mb-2"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <button className="btn btn-warning" type="submit">
          Register
        </button>
      </form>

      {message ? <div className="alert alert-success mt-3">{message}</div> : null}
      {error ? <div className="alert alert-danger mt-3">{error}</div> : null}
    </div>
  );
};

export default Register;
