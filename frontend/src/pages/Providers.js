import React, { useEffect, useState } from "react";

const Providers = ({ serviceId }) => {
  const [providers, setProviders] = useState([]);

  useEffect(() => {
    fetch(`http://127.0.0.1:8000/api/providers/?service=${serviceId}`)
      .then((res) => res.json())
      .then((data) => setProviders(data));
  }, [serviceId]);

  const handleBooking = (providerId) => {
    const bookingData = {
      user: 1,
      service_provider: providerId,
      service: serviceId,
      date: "2026-04-05",
      time: "10:00:00",
    };

    fetch("http://127.0.0.1:8000/api/bookings/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(bookingData),
    })
      .then((res) => res.json())
      .then((data) => {
        alert("Booking Successful ✅");
      })
      .catch((err) => {
        alert("Booking Failed ❌");
      });
  };

  return (
    <div className="mt-4">
      <h3>Providers</h3>

      <div className="row">
        {providers.map((provider) => (
          <div className="col-md-4" key={provider.id}>
            <div className="card p-3 mb-3 shadow-sm">
              {/* <p>{provider.user}</p> */}
              <p><strong>Name:</strong> {provider.user.username}</p>
<p><strong>Email:</strong> {provider.user.email}</p>
              <button
                className="btn btn-success"
                onClick={() => handleBooking(provider.id)}
              >
                Book Now
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Providers;