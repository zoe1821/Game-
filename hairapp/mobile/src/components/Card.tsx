import React from 'react';
import { View, type StyleProp, type ViewStyle } from 'react-native';

import { useTheme } from '@/design/theme';

export interface CardProps {
  children: React.ReactNode;
  tone?: 'default' | 'sunken' | 'accent' | 'warn' | 'alert';
  style?: StyleProp<ViewStyle>;
  accessibilityLabel?: string;
}

/**
 * Superficie base. Usa borde fino en vez de sombra: la sombra difusa es lo que
 * hace que una interfaz parezca un panel de control, y la estética objetivo es
 * editorial (A19).
 */
export function Card({ children, tone = 'default', style, accessibilityLabel }: CardProps): React.ReactElement {
  const theme = useTheme();

  const backgrounds = {
    default: theme.colors.surface,
    sunken: theme.colors.surfaceSunken,
    accent: theme.colors.surface,
    warn: theme.colors.surface,
    alert: theme.colors.surface,
  } as const;

  const borders = {
    default: theme.colors.line,
    sunken: theme.colors.line,
    accent: theme.colors.accent,
    warn: theme.colors.warn,
    alert: theme.colors.alert,
  } as const;

  return (
    <View
      accessible={accessibilityLabel !== undefined}
      accessibilityLabel={accessibilityLabel}
      style={[
        {
          backgroundColor: backgrounds[tone],
          borderColor: borders[tone],
          borderWidth: 1,
          borderRadius: theme.radius.lg,
          padding: theme.spacing.lg,
        },
        style,
      ]}
    >
      {children}
    </View>
  );
}
