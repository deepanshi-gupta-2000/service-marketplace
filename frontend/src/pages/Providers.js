import React, { useEffect, useMemo, useState } from "react";

import { apiFetch } from "../auth";

const Providers = ({ filters, onChooseProvider, selectedProviderId, serviceId }) => {
  const [providers, setProviders] = useState([]);
  const [error, setError] = useState("");

  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    params.set("service", serviceId);

    if (filters.location) {
      params.set("location", filters.location);
    }
    if (filters.minPrice) {
      params.set("min_price", filters.minPrice);
    }
    if (filters.maxPrice) {
      params.set("max_price", filters.maxPrice);
    }
    if (filters.minRating) {
      params.set("min_rating", filters.minRating);
    }
    if (filters.sortBy) {
      params.set("sort_by", filters.sortBy);
    }

    return params.toString();
  }, [filters, serviceId]);

  useEffect(() => {
    const loadProviders = async () => {
      setError("");
      const { response, data } = await apiFetch(`/providers/?${queryString}`);

      if (!response.ok) {
        setError("Could not load providers.");
        return;
      }

      setProviders(data || []);
    };

    if (serviceId) {
      loadProviders();
    }
  }, [queryString, serviceId]);

  if (!serviceId) {
    return null;
  }

  return (
    <div className="panel mt-4">
      <div className="section-header">
        <h3>Available Providers</h3>
        <p>Filter by location, budget, and rating, then select a provider or use auto-assignment.</p>
      </div>

      {selectedProviderId ? (
        <div className="alert alert-info">
          A provider is selected for this request. You can now send the request below, or switch to another provider.
        </div>
      ) : null}

      {error ? <div className="alert alert-danger">{error}</div> : null}

      <div className="card-grid">
        {providers.map((provider) => {
          const selected = selectedProviderId === provider.id;
          return (
            <div className={`market-card ${selected ? "selected" : ""}`} key={provider.id}>
              <div className="card-topline">
                <span className="tag">{provider.service.name}</span>
                <span className="rating">Rating: {provider.average_rating || 0}</span>
              </div>
              <h4>{provider.provider_profile?.display_name || provider.user.username}</h4>
              <p>{provider.provider_profile?.skills_summary || "General home services"}</p>
              <p>{provider.pricing_type_label}</p>
              <p>{provider.pricing_display}</p>
              <p>Location: {provider.location}</p>
              <p>Experience: {provider.experience} years</p>
              <p>Active jobs: {provider.active_jobs}</p>
              <button
                className={`btn ${selected ? "btn-success" : "btn-primary"} mt-2`}
                onClick={() => onChooseProvider(provider.id)}
                type="button"
              >
                {selected ? "Selected Provider" : "Choose Provider"}
              </button>
            </div>
          );
        })}
      </div>

      {!providers.length && !error ? (
        <div className="empty-state">
          No providers matched the current service, location, price, and rating filters.
        </div>
      ) : null}
    </div>
  );
};

export default Providers;
