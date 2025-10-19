import { toast } from '@/hooks/use-toast';

/**
 * Toast options interface
 */
export interface ToastOptions {
  title: string;
  description?: string;
  variant?: 'default' | 'destructive' | 'success';
  duration?: number;
}

/**
 * Show a toast notification
 * @param options - Toast configuration options
 */
export function showToast(options: ToastOptions): void {
  const { title, description, variant = 'default', duration = 5000 } = options;

  // Map 'success' variant to 'default' with appropriate styling
  const toastVariant = variant === 'success' ? 'default' : variant;

  toast({
    title,
    description,
    variant: toastVariant,
    duration,
    // Add success styling class if needed
    className: variant === 'success' ? 'border-green-500 bg-green-50 text-green-900' : undefined,
  });
}

/**
 * Show an error toast
 * @param title - Error title
 * @param description - Error description (optional)
 */
export function showErrorToast(title: string, description?: string): void {
  showToast({
    title,
    description,
    variant: 'destructive',
    duration: 5000,
  });
}

/**
 * Show a success toast
 * @param title - Success title
 * @param description - Success description (optional)
 */
export function showSuccessToast(title: string, description?: string): void {
  showToast({
    title,
    description,
    variant: 'success',
    duration: 3000,
  });
}

/**
 * Show a validation error toast
 * @param errors - Array of validation error messages
 */
export function showValidationErrorToast(errors: string[]): void {
  showToast({
    title: 'Validation Error',
    description: errors.join(', '),
    variant: 'destructive',
    duration: 5000,
  });
}

/**
 * Show a network error toast
 */
export function showNetworkErrorToast(): void {
  showToast({
    title: 'Network Error',
    description: 'Please check your connection and try again',
    variant: 'destructive',
    duration: 5000,
  });
}
