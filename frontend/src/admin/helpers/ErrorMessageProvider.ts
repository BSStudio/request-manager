import { isAxiosError } from 'axios';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function getErrorMessage(error: any) {
  if (isAxiosError(error)) {
    if (error.response) {
      return JSON.stringify(error.response.data);
    }
    return error.message;
  } else if (error instanceof Error) {
    return error.message;
  } else if (typeof error === 'string') {
    return error;
  }
  throw error;
}
