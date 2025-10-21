import { Amplify } from 'aws-amplify';

interface InitializationState {
  isInitialized: boolean;
  isInitializing: boolean;
  hasError: boolean;
  error: string | null;
  timestamp: number;
}

class InitGuard {
  private state: InitializationState = {
    isInitialized: false,
    isInitializing: false,
    hasError: false,
    error: null,
    timestamp: 0,
  };

  private initPromise: Promise<void> | null = null;
  private listeners: Set<(state: InitializationState) => void> = new Set();
  private initTimeout = 5000;

  async initialize(): Promise<void> {
    if (this.state.isInitialized) {
      return;
    }

    if (this.state.isInitializing && this.initPromise) {
      return this.initPromise;
    }

    this.state.isInitializing = true;
    this.notifyListeners();

    this.initPromise = this._performInitialization();
    return this.initPromise;
  }

  private async _performInitialization(): Promise<void> {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      const userPoolId = process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID;
      const clientId = process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID;
      const region = process.env.NEXT_PUBLIC_COGNITO_REGION || 'us-east-1';

      if (!apiUrl) {
        throw new Error('NEXT_PUBLIC_API_URL is not configured');
      }

      if (!userPoolId || !clientId) {
        console.warn('Cognito configuration incomplete - auth features may not work');
      }

      const currentConfig = Amplify.getConfig();

      if (!currentConfig.Auth) {
        Amplify.configure({
          Auth: {
            Cognito: {
              userPoolId: userPoolId || '',
              userPoolClientId: clientId || '',
              identityPoolId: process.env.NEXT_PUBLIC_IDENTITY_POOL_ID || '',
              loginWith: {
                email: true,
              },
              signUpVerificationMethod: 'code',
              userAttributes: {
                email: {
                  required: true,
                },
              },
              allowGuestAccess: false,
              passwordFormat: {
                minLength: 8,
                requireLowercase: true,
                requireUppercase: true,
                requireNumbers: true,
                requireSpecialCharacters: true,
              },
            },
          },
          API: {
            REST: {
              'multi-agent-api': {
                endpoint: apiUrl,
                region: region,
              },
            },
          },
        });
      }

      await this.waitForReady();

      this.state = {
        isInitialized: true,
        isInitializing: false,
        hasError: false,
        error: null,
        timestamp: Date.now(),
      };

      this.notifyListeners();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Initialization failed';

      this.state = {
        isInitialized: false,
        isInitializing: false,
        hasError: true,
        error: errorMessage,
        timestamp: Date.now(),
      };

      this.notifyListeners();
      throw error;
    } finally {
      this.initPromise = null;
    }
  }

  private async waitForReady(): Promise<void> {
    return new Promise((resolve) => {
      setTimeout(resolve, 100);
    });
  }

  isReady(): boolean {
    return this.state.isInitialized && !this.state.hasError;
  }

  canMakeApiCalls(): boolean {
    return this.isReady() && Boolean(process.env.NEXT_PUBLIC_API_URL);
  }

  getState(): InitializationState {
    return { ...this.state };
  }

  subscribe(listener: (state: InitializationState) => void): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private notifyListeners(): void {
    const state = this.getState();
    this.listeners.forEach((listener) => {
      try {
        listener(state);
      } catch (error) {
        console.error('Error in init guard listener:', error);
      }
    });
  }

  reset(): void {
    this.state = {
      isInitialized: false,
      isInitializing: false,
      hasError: false,
      error: null,
      timestamp: 0,
    };
    this.initPromise = null;
    this.notifyListeners();
  }

  getApiUrl(): string {
    return process.env.NEXT_PUBLIC_API_URL || '';
  }

  hasValidConfig(): boolean {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    return Boolean(apiUrl && apiUrl !== 'https://api.example.com/api/v1');
  }

  async ensureReady(options?: { timeout?: number; skipIfInvalid?: boolean }): Promise<boolean> {
    const timeout = options?.timeout || this.initTimeout;
    const skipIfInvalid = options?.skipIfInvalid || false;

    if (!this.hasValidConfig()) {
      if (skipIfInvalid) {
        console.warn('API configuration is invalid - skipping initialization');
        return false;
      }
      throw new Error('Invalid API configuration');
    }

    if (this.isReady()) {
      return true;
    }

    if (this.state.hasError) {
      if (skipIfInvalid) {
        return false;
      }
      throw new Error(this.state.error || 'Initialization error');
    }

    try {
      await Promise.race([
        this.initialize(),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Initialization timeout')), timeout)
        ),
      ]);
      return this.isReady();
    } catch (error) {
      if (skipIfInvalid) {
        console.error('Initialization failed:', error);
        return false;
      }
      throw error;
    }
  }
}

export const initGuard = new InitGuard();

export default initGuard;
