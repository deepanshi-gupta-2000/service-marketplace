import React, { useEffect, useState } from "react";
import Providers from "./Providers";

const Services = () => {
  const [services, setServices] = useState([]);
  const [selectedService, setSelectedService] = useState(null);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/services/")
      .then((res) => res.json())
      .then((data) => setServices(data));
  }, []);

  return (
    <div className="container mt-4">
      <h2 className="mb-4">Services</h2>

      <div className="row">
        {services.map((service) => (
          <div className="col-md-4" key={service.id}>
            <div className="card p-3 mb-3 shadow-sm">
              <h5>{service.name}</h5>
              <button
                className="btn btn-primary mt-2"
                onClick={() => setSelectedService(service.id)}
              >
                View Providers
              </button>
            </div>
          </div>
        ))}
      </div>

      {selectedService && <Providers serviceId={selectedService} />}
    </div>
  );
};

export default Services;