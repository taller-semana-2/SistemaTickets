import axios from 'axios';

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
const logRequest = (config: any) => {
  console.log(`→ ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
  return config;
};

const logError = (error: any) => {
  console.error('❌ API Error:', error.response?.status, error.message);
  return Promise.reject(error);
};

ticketApiClient.interceptors.request.use(logRequest);
ticketApiClient.interceptors.response.use((response) => response, logError);

notificationApiClient.interceptors.request.use(logRequest);
notificationApiClient.interceptors.response.use((response) => response, logError);

assignmentApiClient.interceptors.request.use(logRequest);
assignmentApiClient.interceptors.response.use((response) => response, logError);

usersApiClient.interceptors.request.use(logRequest);
usersApiClient.interceptors.response.use((response) => response, logError);
