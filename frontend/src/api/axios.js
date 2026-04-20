import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 60000, // 60s timeout for LLM processing
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
