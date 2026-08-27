import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import { create } from 'zustand';

import type { TokenStore } from '@/api/client';
import type { Tokens } from '@/api/types';

const ACCESS_KEY = 'trichon.access';
const REFRESH_KEY = 'trichon.refresh';

/**
 * Los tokens van en el almacén seguro del sistema (Keychain / Keystore), no en
 * AsyncStorage. AsyncStorage es texto plano accesible en un dispositivo con
 * root o jailbreak.
 */
export const secureTokenStore: TokenStore = {
  async getAccessToken() {
    return SecureStore.getItemAsync(ACCESS_KEY);
  },
  async getRefreshToken() {
    return SecureStore.getItemAsync(REFRESH_KEY);
  },
  async setTokens(tokens: Tokens) {
    await SecureStore.setItemAsync(ACCESS_KEY, tokens.access_token);
    await SecureStore.setItemAsync(REFRESH_KEY, tokens.refresh_token);
  },
  async clear() {
    await SecureStore.deleteItemAsync(ACCESS_KEY);
    await SecureStore.deleteItemAsync(REFRESH_KEY);
  },
};

interface AuthState {
  status: 'unknown' | 'signed_in' | 'signed_out';
  setSignedIn: () => void;
  setSignedOut: () => void;
  hydrate: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  status: 'unknown',
  setSignedIn: () => set({ status: 'signed_in' }),
  setSignedOut: () => set({ status: 'signed_out' }),
  async hydrate() {
    const token = await secureTokenStore.getAccessToken();
    set({ status: token ? 'signed_in' : 'signed_out' });
  },
}));

const ONBOARDING_KEY = 'trichon.onboarding.draft';

/**
 * Borrador del onboarding.
 *
 * Se guarda en local mientras se rellena para que salir de la app a mitad no
 * signifique empezar de cero. El onboarding esencial dura menos de tres
 * minutos, pero perderlo igualmente molesta.
 */
export interface OnboardingDraft {
  dominant_pattern?: string;
  approximate_length_cm?: number;
  wash_frequency_days?: number;
  primary_goal?: string;
  country?: string;
  is_chemically_processed?: boolean;
}

interface OnboardingState {
  draft: OnboardingDraft;
  setField: <K extends keyof OnboardingDraft>(key: K, value: OnboardingDraft[K]) => void;
  reset: () => void;
  hydrate: () => Promise<void>;
}

export const useOnboardingStore = create<OnboardingState>((set, get) => ({
  draft: {},
  setField(key, value) {
    const draft = { ...get().draft, [key]: value };
    set({ draft });
    void AsyncStorage.setItem(ONBOARDING_KEY, JSON.stringify(draft));
  },
  reset() {
    set({ draft: {} });
    void AsyncStorage.removeItem(ONBOARDING_KEY);
  },
  async hydrate() {
    const raw = await AsyncStorage.getItem(ONBOARDING_KEY);
    if (raw) {
      try {
        set({ draft: JSON.parse(raw) as OnboardingDraft });
      } catch {
        // Un borrador corrupto no debe impedir usar la app: se descarta.
        await AsyncStorage.removeItem(ONBOARDING_KEY);
      }
    }
  },
}));
