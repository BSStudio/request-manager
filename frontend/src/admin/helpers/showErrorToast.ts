import { getErrorMessage } from 'admin/helpers/ErrorMessageProvider';
import { toast } from 'admin/providers/ToastProvider';

export const showErrorToast = (error: unknown) => {
  let detail: string;
  try {
    detail = getErrorMessage(error);
  } catch {
    detail = 'Ismeretlen hiba történt';
  }
  toast.showToast({
    detail,
    life: 3000,
    severity: 'error',
    summary: 'Hiba',
  });
};
