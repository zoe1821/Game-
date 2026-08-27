import React from 'react';
import { ActivityIndicator, Pressable, type StyleProp, View, type ViewStyle } from 'react-native';

import { useTheme } from '@/design/theme';

import { Text } from './Text';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'destructive';

export interface ButtonProps {
  label: string;
  onPress: () => void;
  variant?: ButtonVariant;
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  style?: StyleProp<ViewStyle>;
  /** Se lee antes que la etiqueta cuando hace falta más contexto (A18). */
  accessibilityHint?: string;
}

export function Button({
  label,
  onPress,
  variant = 'primary',
  disabled = false,
  loading = false,
  fullWidth = true,
  style,
  accessibilityHint,
}: ButtonProps): React.ReactElement {
  const theme = useTheme();
  const isInactive = disabled || loading;

  const background: Record<ButtonVariant, string> = {
    primary: theme.colors.accent,
    secondary: theme.colors.surfaceSunken,
    ghost: 'transparent',
    destructive: theme.colors.alert,
  };
  const foreground: Record<ButtonVariant, string> = {
    primary: theme.colors.accentInk,
    secondary: theme.colors.ink,
    ghost: theme.colors.accent,
    destructive: theme.colors.alertInk,
  };

  return (
    <Pressable
      onPress={onPress}
      disabled={isInactive}
      accessibilityRole="button"
      accessibilityState={{ disabled: isInactive, busy: loading }}
      accessibilityHint={accessibilityHint}
      style={({ pressed }) => [
        {
          minHeight: theme.touchTarget.comfortable,
          paddingHorizontal: theme.spacing.lg,
          paddingVertical: theme.spacing.md,
          borderRadius: theme.radius.lg,
          backgroundColor: background[variant],
          borderWidth: variant === 'ghost' ? 0 : 1,
          borderColor: variant === 'secondary' ? theme.colors.line : 'transparent',
          alignItems: 'center',
          justifyContent: 'center',
          alignSelf: fullWidth ? 'stretch' : 'flex-start',
          opacity: isInactive ? 0.5 : pressed ? 0.85 : 1,
        },
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={foreground[variant]} />
      ) : (
        <View>
          <Text variant="bodyStrong" style={{ color: foreground[variant] }}>
            {label}
          </Text>
        </View>
      )}
    </Pressable>
  );
}
