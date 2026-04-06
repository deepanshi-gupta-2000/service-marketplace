import React, { useEffect, useState } from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";

import { clearAccessToken, fetchCurrentUser } from "./auth";
import Navbar from "./components/Navbar";
import Bookings from "./pages/Bookings";
import Login from "./pages/Login";
import Register from "./pages/Register";
import RegisterProvider from "./pages/RegisterProvider";
import Services from "./pages/Services";

const App = () => {
  const [currentUser, setCurrentUser] = useState(null);
  const [authReady, setAuthReady] = useState(false);

  const refreshCurrentUser = async () => {
    try {
      const user = await fetchCurrentUser();
      setCurrentUser(user);
      setAuthReady(true);
      return user;
    } catch (error) {
      setCurrentUser(null);
      setAuthReady(true);
      return null;
    }
  };

  useEffect(() => {
    refreshCurrentUser();
  }, []);

  const handleLogout = () => {
    clearAccessToken();
    setCurrentUser(null);
  };

  return (
    <Router>
      <Navbar currentUser={currentUser} onLogout={handleLogout} />
      <div className="app-shell">
        <h1 className="app-title">Service Marketplace</h1>

        <Routes>
          <Route path="/" element={<Services currentUser={currentUser} />} />
          <Route path="/bookings" element={<Bookings currentUser={currentUser} />} />
          <Route
            path="/register-provider"
            element={
              <RegisterProvider
                authReady={authReady}
                currentUser={currentUser}
                refreshCurrentUser={refreshCurrentUser}
              />
            }
          />
          <Route path="/login" element={<Login onLogin={refreshCurrentUser} />} />
          <Route path="/register" element={<Register />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;
