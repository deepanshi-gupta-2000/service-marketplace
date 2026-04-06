const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:8000/api";
const ACCESS_TOKEN_KEY = "serviceMarketplaceAccessToken";
const REFRESH_TOKEN_KEY = "serviceMarketplaceRefreshToken";

export const getAccessToken = () => localStorage.getItem(ACCESS_TOKEN_KEY);
export const getRefreshToken = () => localStorage.getItem(REFRESH_TOKEN_KEY);

export const setTokens = ({ access, refresh }) => {
  if (access) {
    localStorage.setItem(ACCESS_TOKEN_KEY, access);
  }
  if (refresh) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  }
};

export const clearAccessToken = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
};

export const getAuthHeaders = () => {
  const token = getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

let refreshPromise = null;

const refreshAccessToken = async () => {
  const refresh = getRefreshToken();
  if (!refresh) {
    clearAccessToken();
    return null;
  }

  const response = await fetch(`${API_BASE_URL}/auth/refresh/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ refresh }),
  });

  let data = null;
  try {
    data = await response.json();
  } catch (error) {
    data = null;
  }

  if (!response.ok || !data?.access) {
    clearAccessToken();
    return null;
  }

  setTokens({ access: data.access });
  return data.access;
};

const getFreshAccessToken = async () => {
  if (!refreshPromise) {
    refreshPromise = refreshAccessToken().finally(() => {
      refreshPromise = null;
    });
  }

  return refreshPromise;
};

export const apiFetch = async (path, options = {}) => {
  const { headers, _retried, ...restOptions } = options;
  const makeRequest = async () =>
    fetch(`${API_BASE_URL}${path}`, {
      ...restOptions,
      headers: {
        ...headers,
        ...getAuthHeaders(),
      },
    });

  let response = await makeRequest();

  let data = null;
  try {
    data = await response.json();
  } catch (error) {
    data = null;
  }

  if (response.status === 401 && !_retried && path !== "/auth/refresh/") {
    const newAccessToken = await getFreshAccessToken();
    if (newAccessToken) {
      response = await makeRequest();
      try {
        data = await response.json();
      } catch (error) {
        data = null;
      }
    }
  }

  return { response, data };
};

export const fetchCurrentUser = async () => {
  const token = getAccessToken();
  if (!token) {
    return null;
  }

  const { response, data } = await apiFetch("/auth/me/");

  if (response.status === 401) {
    clearAccessToken();
    return null;
  }

  if (!response.ok) {
    throw new Error("Could not load current user.");
  }

  return data;
};

export { API_BASE_URL };
