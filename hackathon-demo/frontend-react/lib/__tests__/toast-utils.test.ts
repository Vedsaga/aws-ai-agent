/**
 * Toast utility functions tests
 * 
 * These tests verify that toast functions are properly exported and callable.
 * Actual toast rendering is tested through component integration tests.
 */

import { 
  showToast, 
  showErrorToast, 
  showSuccessToast, 
  showValidationErrorToast,
  showNetworkErrorToast,
  type ToastOptions 
} from '../toast-utils';

describe('Toast Utilities', () => {
  // Mock the toast hook
  jest.mock('@/hooks/use-toast', () => ({
    toast: jest.fn(),
  }));

  describe('showToast', () => {
    it('should be a function', () => {
      expect(typeof showToast).toBe('function');
    });

    it('should accept ToastOptions', () => {
      const options: ToastOptions = {
        title: 'Test',
        description: 'Test description',
        variant: 'default',
        duration: 5000,
      };
      
      // Should not throw
      expect(() => showToast(options)).not.toThrow();
    });
  });

  describe('showErrorToast', () => {
    it('should be a function', () => {
      expect(typeof showErrorToast).toBe('function');
    });

    it('should accept title and optional description', () => {
      expect(() => showErrorToast('Error')).not.toThrow();
      expect(() => showErrorToast('Error', 'Description')).not.toThrow();
    });
  });

  describe('showSuccessToast', () => {
    it('should be a function', () => {
      expect(typeof showSuccessToast).toBe('function');
    });

    it('should accept title and optional description', () => {
      expect(() => showSuccessToast('Success')).not.toThrow();
      expect(() => showSuccessToast('Success', 'Description')).not.toThrow();
    });
  });

  describe('showValidationErrorToast', () => {
    it('should be a function', () => {
      expect(typeof showValidationErrorToast).toBe('function');
    });

    it('should accept array of error messages', () => {
      expect(() => showValidationErrorToast(['Error 1', 'Error 2'])).not.toThrow();
    });
  });

  describe('showNetworkErrorToast', () => {
    it('should be a function', () => {
      expect(typeof showNetworkErrorToast).toBe('function');
    });

    it('should not require parameters', () => {
      expect(() => showNetworkErrorToast()).not.toThrow();
    });
  });
});
