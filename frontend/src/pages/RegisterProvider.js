import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { apiFetch } from "../auth";

const emptyServiceForm = {
  serviceNames: "",
  price: "",
  pricingType: "fixed",
  locationName: "",
  experience: "",
};

const emptyProfileForm = {
  display_name: "",
  bio: "",
  skills_summary: "",
  availability_notes: "",
  default_location: "",
  available_from: "",
  available_to: "",
  is_accepting_jobs: true,
};

const formatCurrency = (value) => `Rs. ${Number(value || 0).toLocaleString("en-IN")}`;

const RegisterProvider = ({ authReady, currentUser, refreshCurrentUser }) => {
  const [serviceForm, setServiceForm] = useState(emptyServiceForm);
  const [profileForm, setProfileForm] = useState(emptyProfileForm);
  const [providerServices, setProviderServices] = useState([]);
  const [incomingRequests, setIncomingRequests] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [steppingDown, setSteppingDown] = useState(false);
  const [savingId, setSavingId] = useState(null);
  const [requestActionId, setRequestActionId] = useState(null);
  const [savingProfile, setSavingProfile] = useState(false);

  const isProfessional = currentUser?.role === "professional";

  const loadProviderServices = useCallback(async () => {
    if (!currentUser) {
      setProviderServices([]);
      return;
    }

    const { response, data } = await apiFetch(`/providers/?user=${currentUser.id}`);
    if (!response.ok) {
      setError("Could not load your provider services.");
      return;
    }

    setProviderServices(data || []);
  }, [currentUser]);

  const loadIncomingRequests = useCallback(async () => {
    if (!currentUser || currentUser.role !== "professional") {
      setIncomingRequests([]);
      return;
    }

    const { response, data } = await apiFetch(
      `/bookings/requests/?provider_user=${currentUser.id}&status=pending_provider_response`
    );
    if (!response.ok) {
      setError("Could not load incoming requests.");
      return;
    }

    setIncomingRequests(data || []);
  }, [currentUser]);

  const loadDashboard = useCallback(async () => {
    if (!currentUser || currentUser.role !== "professional") {
      setDashboard(null);
      setProfileForm(emptyProfileForm);
      return;
    }

    const { response, data } = await apiFetch("/providers/dashboard/");
    if (!response.ok) {
      setError("Could not load provider dashboard.");
      return;
    }

    setDashboard(data);
    setProviderServices(data.active_services || []);
    setProfileForm({
      display_name: data.profile?.display_name || "",
      bio: data.profile?.bio || "",
      skills_summary: data.profile?.skills_summary || "",
      availability_notes: data.profile?.availability_notes || "",
      default_location: data.profile?.default_location || "",
      available_from: data.profile?.available_from || "",
      available_to: data.profile?.available_to || "",
      is_accepting_jobs: data.profile?.is_accepting_jobs ?? true,
    });
  }, [currentUser]);

  useEffect(() => {
    loadProviderServices();
  }, [loadProviderServices]);

  useEffect(() => {
    loadIncomingRequests();
  }, [loadIncomingRequests]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage("");
    setError("");

    const { response, data } = await apiFetch("/providers/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        service_names: serviceForm.serviceNames
          .split(/\r?\n|,/)
          .map((name) => name.trim())
          .filter(Boolean),
        price: Number(serviceForm.price),
        pricing_type: serviceForm.pricingType,
        location: serviceForm.locationName,
        experience: Number(serviceForm.experience || 0),
      }),
    });

    if (!response.ok) {
      if (response.status === 401) {
        setError("Please log in with your customer account to upgrade it to provider.");
        return;
      }

      setError(data?.error || "Provider registration failed.");
      return;
    }

    await refreshCurrentUser();
    await loadProviderServices();
    await loadIncomingRequests();
    await loadDashboard();
    const createdServices = (data.providers || []).map((provider) => provider.service.name);
    const skippedServices = data.skipped_services?.length
      ? ` Skipped existing services: ${data.skipped_services.join(", ")}.`
      : "";

    setMessage(`Services saved: ${createdServices.join(", ")}.${skippedServices}`);
    setServiceForm(emptyServiceForm);
  };

  const handleProfileSave = async (event) => {
    event.preventDefault();
    setMessage("");
    setError("");
    setSavingProfile(true);

    const { response, data } = await apiFetch("/providers/profile/", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(profileForm),
    });

    setSavingProfile(false);

    if (!response.ok) {
      setError("Could not update provider profile.");
      return;
    }

    setProfileForm({
      display_name: data.display_name || "",
      bio: data.bio || "",
      skills_summary: data.skills_summary || "",
      availability_notes: data.availability_notes || "",
      default_location: data.default_location || "",
      available_from: data.available_from || "",
      available_to: data.available_to || "",
      is_accepting_jobs: data.is_accepting_jobs ?? true,
    });
    await loadDashboard();
    setMessage("Provider profile updated.");
  };

  const handleUpdateService = async (providerId, updates) => {
    setMessage("");
    setError("");
    setSavingId(providerId);

    const { response, data } = await apiFetch(`/providers/${providerId}/`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(updates),
    });

    setSavingId(null);

    if (!response.ok) {
      setError(data?.error || "Could not update provider service.");
      return;
    }

    setProviderServices((current) =>
      current.map((provider) => (provider.id === providerId ? data : provider))
    );
    await loadDashboard();
    setMessage(`Updated ${data.service.name} successfully.`);
  };

  const handleDeactivateService = async (providerId) => {
    setMessage("");
    setError("");
    setSavingId(providerId);

    const { response, data } = await apiFetch(`/providers/${providerId}/`, {
      method: "DELETE",
    });

    setSavingId(null);

    if (!response.ok) {
      setError(data?.error || "Could not remove service.");
      return;
    }

    setProviderServices((current) => current.filter((provider) => provider.id !== providerId));
    await loadDashboard();
    setMessage(data.message);
  };

  const handleRequestAction = async (requestId, action) => {
    setMessage("");
    setError("");
    setRequestActionId(requestId);

    const { response, data } = await apiFetch("/bookings/requests/", {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ id: requestId, action }),
    });

    setRequestActionId(null);

    if (!response.ok) {
      setError(data?.error || "Could not update request.");
      return;
    }

    await loadIncomingRequests();
    await loadDashboard();
    if (data.status === "booking_created") {
      setMessage(`Request accepted. Booking #${data.created_booking?.id} is now confirmed.`);
      return;
    }

    if (data.status === "inspection_scheduled") {
      setMessage("Request accepted. This service now moves into inspection scheduling.");
      return;
    }

    setMessage(`Request updated to ${data.status.replaceAll("_", " ")}.`);
  };

  const handleStepDown = async () => {
    setMessage("");
    setError("");
    setSteppingDown(true);

    const { response, data } = await apiFetch("/providers/profile/", {
      method: "DELETE",
    });

    setSteppingDown(false);

    if (!response.ok) {
      setError(data?.error || "Could not step down from professional role.");
      return;
    }

    await refreshCurrentUser();
    setProviderServices([]);
    setDashboard(null);
    const deactivatedServices = data.deactivated_services?.length
      ? ` Deactivated services: ${data.deactivated_services.join(", ")}.`
      : "";
    setMessage(
      `Your account is now back to customer. Provider history has been preserved.${deactivatedServices}`
    );
  };

  if (!authReady) {
    return (
      <div className="page-shell">
        <section className="panel">
          <h2>Provider Services</h2>
          <p>Loading account...</p>
        </section>
      </div>
    );
  }

  if (!currentUser) {
    return (
      <div className="page-shell">
        <section className="hero-panel">
          <div>
            <p className="eyebrow">Provider Flow</p>
            <h2>Become a Provider</h2>
            <p className="hero-copy">
              Upgrade your existing customer account to a provider account and add one or
              more services for the demo marketplace.
            </p>
          </div>
        </section>

        <section className="panel">
          <div className="alert alert-info">
            Please log in first so we know which customer account should be upgraded.
          </div>
          <div className="hero-actions">
            <Link className="btn btn-primary" to="/login">
              Login
            </Link>
            <Link className="btn btn-outline-secondary" to="/register">
              Create Account
            </Link>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="page-shell">
      <section className="hero-panel">
        <div>
          <p className="eyebrow">Provider Flow</p>
          <h2>{isProfessional ? "Provider Dashboard" : "Become a Provider"}</h2>
          <p className="hero-copy">
            Signed in as <strong>{currentUser.username}</strong>.{" "}
            {isProfessional
              ? "Track requests, earnings, ratings, and service operations from one place."
              : "Add one or more services, pricing, and location to start receiving jobs."}
          </p>
        </div>
      </section>

      {message ? <div className="alert alert-success">{message}</div> : null}
      {error ? <div className="alert alert-danger">{error}</div> : null}

      {isProfessional && dashboard ? (
        <>
          <section className="panel">
            <div className="section-header">
              <h3>Business Snapshot</h3>
              <p>Quick metrics for your provider activity in the demo marketplace.</p>
            </div>
            <div className="dashboard-grid">
              <StatCard label="Active Services" value={dashboard.summary.active_service_count} />
              <StatCard label="Pending Requests" value={dashboard.summary.pending_request_count} />
              <StatCard label="Active Jobs" value={dashboard.summary.active_booking_count} />
              <StatCard label="Completed Jobs" value={dashboard.summary.completed_booking_count} />
              <StatCard label="Average Rating" value={dashboard.summary.average_rating} />
              <StatCard label="Reviews" value={dashboard.summary.review_count} />
              <StatCard label="Provider Earnings" value={formatCurrency(dashboard.summary.total_earnings)} />
              <StatCard label="Platform Fee" value={formatCurrency(dashboard.summary.total_platform_fee)} />
            </div>
          </section>

          <section className="panel">
            <div className="section-header">
              <h3>Provider Profile</h3>
              <p>Update the public details customers will see when evaluating your services.</p>
            </div>
            <form className="booking-form" onSubmit={handleProfileSave}>
              <input
                className="form-control"
                onChange={(event) =>
                  setProfileForm((current) => ({ ...current, display_name: event.target.value }))
                }
                placeholder="Display name"
                type="text"
                value={profileForm.display_name}
              />
              <textarea
                className="form-control"
                onChange={(event) =>
                  setProfileForm((current) => ({ ...current, bio: event.target.value }))
                }
                placeholder="Short bio"
                rows="3"
                value={profileForm.bio}
              />
              <textarea
                className="form-control"
                onChange={(event) =>
                  setProfileForm((current) => ({ ...current, skills_summary: event.target.value }))
                }
                placeholder="Skills summary"
                rows="3"
                value={profileForm.skills_summary}
              />
              <textarea
                className="form-control"
                onChange={(event) =>
                  setProfileForm((current) => ({ ...current, availability_notes: event.target.value }))
                }
                placeholder="Availability notes"
                rows="3"
                value={profileForm.availability_notes}
              />
              <input
                className="form-control"
                onChange={(event) =>
                  setProfileForm((current) => ({ ...current, default_location: event.target.value }))
                }
                placeholder="Default city / service area"
                type="text"
                value={profileForm.default_location}
              />
              <div className="filter-grid">
                <input
                  className="form-control"
                  onChange={(event) =>
                    setProfileForm((current) => ({ ...current, available_from: event.target.value }))
                  }
                  type="time"
                  value={profileForm.available_from || ""}
                />
                <input
                  className="form-control"
                  onChange={(event) =>
                    setProfileForm((current) => ({ ...current, available_to: event.target.value }))
                  }
                  type="time"
                  value={profileForm.available_to || ""}
                />
              </div>
              <label className="checkbox-row">
                <input
                  checked={profileForm.is_accepting_jobs}
                  onChange={(event) =>
                    setProfileForm((current) => ({
                      ...current,
                      is_accepting_jobs: event.target.checked,
                    }))
                  }
                  type="checkbox"
                />
                Accept new jobs
              </label>
              <button className="btn btn-primary" disabled={savingProfile} type="submit">
                {savingProfile ? "Saving..." : "Save Profile"}
              </button>
            </form>
          </section>

          <section className="panel">
            <div className="section-header">
              <h3>Your Active Services</h3>
              <p>Edit the services you currently provide.</p>
            </div>

            <div className="card-grid">
              {providerServices.map((provider) => (
                <ProviderServiceCard
                  key={provider.id}
                  onDeactivate={handleDeactivateService}
                  onSave={handleUpdateService}
                  provider={provider}
                  saving={savingId === provider.id}
                />
              ))}
            </div>

            {!providerServices.length ? (
              <div className="empty-state">You do not have any active provider services right now.</div>
            ) : null}
          </section>

          <section className="panel mt-4">
            <div className="section-header">
              <h3>Incoming Service Requests</h3>
              <p>Customers send interest first. Accept to create a booking or move inspection-based services into the next step.</p>
            </div>

            <div className="card-grid">
              {incomingRequests.map((requestItem) => (
                <div className="market-card booking-card" key={requestItem.id}>
                  <div className="card-topline">
                    <span className="tag">{requestItem.service?.name}</span>
                    <span className="status-badge">{requestItem.status.replaceAll("_", " ")}</span>
                  </div>
                  <h4>{requestItem.customer?.username}</h4>
                  <p>Location: {requestItem.location}</p>
                  <p>
                    Preferred slot: {requestItem.date} at {requestItem.time}
                  </p>
                  {requestItem.notes ? <p>Customer notes: {requestItem.notes}</p> : null}
                  <div className="action-row">
                    <button
                      className="btn btn-primary"
                      disabled={requestActionId === requestItem.id}
                      onClick={() => handleRequestAction(requestItem.id, "accept")}
                      type="button"
                    >
                      {requestActionId === requestItem.id ? "Updating..." : "Accept"}
                    </button>
                    <button
                      className="btn btn-outline-secondary"
                      disabled={requestActionId === requestItem.id}
                      onClick={() => handleRequestAction(requestItem.id, "reject")}
                      type="button"
                    >
                      Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {!incomingRequests.length ? (
              <div className="empty-state">No pending customer requests right now.</div>
            ) : null}
          </section>

          <section className="panel mt-4">
            <div className="section-header">
              <h3>Operations Feed</h3>
              <p>Recent active jobs, reviews, and dummy payouts in one place.</p>
            </div>
            <div className="dashboard-columns">
              <DashboardList
                items={dashboard.active_bookings}
                renderItem={(item) => (
                  <>
                    <strong>{item.service_name}</strong>
                    <span>{item.customer_name}</span>
                    <span>{item.location}</span>
                    <span>{item.status.replaceAll("_", " ")}</span>
                  </>
                )}
                title="Active Jobs"
              />
              <DashboardList
                items={dashboard.recent_reviews}
                renderItem={(item) => (
                  <>
                    <strong>{item.service_name}</strong>
                    <span>{item.customer_name}</span>
                    <span>{item.rating}/5</span>
                    <span>{item.comment || "No comment shared"}</span>
                  </>
                )}
                title="Recent Reviews"
              />
              <DashboardList
                items={dashboard.recent_payments}
                renderItem={(item) => (
                  <>
                    <strong>{item.service_name}</strong>
                    <span>{item.customer_name}</span>
                    <span>Earnings: {formatCurrency(item.provider_earnings)}</span>
                    <span>Status: {item.status}</span>
                  </>
                )}
                title="Recent Dummy Payments"
              />
            </div>
          </section>
        </>
      ) : null}

      <section className="panel">
        <div className="section-header">
          <h3>{isProfessional ? "Add More Services" : "Provider Onboarding"}</h3>
          <p>
            Your current role is <strong>{currentUser.role}</strong>. Use this form to{" "}
            {isProfessional ? "expand your active catalog" : "upgrade the same account"}.
          </p>
        </div>

        {isProfessional ? (
          <div className="alert alert-info">
            If you want to stop being a professional, you can step down to customer.
            Your old services, ratings, reviews, and provider history will still be
            stored for future reference.
            <div className="mt-2">
              <button
                className="btn btn-outline-secondary"
                disabled={steppingDown}
                onClick={handleStepDown}
                type="button"
              >
                {steppingDown ? "Updating..." : "Step Down to Customer"}
              </button>
            </div>
          </div>
        ) : null}

        <form className="booking-form" onSubmit={handleSubmit}>
          <textarea
            className="form-control"
            onChange={(event) =>
              setServiceForm((current) => ({ ...current, serviceNames: event.target.value }))
            }
            placeholder="Services (example: Plumbing, Cleaning or one per line)"
            required
            rows="4"
            value={serviceForm.serviceNames}
          />
          <input
            className="form-control"
            onChange={(event) =>
              setServiceForm((current) => ({ ...current, price: event.target.value }))
            }
            placeholder={
              serviceForm.pricingType === "starting_from" ? "Starting price" : "Base price"
            }
            required
            type="number"
            value={serviceForm.price}
          />
          <select
            className="form-control"
            onChange={(event) =>
              setServiceForm((current) => ({ ...current, pricingType: event.target.value }))
            }
            value={serviceForm.pricingType}
          >
            <option value="fixed">Fixed Price</option>
            <option value="starting_from">Starting From</option>
            <option value="inspection">Inspection Required</option>
            <option value="custom_quote">Custom Quote</option>
          </select>
          <input
            className="form-control"
            onChange={(event) =>
              setServiceForm((current) => ({ ...current, experience: event.target.value }))
            }
            placeholder="Experience in years"
            type="number"
            value={serviceForm.experience}
          />
          <input
            className="form-control"
            onChange={(event) =>
              setServiceForm((current) => ({ ...current, locationName: event.target.value }))
            }
            placeholder="Primary location"
            required
            type="text"
            value={serviceForm.locationName}
          />
          <button className="btn btn-success" type="submit">
            {isProfessional ? "Add Services" : "Save Provider Services"}
          </button>
        </form>
      </section>
    </div>
  );
};

const StatCard = ({ label, value }) => (
  <div className="market-card stat-card">
    <span className="eyebrow">{label}</span>
    <strong className="stat-value">{value}</strong>
  </div>
);

const DashboardList = ({ items, renderItem, title }) => (
  <div className="market-card dashboard-list">
    <div className="section-header compact">
      <h3>{title}</h3>
    </div>
    {items?.length ? (
      <div className="feed-list">
        {items.map((item) => (
          <div className="feed-item" key={item.id}>
            {renderItem(item)}
          </div>
        ))}
      </div>
    ) : (
      <div className="empty-state">No recent activity yet.</div>
    )}
  </div>
);

const ProviderServiceCard = ({ onDeactivate, onSave, provider, saving }) => {
  const [price, setPrice] = useState(provider.price);
  const [pricingType, setPricingType] = useState(provider.pricing_type);
  const [location, setLocation] = useState(provider.location);
  const [experience, setExperience] = useState(provider.experience);

  return (
    <div className="market-card">
      <div className="card-topline">
        <span className="tag">{provider.service.name}</span>
        <span className="rating">Rating: {provider.average_rating || 0}</span>
      </div>
      <p>{provider.pricing_display}</p>
      <p>Active jobs: {provider.active_jobs}</p>

      <div className="booking-form">
        <input
          className="form-control"
          onChange={(event) => setPrice(event.target.value)}
          type="number"
          value={price}
        />
        <select
          className="form-control"
          onChange={(event) => setPricingType(event.target.value)}
          value={pricingType}
        >
          <option value="fixed">Fixed Price</option>
          <option value="starting_from">Starting From</option>
          <option value="inspection">Inspection Required</option>
          <option value="custom_quote">Custom Quote</option>
        </select>
        <input
          className="form-control"
          onChange={(event) => setLocation(event.target.value)}
          type="text"
          value={location}
        />
        <input
          className="form-control"
          onChange={(event) => setExperience(event.target.value)}
          type="number"
          value={experience}
        />
      </div>

      <div className="action-row mt-2">
        <button
          className="btn btn-primary"
          disabled={saving}
          onClick={() =>
            onSave(provider.id, {
              price: Number(price),
              pricing_type: pricingType,
              location,
              experience: Number(experience || 0),
            })
          }
          type="button"
        >
          {saving ? "Saving..." : "Save Changes"}
        </button>
        <button
          className="btn btn-outline-secondary"
          disabled={saving}
          onClick={() => onDeactivate(provider.id)}
          type="button"
        >
          Remove Service
        </button>
      </div>
    </div>
  );
};

export default RegisterProvider;
