import Constants from 'expo-constants';

export { createDemoEndpoints } from './client';

/**
 * Si la app corre sin servidor.
 *
 * Por defecto está **activado**, porque la compilación que se instala desde
 * GitHub no tiene ningún backend al que llamar. Se apaga poniendo
 * `demoMode: false` en `app.json`, o dando una `apiBaseUrl` real.
 */
export function isDemoMode(): boolean {
  const extra = Constants.expoConfig?.extra as Record<string, unknown> | undefined;
  if (typeof extra?.demoMode === 'boolean') {
    return extra.demoMode;
  }
  return true;
}
