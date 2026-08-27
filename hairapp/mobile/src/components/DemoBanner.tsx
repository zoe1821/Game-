import React from 'react';
import { View } from 'react-native';

import { useTheme } from '@/design/theme';
import { isDemoMode } from '@/demo';
import { t } from '@/i18n';

import { Text } from './Text';

/**
 * Aviso de modo demostración.
 *
 * Está a propósito siempre visible y no se puede cerrar. La app no puede
 * aparentar que guardó algo que no guardó: eso sería exactamente el tipo de
 * mentira pequeña que el resto del producto existe para no cometer.
 */
export function DemoBanner(): React.ReactElement | null {
  const theme = useTheme();
  if (!isDemoMode()) {
    return null;
  }
  return (
    <View
      accessibilityRole="alert"
      style={{
        backgroundColor: theme.colors.warnSoft,
        paddingHorizontal: theme.spacing.lg,
        paddingVertical: theme.spacing.sm,
        borderBottomWidth: 1,
        borderBottomColor: theme.colors.warn,
      }}
    >
      <Text variant="caption" style={{ color: theme.colors.warn }}>
        {t('demo.banner')}
      </Text>
    </View>
  );
}
