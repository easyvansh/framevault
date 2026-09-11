import axios from "axios";

const baseURLCandidates = [
  import.meta.env.VITE_API_URL,
  import.meta.env.DEV ? "" : undefined,
  "http://127.0.0.1:8001",
  "http://127.0.0.1:8000",
].filter((value, index, values) => value !== undefined && values.indexOf(value) === index);

let activeBaseURL = baseURLCandidates[0];

export function resolveMediaUrl(value) {
  if (!value || /^(https?:|data:|blob:)/i.test(value)) return value;
  const path = value.startsWith("/") ? value : `/${value}`;
  return `${activeBaseURL}${path}`;
}

async function request(config) {
  let lastError;

  for (const baseURL of [activeBaseURL, ...baseURLCandidates].filter((value, index, values) => values.indexOf(value) === index)) {
    const api = axios.create({ baseURL, timeout: 60000 });
    try {
      const response = await api.request(config);
      activeBaseURL = baseURL;
      return response;
    } catch (error) {
      const canRetry = !error.response && ["ERR_NETWORK", "ECONNABORTED"].includes(error.code);
      lastError = error;
      if (!canRetry) throw error;
    }
  }

  throw lastError;
}

export const searchFilmGrab = (query) => request({ method: "get", url: "/api/search", params: { q: query } });
export const scrapeFilm = (payload) => request({ method: "post", url: "/api/scrape", data: payload });
export const listFilms = () => request({ method: "get", url: "/api/films" });
export const listFrames = (filmId) => request({ method: "get", url: `/api/films/${filmId}/frames` });
export const getFrame = (frameId) => request({ method: "get", url: `/api/frames/${frameId}` });
<<<<<<< HEAD
export const getFrameDetails = (frameId) => request({ method: "get", url: `/api/frames/${frameId}/details` });
export const updateFilmMetadata = (filmId, data) => request({ method: "patch", url: `/api/films/${filmId}/metadata`, data });
=======
>>>>>>> 1b5c36d (updated to v2)
export const setFrameSelected = (frameId, selected) => request({ method: "post", url: `/api/frames/${frameId}/select`, data: { selected } });
export const listImages = (filmId) => request({ method: "get", url: `/api/films/${filmId}/images` });
export const setImageSelected = (imageId, selected) => request({ method: "post", url: `/api/images/${imageId}/select`, data: { selected } });
export const downloadSelected = (filmId) => request({ method: "post", url: "/api/download/selected", data: { film_id: filmId } });
export const downloadAll = (filmId) => request({ method: "post", url: "/api/download/all", data: { film_id: filmId } });
export const uploadImages = (files) => {
  const data = new FormData();
  files.forEach((file) => data.append("files", file));
  return request({ method: "post", url: "/api/ingestion/images", data });
};
export const uploadVideo = (file) => {
  const data = new FormData();
  data.append("file", file);
  return request({ method: "post", url: "/api/ingestion/videos", data });
};
export const extractVideoShots = (assetId, threshold = 0.3) => request({ method: "post", url: `/api/media-assets/${assetId}/shots`, params: { threshold } });
export const getVideoShots = (assetId) => request({ method: "get", url: `/api/media-assets/${assetId}/shots` });
export const analyzeFrame = (frameId) => request({ method: "post", url: `/api/frames/${frameId}/analysis` });
export const getFrameAnalysis = (frameId) => request({ method: "get", url: `/api/frames/${frameId}/analysis` });
