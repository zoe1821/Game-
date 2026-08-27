import React from 'react';
import { Text as RNText, type StyleProp, type TextStyle } from 'react-native';

import { useTheme } from '@/design/theme';
import type { TypographyToken } from '@/design/tokens';

export type TextTone = 'default' | 'strong' | 'muted' | 'faint' | 'accent' | 'warn' | 'alert';

export interface TextProps {
  children: React.ReactNode;
  variant?: TypographyToken;
  tone?: TextTone;
  style?: StyleProp<TextStyle>;
  numberOfLines?: number;
  /** Etiqueta para lector de pantalla cuando el texto visible no basta (A18). */
  accessibilityLabel?: string;
  accessibilityRole?: 'header' | 'text' | 'summary';
}

/**
 * Todo el texto de la app pasa por aquí.
 *
 * Motivo: es el único sitio donde se aplica la escala tipográfica y el tono de
 * color, así que no puede aparecer un `fontSize: 15` suelto en una pantalla.
 * Además respeta el escalado de tamaño del sistema, que es la primera cosa que
 * rompe la accesibilidad cuando se hace a mano.
 */
export function Text({
  children,
  variant = 'body',
  tone = 'default',
  style,
  numberOfLines,
  accessibilityLabel,
  accessibilityRole,
}: TextProps): React.ReactElement {
  const theme = useTheme();
  const typography = theme.typography[variant];

  const colorByTone: Record<TextTone, string> = {
    default: theme.colors.ink,
    strong: theme.colors.inkStrong,
    muted: theme.colors.inkMuted,
    faint: theme.colors.inkFaint,
    accent: theme.colors.accent,
    warn: theme.colors.warn,
    alert: theme.colors.alert,
  };

  return (
    <RNText
      style={[
        {
          fontSize: typography.fontSize,
          lineHeight: typography.lineHeight,
          letterSpacing: typography.letterSpacing,
          fontWeight: typography.fontWeight as TextStyle['fontWeight'],
          color: colorByTone[tone],
        },
        style,
      ]}
      numberOfLines={numberOfLines}
      accessibilityLabel={accessibilityLabel}
      accessibilityRole={accessibilityRole}
      // Se permite el escalado del sistema, con un tope para que un ajuste
      // extremo no rompa el layout por completo.
      maxFontSizeMultiplier={2}
    >
      {children}
    </RNText>
  );
}
