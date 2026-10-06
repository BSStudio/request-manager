import { getErrorMessage } from 'admin/helpers/ErrorMessageProvider';
import { toast } from 'admin/providers/ToastProvider';

export const showErrorToast = (error: unknown) => {
  toast.showToast({
    detail: getErrorMessage(error),
    life: 3000,
    severity: 'error',
    summary: 'Hiba',
  });
};
