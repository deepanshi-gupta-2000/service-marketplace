import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { apiFetch } from "../auth";
import Providers from "./Providers";

const initialBookingForm = {
  location: "",
  date: "",
  time: "",
  notes: "",
};

const initialFilters = {
  minPrice: "",
  maxPrice: "",
  minRating: "",
  sortBy: "highest_rated",
};

const Services = ({ currentUser }) => {
  const [services, setServices] = useState([]);
  const [selectedService, setSelectedService] = useState(null);
  const [selectedProviderId, setSelectedProviderId] = useState(null);
  const [bookingForm, setBookingForm] = useState(initialBookingForm);
  const [filters, setFilters] = useState(initialFilters);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const loadServices = async () => {
      const { response, data } = await apiFetch("/services/");
      if (!response.ok) {
        setError("Could not load services.");
        return;
      }

      setServices(data || []);
    };

    loadServices();
  }, []);

  const handleBookService = async (event) => {
    event.preventDefault();
    setMessage("");
    setError("");

    if (!currentUser) {
      setError("Please login as a customer to send a service request.");
      return;
    }

    if (!selectedService) {
      setError("Please choose a service first.");
      return;
    }

    const payload = {
      service: selectedService.id,
      location: bookingForm.location,
      date: bookingForm.date,
      time: bookingForm.time,
      notes: bookingForm.notes,
    };

    if (selectedProviderId) {
      payload.preferred_provider = selectedProviderId;
    }

    const { response, data } = await apiFetch("/bookings/requests/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      setError(data?.error || "Could not send request.");
      return;
    }

    setMessage(
      `Request sent to ${data.preferred_provider?.user?.username || "the matched provider"}. They can now accept, reject, or schedule an inspection based on the service type.`
    );
    setBookingForm(initialBookingForm);
    setFilters(initialFilters);
    setSelectedProviderId(null);
  };

  const updateBookingLocation = (value) => {
    setBookingForm((current) => ({ ...current, location: value }));
  };

  return (
    <div className="page-shell">
      <section className="hero-panel">
        <div>
          <p className="eyebrow">Customer Flow</p>
          <h2>Book a home service in one place</h2>
          <p className="hero-copy">
            Pick a service, choose your service location, filter providers by budget and
            rating, then send a request to the best match for your home.
          </p>
        </div>
        <div className="hero-actions">
          <Link className="btn btn-primary" to="/bookings">
            View My Bookings
          </Link>
          {!currentUser ? (
            <Link className="btn btn-outline-secondary" to="/login">
              Login to Book
            </Link>
          ) : null}
        </div>
      </section>

      {message ? <div className="alert alert-success mt-4">{message}</div> : null}
      {error ? <div className="alert alert-danger mt-4">{error}</div> : null}

      <section className="panel mt-4">
        <div className="section-header">
          <h3>Service Catalog</h3>
          <p>Select the service you want to book. Pricing explains whether it is fixed, a starting rate, or inspection-based.</p>
        </div>
        <div className="card-grid">
          {services.map((service) => {
            const selected = selectedService?.id === service.id;
            return (
              <button
                className={`market-card service-card ${selected ? "selected" : ""}`}
                key={service.id}
                onClick={() => {
                  setSelectedService(service);
                  setSelectedProviderId(null);
                }}
                type="button"
              >
                <div className="card-topline">
                  <span className="tag">{selected ? "Selected" : "Service"}</span>
                  <span className="pricing-chip">{service.pricing_type_label}</span>
                </div>
                <h4>{service.name}</h4>
                <p>{service.description || "Demo category available for booking."}</p>
                <p className="service-pricing">{service.pricing_display}</p>
              </button>
            );
          })}
        </div>
      </section>

      {selectedService ? (
        <>
          <section className="panel mt-4">
            <div className="section-header">
              <h3>Provider Filters</h3>
              <p>Enter the service location once and use the filters to narrow matching providers.</p>
            </div>

            <div className="filter-grid">
              <input
                className="form-control"
                onChange={(event) => updateBookingLocation(event.target.value)}
                placeholder="Service location (example: Agra)"
                type="text"
                value={bookingForm.location}
              />
              <input
                className="form-control"
                onChange={(event) =>
                  setFilters((current) => ({ ...current, minPrice: event.target.value }))
                }
                placeholder="Min price"
                type="number"
                value={filters.minPrice}
              />
              <input
                className="form-control"
                onChange={(event) =>
                  setFilters((current) => ({ ...current, maxPrice: event.target.value }))
                }
                placeholder="Max price"
                type="number"
                value={filters.maxPrice}
              />
              <select
                className="form-control"
                onChange={(event) =>
                  setFilters((current) => ({ ...current, minRating: event.target.value }))
                }
                value={filters.minRating}
              >
                <option value="">Min rating</option>
                <option value="4.5">4.5+</option>
                <option value="4">4+</option>
                <option value="3">3+</option>
              </select>
              <select
                className="form-control"
                onChange={(event) =>
                  setFilters((current) => ({ ...current, sortBy: event.target.value }))
                }
                value={filters.sortBy}
              >
                <option value="highest_rated">Highest rated</option>
                <option value="lowest_price">Lowest price</option>
                <option value="highest_experience">Most experienced</option>
              </select>
            </div>
          </section>

          <Providers
            filters={{
              ...filters,
              location: bookingForm.location,
            }}
            onChooseProvider={setSelectedProviderId}
            selectedProviderId={selectedProviderId}
            serviceId={selectedService.id}
          />

          <section className="panel mt-4">
            <div className="section-header">
              <h3>Send Service Request</h3>
              <p>
                Request <strong>{selectedService.name}</strong>{" "}
                {selectedProviderId ? "from a selected provider." : "with smart provider matching."}
              </p>
            </div>

            {selectedProviderId ? (
              <div className="alert alert-info">
                Provider selected for this request.
                <button
                  className="btn btn-outline-secondary"
                  onClick={() => setSelectedProviderId(null)}
                  type="button"
                >
                  Use Auto-Assign Instead
                </button>
              </div>
            ) : null}

            <form className="booking-form" onSubmit={handleBookService}>
              <input
                className="form-control"
                onChange={(event) =>
                  setBookingForm((current) => ({ ...current, date: event.target.value }))
                }
                required
                type="date"
                value={bookingForm.date}
              />
              <input
                className="form-control"
                onChange={(event) =>
                  setBookingForm((current) => ({ ...current, time: event.target.value }))
                }
                required
                type="time"
                value={bookingForm.time}
              />
              <textarea
                className="form-control"
                onChange={(event) =>
                  setBookingForm((current) => ({ ...current, notes: event.target.value }))
                }
                placeholder="Notes for the provider"
                rows="4"
                value={bookingForm.notes}
              />
              <button className="btn btn-success" type="submit">
                Send Request
              </button>
            </form>
          </section>
        </>
      ) : null}
    </div>
  );
};

export default Services;
