import axios from 'axios';

// In production, set VITE_API_URL to your Render backend URL
// e.g. VITE_API_URL=https://agenttube-ai-backend.onrender.com
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

export const summarizeVideo = async (videoUrl) => {
  const response = await api.post('/summarize', { video_url: videoUrl });
  return response.data;
};

export const chatWithVideo = async (videoUrl, query) => {
  const response = await api.post('/chat', { video_url: videoUrl, query: query });
  return response.data;
};
