export function getErrorMessage(error: unknown, fallback = 'Something went wrong') {
  if (typeof error === 'string') {
    return error;
  }

  if (error && typeof error === 'object') {
    const maybeAxiosError = error as {
      message?: string;
      response?: {
        data?: {
          detail?: string;
        };
      };
    };

    if (maybeAxiosError.response?.data?.detail) {
      return maybeAxiosError.response.data.detail;
    }

    if (maybeAxiosError.message) {
      return maybeAxiosError.message;
    }
  }

  return fallback;
}
