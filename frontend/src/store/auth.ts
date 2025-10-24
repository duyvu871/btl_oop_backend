import { atom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';

// User interface
export interface User {
  id: string;
  email: string;
  name?: string;
  verified: boolean;
}

// Auth tokens stored in localStorage
export const accessTokenAtom = atomWithStorage<string | null>('access_token', null);
export const refreshTokenAtom = atomWithStorage<string | null>('refresh_token', null);

// Current user state
export const userAtom = atom<User | null>(null);

// Auth state (derived from tokens)
export const isAuthenticatedAtom = atom(
  (get) => {
    const accessToken = get(accessTokenAtom);
    return !!accessToken;
  }
);

// Logout action
export const logoutAtom = atom(
  null,
  (_get, set) => {
    set(accessTokenAtom, null);
    set(refreshTokenAtom, null);
    set(userAtom, null);
  }
);

