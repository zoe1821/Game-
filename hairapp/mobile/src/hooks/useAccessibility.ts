import { useEffect, useState } from 'react';
import { AccessibilityInfo } from 'react-native';

/**
 * Preferencias de accesibilidad del sistema (A18).
 *
 * Se leen del dispositivo, no se ofrecen como ajustes propios: alguien que ya
 * ha configurado "reducir movimiento" en su móvil no debería tener que
 * configurarlo otra vez en cada app.
 */
export interface AccessibilityPreferences {
  /** El sistema pide reducir animaciones. */
  reduceMotion: boolean;
  /** Hay un lector de pantalla activo. */
  screenReader: boolean;
  /** El sistema pide más contraste. */
  boldText: boolean;
}

export function useAccessibilityPreferences(): AccessibilityPreferences {
  const [preferences, setPreferences] = useState<AccessibilityPreferences>({
    reduceMotion: false,
    screenReader: false,
    boldText: false,
  });

  useEffect(() => {
    let active = true;

    async function read(): Promise<void> {
      const [reduceMotion, screenReader, boldText] = await Promise.all([
        AccessibilityInfo.isReduceMotionEnabled(),
        AccessibilityInfo.isScreenReaderEnabled(),
        AccessibilityInfo.isBoldTextEnabled?.() ?? Promise.resolve(false),
      ]);
      if (active) {
        setPreferences({ reduceMotion, screenReader, boldText });
      }
    }
    void read();

    const subscriptions = [
      AccessibilityInfo.addEventListener('reduceMotionChanged', (reduceMotion) =>
        setPreferences((current) => ({ ...current, reduceMotion })),
      ),
      AccessibilityInfo.addEventListener('screenReaderChanged', (screenReader) =>
        setPreferences((current) => ({ ...current, screenReader })),
      ),
    ];

    return () => {
      active = false;
      subscriptions.forEach((subscription) => subscription.remove());
    };
  }, []);

  return preferences;
}

/**
 * Duración de animación que respeta la preferencia del sistema.
 *
 * Devuelve 0 cuando se pide reducir movimiento: una animación de 200 ms no es
 * "poco movimiento", es movimiento.
 */
export function useAnimationDuration(base: number): number {
  const { reduceMotion } = useAccessibilityPreferences();
  return reduceMotion ? 0 : base;
}
