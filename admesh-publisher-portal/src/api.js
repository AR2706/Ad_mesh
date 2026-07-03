import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Automatically attach the JWT token to every request if it exists
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("admesh_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  login: async (username, password) => {
    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);
    // Remember, we changed this from /login to /token in the backend!
    const response = await api.post("/token", formData);
    return response.data;
  },
};

export const advertiserAPI = {
  createRule: async (ruleData) => {
    const response = await api.post("/rules", ruleData);
    return response.data;
  },
};

export const publisherAPI = {
  deploy: async (provider, targetRepo) => {
    const response = await api.post("/deploy", {
      provider: provider,
      target_repo: targetRepo,
    });
    return response.data;
  },
};

export default api;
