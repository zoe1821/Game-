import { useRouter } from 'expo-router';
import React from 'react';
import { View } from 'react-native';

import { Button } from '@/components/Button';
import { Screen } from '@/components/Screen';
import { Stack } from '@/components/Stack';
import { Text } from '@/components/Text';
import { t } from '@/i18n';

/**
 * Pantalla de entrada.
 *
 * El primer texto que ve alguien no puede sonar a «descubre tu tipo de rizo»
 * (docs/03-POSITIONING.md §5). Dice de entrada las dos cosas que separan a
 * este producto del resto: el análisis por zonas y que no vamos a empujar
 * compras.
 */
/** El nombre de marca no se traduce: es el mismo en todos los idiomas. */
const BRAND = 'TRICHON';

export default function Landing(): React.ReactElement {
  const router = useRouter();

  return (
    <Screen scroll={false} style={{ justifyContent: 'space-between' }}>
      <View style={{ flex: 1, justifyContent: 'center' }}>
        <Stack gap="lg">
          <Text variant="overline" tone="accent">
            {BRAND}
          </Text>
          <Text variant="display" tone="strong" accessibilityRole="header">
            {t('home.heroTitle')}
          </Text>
          <Text variant="body" tone="muted">
            {t('home.heroBody')}
          </Text>
        </Stack>
      </View>

      <Stack gap="md">
        <Button label={t('home.startScan')} onPress={() => router.push('/onboarding')} />
        <Text variant="caption" tone="faint" style={{ textAlign: 'center' }}>
          {t('safety.cosmeticOnly')}
        </Text>
      </Stack>
    </Screen>
  );
}
