import React from 'react';
import { ActivityIndicator, View } from 'react-native';

import { useTheme } from '@/design/theme';
import { t } from '@/i18n';

import { Button } from './Button';
import { Card } from './Card';
import { Stack } from './Stack';
import { Text } from './Text';

export function LoadingState({ label }: { label?: string }): React.ReactElement {
  const theme = useTheme();
  return (
    <View
      accessibilityRole="progressbar"
      accessibilityLabel={label ?? t('common.loading')}
      style={{ paddingVertical: theme.spacing.xxl, alignItems: 'center', gap: theme.spacing.md }}
    >
      <ActivityIndicator color={theme.colors.accent} />
      <Text variant="caption" tone="muted">
        {label ?? t('common.loading')}
      </Text>
    </View>
  );
}

export interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps): React.ReactElement {
  return (
    <Card tone="alert">
      <Stack gap="md">
        <Text variant="body">{message}</Text>
        {onRetry ? <Button label={t('common.retry')} onPress={onRetry} variant="secondary" /> : null}
      </Stack>
    </Card>
  );
}

export interface EmptyStateProps {
  title: string;
  body?: string;
  actionLabel?: string;
  onAction?: () => void;
}

/**
 * Estado vacío.
 *
 * Nunca es un mensaje de error disfrazado: «todavía no hay datos» es una
 * situación normal y frecuente en este producto (B2), así que el estado vacío
 * explica qué hacer a continuación en vez de disculparse.
 */
export function EmptyState({ title, body, actionLabel, onAction }: EmptyStateProps): React.ReactElement {
  return (
    <Card tone="sunken">
      <Stack gap="md">
        <Text variant="subheading">{title}</Text>
        {body ? (
          <Text variant="callout" tone="muted">
            {body}
          </Text>
        ) : null}
        {actionLabel && onAction ? (
          <Button label={actionLabel} onPress={onAction} variant="secondary" />
        ) : null}
      </Stack>
    </Card>
  );
}
