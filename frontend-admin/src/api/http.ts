import { create, isAxiosError } from 'axios';

import { isAdminPath } from 'helpers/isAdminPath';
import { clearSession, setRedirectedFrom } from 'helpers/LocalStorageHelper';

import {
  AdminApiFactory,
  LoginApiFactory,
  LogoutApiFactory,
  MeApiFactory,
  MiscApiFactory,
  RequestsApiFactory,
} from './api';

const axiosInstance = create({
  headers: {
    'Accept-Language': 'hu',
  },
  // Django rejects unsafe requests of a session without this header.
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
});

axiosInstance.interceptors.response.use(undefined, (error) => {
  if (isAxiosError(error) && error.response?.status === 401) {
    clearSession();
    if (isAdminPath(window.location.pathname)) {
      setRedirectedFrom(window.location.pathname);
      window.location.href = '/login';
    }
  }
  return Promise.reject(error);
});

// Same origin as the page, so the session cookie is sent. The dev server
// proxies /api to the backend.
const basePath = '';

export const adminApi = AdminApiFactory(undefined, basePath, axiosInstance);
export const loginApi = LoginApiFactory(undefined, basePath, axiosInstance);
export const logoutApi = LogoutApiFactory(undefined, basePath, axiosInstance);
export const meApi = MeApiFactory(undefined, basePath, axiosInstance);
export const miscApi = MiscApiFactory(undefined, basePath, axiosInstance);
export const requestsApi = RequestsApiFactory(
  undefined,
  basePath,
  axiosInstance,
);
