import React from 'react';

import { useTheme } from '@/design/theme';
import { t } from '@/i18n';

import { Card } from './Card';
import { Stack } from './Stack';
import { Text } from './Text';

/**
 * Bloque de derivación (A23, docs/09-CONTROLLED-LANGUAGE.md §3).
 *
 * Se muestra íntegro y **sin ninguna interpretación previa**. No lleva
 * estimaciones al lado, ni recomendaciones, ni un «mientras tanto prueba…»:
 * ese es exactamente el patrón que puede retrasar una consulta que hace falta.
 *
 * El texto es fijo por diseño. No se personaliza ni se acorta.
 */
export function ReferralBlock(): React.ReactElement {
  const theme = useTheme();
  return (
    <Card tone="warn" accessibilityLabel={t('safety.referralBlockTitle')}>
      <Stack gap="md">
        <Text variant="subheading" tone="warn">
          {t('safety.referralBlockTitle')}
        </Text>
        <Text variant="body">{t('safety.referralBlock')}</Text>
        <Text variant="caption" tone="muted" style={{ marginTop: theme.spacing.xs }}>
          {t('safety.cosmeticOnly')}
        </Text>
      </Stack>
    </Card>
  );
}
