import axios from "axios";

const baseURLCandidates = [
  import.meta.env.VITE_API_URL,
  "",
  "http://127.0.0.1:8001",
  "http://127.0.0.1:8000",
].filter((value, index, values) => value !== undefined && values.indexOf(value) === index);

let activeBaseURL = baseURLCandidates[0];

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
export const listImages = (filmId) => request({ method: "get", url: `/api/films/${filmId}/images` });
export const setImageSelected = (imageId, selected) => request({ method: "post", url: `/api/images/${imageId}/select`, data: { selected } });
export const downloadSelected = (filmId) => request({ method: "post", url: "/api/download/selected", data: { film_id: filmId } });
export const downloadAll = (filmId) => request({ method: "post", url: "/api/download/all", data: { film_id: filmId } });
