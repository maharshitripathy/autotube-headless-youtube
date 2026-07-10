import axios from 'axios';

/**
 * Axios instance for the AutoTube API. Single-user HTTP Basic auth: the
 * encoded credentials are held in memory (sessionStorage) after login.
 */
export const api = axios.create({baseURL: '/api'});

const STORAGE_KEY = 'autotube_basic';

export function setCredentials(username: string, password: string) {
  const token = btoa(`${username}:${password}`);
  sessionStorage.setItem(STORAGE_KEY, token);
}

export function clearCredentials() {
  sessionStorage.removeItem(STORAGE_KEY);
}

export function hasCredentials(): boolean {
  return !!sessionStorage.getItem(STORAGE_KEY);
}

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem(STORAGE_KEY);
  if (token) {
    config.headers.Authorization = `Basic ${token}`;
  }
  return config;
});

// Types mirrored from the backend schemas.
export interface Channel {
  id: number;
  youtube_channel_id: string;
  title: string;
  handle?: string | null;
  thumbnail_url?: string | null;
  niche?: string | null;
  autonomous: boolean;
  require_approval: boolean;
  uploads_per_day: number;
  active: boolean;
}

export interface Job {
  id: number;
  channel_id: number;
  video_id?: number | null;
  status: string;
  current_step?: string | null;
  error?: string | null;
  trigger: string;
}

export interface CalendarEntry {
  id: number;
  channel_id: number;
  scheduled_for: string;
  topic: string;
  notes?: string | null;
  source: string;
  locked: boolean;
  done: boolean;
}

export interface AnalyticsSummary {
  channel_id: number;
  total_views: number;
  total_watch_time_minutes: number;
  subscribers_gained: number;
  avg_ctr: number;
  videos_published: number;
}
