import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import React from 'react';
import { Switch, View } from 'react-native';

import { useApi } from '@/api/provider';
import type { Consent, ConsentPurpose } from '@/api/types';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Screen } from '@/components/Screen';
import { Stack } from '@/components/Stack';
import { ErrorState, LoadingState } from '@/components/StateViews';
import { Text } from '@/components/Text';
import { useTheme } from '@/design/theme';
import { t } from '@/i18n';
import { secureTokenStore, useAuthStore } from '@/state/auth';

/** Los que se pueden cambiar. Términos y privacidad no: sin ellos no hay app. */
const TOGGLEABLE: ConsentPurpose[] = [
  'photo_processing',
  'model_training',
  'stylist_sharing',
  'anonymous_aggregate',
];

/**
 * Privacidad y consentimientos (A22, B6 §3.2).
 *
 * Cada propósito es un interruptor independiente y revocar cuesta lo mismo que
 * conceder — un solo toque. El de entrenamiento de modelos lleva escrito al
 * lado que dejarlo apagado no quita ninguna función, porque es cierto y porque
 * es justo lo que la gente sospecha que no lo es.
 */
export default function Privacy(): React.ReactElement {
  const api = useApi();
  const router = useRouter();
  const queryClient = useQueryClient();
  const setSignedOut = useAuthStore((state) => state.setSignedOut);

  const me = useQuery({ queryKey: ['me'], queryFn: () => api.auth.me() });

  const update = useMutation({
    mutationFn: (payload: { purpose: ConsentPurpose; granted: boolean }) =>
      api.auth.setConsents([payload]),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['me'] }),
  });

  const deleteAccount = useMutation({
    mutationFn: () => api.auth.deleteAccount(),
    onSuccess: async () => {
      await secureTokenStore.clear();
      setSignedOut();
      queryClient.clear();
      router.replace('/');
    },
  });

  if (me.isLoading) {
    return (
      <Screen>
        <LoadingState />
      </Screen>
    );
  }
  if (me.isError) {
    return (
      <Screen>
        <ErrorState
          message={me.error instanceof Error ? me.error.message : t('error.generic')}
          onRetry={() => void me.refetch()}
        />
      </Screen>
    );
  }

  const consents = new Map((me.data?.consents ?? []).map((c: Consent) => [c.purpose, c]));

  return (
    <Screen>
      <Stack gap="lg">
        <Text variant="title" tone="strong" accessibilityRole="header">
          {t('privacy.title')}
        </Text>

        <Card>
          <Stack gap="sm">
            <Text variant="subheading">{t('privacy.photosTitle')}</Text>
            <Text variant="callout" tone="muted">
              {t('privacy.photosBody')}
            </Text>
          </Stack>
        </Card>

        <Stack gap="sm">
          {TOGGLEABLE.map((purpose) => (
            <ConsentToggle
              key={purpose}
              purpose={purpose}
              granted={consents.get(purpose)?.granted ?? false}
              onChange={(granted) => update.mutate({ purpose, granted })}
            />
          ))}
        </Stack>

        <Card tone="alert">
          <Stack gap="md">
            <Text variant="subheading" tone="alert">
              {t('privacy.deleteAccount')}
            </Text>
            {/* Se dice lo que se borra de verdad, incluidas las fotos del
                almacenamiento, no solo las filas. */}
            <Text variant="callout" tone="muted">
              {t('privacy.deleteAccountBody')}
            </Text>
            <Button
              label={t('privacy.deleteAccount')}
              variant="destructive"
              loading={deleteAccount.isPending}
              onPress={() => deleteAccount.mutate()}
            />
          </Stack>
        </Card>
      </Stack>
    </Screen>
  );
}

function ConsentToggle({
  purpose,
  granted,
  onChange,
}: {
  purpose: ConsentPurpose;
  granted: boolean;
  onChange: (granted: boolean) => void;
}): React.ReactElement {
  const theme = useTheme();
  return (
    <Card tone="sunken">
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: theme.spacing.lg }}>
        <View style={{ flex: 1, gap: theme.spacing.xxs }}>
          <Text variant="callout">{t(`privacy.consent.${purpose}`)}</Text>
          {purpose === 'model_training' && !granted ? (
            <Text variant="caption" tone="faint">
              {t('privacy.modelTrainingHint')}
            </Text>
          ) : null}
        </View>
        <Switch
          value={granted}
          onValueChange={onChange}
          accessibilityLabel={t(`privacy.consent.${purpose}`)}
          trackColor={{ false: theme.colors.line, true: theme.colors.accentSoft }}
          thumbColor={granted ? theme.colors.accent : theme.colors.surface}
        />
      </View>
    </Card>
  );
}
