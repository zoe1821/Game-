import React from 'react';
import { View } from 'react-native';

import { useTheme } from '@/design/theme';

import { Text } from './Text';

export interface ConfidenceBarProps {
  label: string;
  value: number;
  tone?: 'evidence' | 'personal';
  /** Cuando el historial contradice la regla, se marca en vez de disimularse. */
  contradicts?: boolean;
}

/**
 * Barra de confianza.
 *
 * No muestra un porcentaje numérico a propósito: «68 % de confianza» sugiere
 * una precisión que estos datos no tienen. Muestra una posición en una escala,
 * que es lo que la cifra significa de verdad.
 */
export function ConfidenceBar({
  label,
  value,
  tone = 'evidence',
  contradicts = false,
}: ConfidenceBarProps): React.ReactElement {
  const theme = useTheme();
  const clamped = Math.max(0, Math.min(1, value));
  const fill = contradicts
    ? theme.colors.warn
    : tone === 'evidence'
      ? theme.colors.accent
      : theme.colors.inkMuted;

  return (
    <View style={{ gap: theme.spacing.xs }}>
      <Text variant="caption" tone="muted">
        {label}
      </Text>
      <View
        accessibilityRole="progressbar"
        accessibilityValue={{ min: 0, max: 100, now: Math.round(clamped * 100) }}
        style={{
          height: 6,
          borderRadius: theme.radius.pill,
          backgroundColor: theme.colors.surfaceSunken,
          borderWidth: 1,
          borderColor: theme.colors.line,
          overflow: 'hidden',
        }}
      >
        <View
          style={{
            width: `${Math.max(clamped * 100, clamped > 0 ? 4 : 0)}%`,
            height: '100%',
            backgroundColor: fill,
          }}
        />
      </View>
    </View>
  );
}
