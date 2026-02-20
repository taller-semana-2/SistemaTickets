import axios, {
  AxiosError,
  type InternalAxiosRequestConfig,
  type AxiosInstance,
} from 'axios';
import { clearTokens, getAccessToken, refreshAccessToken } from './auth';

interface RetryableRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

// Cliente para ticket-service
export const ticketApiClient = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Cliente para notification-service
export const notificationApiClient = axios.create({
  baseURL: 'http://localhost:8001/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Cliente para assignment-service
export const assignmentApiClient = axios.create({
  baseURL: 'http://localhost:8002/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Cliente para users-service
export const usersApiClient = axios.create({
  baseURL: 'http://localhost:8003/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor global para logging (opcional)
const logRequest = (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
  console.log(`→ ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);

  const token = getAccessToken();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
};

const logError = (error: AxiosError): Promise<never> => {
  console.error('❌ API Error:', error.response?.status, error.message);
  return Promise.reject(error);
};

const attachInterceptors = (client: AxiosInstance): void => {
  client.interceptors.request.use(logRequest);
  client.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const originalRequest = error.config as RetryableRequestConfig | undefined;

      if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
        originalRequest._retry = true;

        const newToken = await refreshAccessToken();
        if (newToken) {
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
          }

          return client(originalRequest);
        }

        clearTokens();
        localStorage.removeItem('ticketSystem_user');
        window.location.href = '/login';
      }

      return logError(error);
    }
  );
};

attachInterceptors(ticketApiClient);
attachInterceptors(notificationApiClient);
attachInterceptors(assignmentApiClient);
attachInterceptors(usersApiClient);
