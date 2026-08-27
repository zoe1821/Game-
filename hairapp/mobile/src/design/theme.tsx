import React, { createContext, useContext, useMemo } from 'react';
import { useColorScheme } from 'react-native';

import {
  darkColors,
  durations,
  lightColors,
  radius,
  spacing,
  touchTarget,
  typography,
  type ThemeColors,
} from './tokens';

export interface Theme {
  colors: ThemeColors;
  spacing: typeof spacing;
  radius: typeof radius;
  typography: typeof typography;
  touchTarget: typeof touchTarget;
  durations: typeof durations;
  scheme: 'light' | 'dark';
}

const ThemeContext = createContext<Theme | null>(null);

export interface ThemeProviderProps {
  children: React.ReactNode;
  /** Fuerza un esquema. Sin esto sigue al sistema, que es lo correcto por defecto. */
  forcedScheme?: 'light' | 'dark';
}

export function ThemeProvider({ children, forcedScheme }: ThemeProviderProps): React.ReactElement {
  const systemScheme = useColorScheme();
  const scheme = forcedScheme ?? (systemScheme === 'dark' ? 'dark' : 'light');

  const value = useMemo<Theme>(
    () => ({
      colors: scheme === 'dark' ? darkColors : lightColors,
      spacing,
      radius,
      typography,
      touchTarget,
      durations,
      scheme,
    }),
    [scheme],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): Theme {
  const theme = useContext(ThemeContext);
  if (theme === null) {
    throw new Error('useTheme debe usarse dentro de un ThemeProvider');
  }
  return theme;
}
