import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { apiFetch } from "../auth";

const RequestCard = ({ requestItem, onCancel }) => (
  <div className="market-card booking-card">
    <div className="card-topline">
      <span className="tag">{requestItem.service?.name || "Service"}</span>
      <span className="status-badge">{requestItem.status.replaceAll("_", " ")}</span>
    </div>
    <h4>{requestItem.preferred_provider?.user?.username || "Matched provider"}</h4>
    <p>Location: {requestItem.location}</p>
    <p>
      Preferred slot: {requestItem.date} at {requestItem.time}
    </p>
    {requestItem.provider_response_notes ? (
      <p>Provider note: {requestItem.provider_response_notes}</p>
    ) : null}
    {requestItem.notes ? <p>Your notes: {requestItem.notes}</p> : null}
    {requestItem.created_booking ? (
      <p>Booking created: #{requestItem.created_booking.id}</p>
    ) : null}

    {requestItem.status === "pending_provider_response" ? (
      <div className="action-row">
        <button className="btn btn-outline-secondary" onClick={() => onCancel(requestItem.id)} type="button">
          Cancel Request
        </button>
      </div>
    ) : null}
  </div>
);

const BookingCard = ({ booking, onCompletePayment, onRefresh, onReview }) => {
  const [rating, setRating] = useState("5");
  const [comment, setComment] = useState("");
  const [submittingReview, setSubmittingReview] = useState(false);

  const updateStatus = async (nextStatus) => {
    await onRefresh({
      method: "PATCH",
      body: JSON.stringify({ id: booking.id, status: nextStatus }),
      headers: { "Content-Type": "application/json" },
    });
  };

  const handleReviewSubmit = async (event) => {
    event.preventDefault();
    setSubmittingReview(true);
    await onReview(booking.id, Number(rating), comment);
    setSubmittingReview(false);
    setComment("");
  };

  return (
    <div className="market-card booking-card">
      <div className="card-topline">
        <span className="tag">{booking.service?.name || "Service"}</span>
        <span className="status-badge">{booking.status.replaceAll("_", " ")}</span>
      </div>
      <h4>{booking.service_provider?.user?.username || "Awaiting provider"}</h4>
      <p>Location: {booking.location}</p>
      <p>
        Slot: {booking.date} at {booking.time}
      </p>
      <p>Payment: {booking.payment_status}</p>
      {booking.notes ? <p>Notes: {booking.notes}</p> : null}

      <div className="action-row">
        {booking.status === "assigned" ? (
          <button className="btn btn-primary" onClick={() => updateStatus("in_progress")} type="button">
            Start Service
          </button>
        ) : null}

        {booking.status === "in_progress" ? (
          <button className="btn btn-success" onClick={() => updateStatus("completed")} type="button">
            Mark Completed
          </button>
        ) : null}

        {booking.status === "requested" ? (
          <button className="btn btn-outline-secondary" onClick={() => updateStatus("cancelled")} type="button">
            Cancel
          </button>
        ) : null}

        {booking.status === "completed" && booking.payment_status !== "credited" ? (
          <button className="btn btn-warning" onClick={() => onCompletePayment(booking.id)} type="button">
            Process Dummy Payment
          </button>
        ) : null}
      </div>

      {booking.status === "completed" ? (
        <form className="review-form" onSubmit={handleReviewSubmit}>
          <label>
            Rating
            <select
              className="form-control"
              onChange={(event) => setRating(event.target.value)}
              value={rating}
            >
              <option value="5">5</option>
              <option value="4">4</option>
              <option value="3">3</option>
              <option value="2">2</option>
              <option value="1">1</option>
            </select>
          </label>
          <textarea
            className="form-control"
            onChange={(event) => setComment(event.target.value)}
            placeholder="Share feedback"
            rows="3"
            value={comment}
          />
          <button className="btn btn-outline-secondary" disabled={submittingReview} type="submit">
            Submit Review
          </button>
        </form>
      ) : null}
    </div>
  );
};

const Bookings = ({ currentUser }) => {
  const [bookings, setBookings] = useState([]);
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadData = useCallback(async () => {
    if (!currentUser) {
      setBookings([]);
      setRequests([]);
      return;
    }

    const [requestsResult, bookingsResult] = await Promise.all([
      apiFetch(`/bookings/requests/?customer=${currentUser.id}`),
      apiFetch(`/bookings/?user=${currentUser.id}`),
    ]);

    if (!requestsResult.response.ok) {
      setError("Could not load service requests.");
      return;
    }
    if (!bookingsResult.response.ok) {
      setError("Could not load bookings.");
      return;
    }

    setRequests(requestsResult.data || []);
    setBookings(bookingsResult.data || []);
  }, [currentUser]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const refreshThroughAction = async (requestOptions) => {
    setMessage("");
    setError("");
    const { response, data } = await apiFetch("/bookings/", requestOptions);
    if (!response.ok) {
      setError(data?.error || "Could not update booking.");
      return;
    }

    setMessage(`Booking updated to ${data.status.replaceAll("_", " ")}.`);
    await loadData();
  };

  const handlePayment = async (bookingId) => {
    setMessage("");
    setError("");
    const { response, data } = await apiFetch("/payments/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ booking: bookingId }),
    });

    if (!response.ok) {
      setError(data?.error || "Could not process payment.");
      return;
    }

    setMessage(`Dummy payment complete. Provider credited Rs. ${data.provider_earnings}.`);
    await loadData();
  };

  const handleReview = async (bookingId, rating, comment) => {
    setMessage("");
    setError("");
    const { response, data } = await apiFetch("/reviews/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ booking: bookingId, rating, comment }),
    });

    if (!response.ok) {
      setError(data?.error || data?.booking?.[0] || "Could not submit review.");
      return;
    }

    setMessage(`Review submitted with rating ${data.rating}.`);
  };

  const handleCancelRequest = async (requestId) => {
    setMessage("");
    setError("");
    const { response, data } = await apiFetch("/bookings/requests/", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: requestId, action: "cancel" }),
    });

    if (!response.ok) {
      setError(data?.error || "Could not cancel request.");
      return;
    }

    setMessage(`Request updated to ${data.status.replaceAll("_", " ")}.`);
    await loadData();
  };

  if (!currentUser) {
    return (
      <div className="page-shell">
        <section className="panel">
          <h2>My Requests & Bookings</h2>
          <p>Please login first to track service requests, bookings, payments, and reviews.</p>
          <Link className="btn btn-primary" to="/login">
            Login
          </Link>
        </section>
      </div>
    );
  }

  return (
    <div className="page-shell">
      <section className="hero-panel">
        <div>
          <p className="eyebrow">Customer Journey</p>
          <h2>Track requests before they become bookings</h2>
          <p className="hero-copy">
            First you send a request, then the provider accepts it, schedules an
            inspection, or declines it. Confirmed work continues through booking,
            payment, and review here.
          </p>
        </div>
      </section>

      {message ? <div className="alert alert-success mt-4">{message}</div> : null}
      {error ? <div className="alert alert-danger mt-4">{error}</div> : null}

      <section className="panel mt-4">
        <div className="section-header">
          <h3>Your Service Requests</h3>
          <p>{requests.length ? "Track pending, accepted, inspection, and cancelled requests." : "No service requests yet."}</p>
        </div>
        <div className="card-grid">
          {requests.map((requestItem) => (
            <RequestCard key={requestItem.id} onCancel={handleCancelRequest} requestItem={requestItem} />
          ))}
        </div>
        {!requests.length ? (
          <div className="empty-state">
            Send your first request from the <Link to="/">services page</Link>.
          </div>
        ) : null}
      </section>

      <section className="panel mt-4">
        <div className="section-header">
          <h3>Your Confirmed Bookings</h3>
          <p>{bookings.length ? "Manage accepted work through completion, payment, and review." : "No confirmed bookings yet."}</p>
        </div>
        <div className="card-grid">
          {bookings.map((booking) => (
            <BookingCard
              booking={booking}
              key={booking.id}
              onCompletePayment={handlePayment}
              onRefresh={refreshThroughAction}
              onReview={handleReview}
            />
          ))}
        </div>
        {!bookings.length ? (
          <div className="empty-state">
            Accepted requests for fixed-price services will appear here as bookings.
          </div>
        ) : null}
      </section>
    </div>
  );
};

export default Bookings;
