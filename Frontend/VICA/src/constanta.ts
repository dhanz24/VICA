
const isBrowser = typeof window !== 'undefined';
const isDev = process.env.NODE_ENV === 'development';


export const APP_NAME = 'VICA';

export const VICA_HOSTNAME = isBrowser ? (isDev ? `${location.hostname}:8000` : ``) : '';
export const VICA_BASE_URL = isBrowser ? (isDev ? `http://${VICA_HOSTNAME}` : ``) : ``;

