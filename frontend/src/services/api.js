import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

export const summarizeVideo = async (videoUrl) => {
  const response = await api.post('/summarize', { video_url: videoUrl });
  return response.data;
};

export const chatWithVideo = async (videoUrl, query) => {
  const response = await api.post('/chat', { video_url: videoUrl, query: query });
  return response.data;
};
