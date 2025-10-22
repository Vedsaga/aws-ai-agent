import { signIn, signOut, getCurrentUser, fetchAuthSession, SignInInput } from 'aws-amplify/auth';
import Cookies from 'js-cookie';

export interface User {
  userId: string;
  email: string;
  tenantId: string;
}

const TOKEN_COOKIE_NAME = 'auth_token';
const REFRESH_TOKEN_COOKIE_NAME = 'refresh_token';
const USER_COOKIE_NAME = 'user_data';

export async function login(email: string, password: string): Promise<{ success: boolean; error?: string }> {
  try {
    const signInInput: SignInInput = {
      username: email,
      password,
    };
    
    const { isSignedIn } = await signIn(signInInput);
    
    if (isSignedIn) {
      // Get session and store tokens
      const session = await fetchAuthSession();
      const idToken = session.tokens?.idToken?.toString();
      
      if (idToken) {
        // Store tokens in secure cookies
        Cookies.set(TOKEN_COOKIE_NAME, idToken, {
          secure: true,
          sameSite: 'strict',
          expires: 1 / 24, // 1 hour
        });
        
        // Get user info
        const user = await getCurrentUser();
        const payload = session.tokens?.idToken?.payload;
        
        const userData: User = {
          userId: user.userId,
          email: payload?.email as string || email,
          tenantId: payload?.['custom:tenant_id'] as string || '',
        };
        
        Cookies.set(USER_COOKIE_NAME, JSON.stringify(userData), {
          secure: true,
          sameSite: 'strict',
          expires: 1 / 24,
        });
        
        return { success: true };
      }
    }
    
    return { success: false, error: 'Sign in failed' };
  } catch (error) {
    console.error('Login error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Login failed',
    };
  }
}

export async function logout(): Promise<void> {
  try {
    await signOut();
    Cookies.remove(TOKEN_COOKIE_NAME);
    Cookies.remove(REFRESH_TOKEN_COOKIE_NAME);
    Cookies.remove(USER_COOKIE_NAME);
  } catch (error) {
    console.error('Logout error:', error);
    // Clear cookies even if signOut fails
    Cookies.remove(TOKEN_COOKIE_NAME);
    Cookies.remove(REFRESH_TOKEN_COOKIE_NAME);
    Cookies.remove(USER_COOKIE_NAME);
  }
}

export async function refreshAuthToken(): Promise<boolean> {
  try {
    const session = await fetchAuthSession({ forceRefresh: true });
    const idToken = session.tokens?.idToken?.toString();
    
    if (idToken) {
      Cookies.set(TOKEN_COOKIE_NAME, idToken, {
        secure: true,
        sameSite: 'strict',
        expires: 1 / 24,
      });
      return true;
    }
    
    return false;
  } catch (error) {
    console.error('Token refresh error:', error);
    return false;
  }
}

export function getStoredUser(): User | null {
  try {
    const userData = Cookies.get(USER_COOKIE_NAME);
    if (userData) {
      return JSON.parse(userData);
    }
    return null;
  } catch (error) {
    console.error('Error getting stored user:', error);
    return null;
  }
}

export function getStoredToken(): string | null {
  return Cookies.get(TOKEN_COOKIE_NAME) || null;
}

export async function checkAuthStatus(): Promise<boolean> {
  try {
    const user = await getCurrentUser();
    return !!user;
  } catch (error) {
    return false;
  }
}
