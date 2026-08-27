import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import React from 'react';
import { View } from 'react-native';

import { useApi } from '@/api/provider';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Screen } from '@/components/Screen';
import { Stack } from '@/components/Stack';
import { ErrorState, LoadingState } from '@/components/StateViews';
import { Text } from '@/components/Text';
import { useTheme } from '@/design/theme';
import { t, tKey } from '@/i18n';

interface FeatureState {
  feature: string;
  allowed: boolean;
  reason: string;
  used: number;
  limit: number | null;
  remaining: number | null;
  message_key: string;
}

interface Entitlements {
  plan: string;
  plan_label_key: string;
  renews: boolean;
  period_start: string;
  period_end: string;
  features: FeatureState[];
  always_included: Array<{ feature: string; label_key: string }>;
}

/**
 * Pantalla de plan y suscripción.
 *
 * Decisiones deliberadas, todas derivadas de docs/02-MONETIZATION.md §2:
 *
 *  - Lo que **nunca** se limita va arriba y con nombre propio, no escondido en
 *    letra pequeña. Es la afirmación que más desconfianza genera en este tipo
 *    de producto, así que es la que hay que poder comprobar de un vistazo.
 *  - El cupo se enseña como "te quedan 2 de 3", no como una barra que se pone
 *    roja. No hay urgencia artificial ni miedo como palanca.
 *  - No se menciona ningún riesgo para el cabello en ninguna parte del muro.
 */
export default function PlanScreen(): React.ReactElement {
  const api = useApi();
  const queryClient = useQueryClient();

  const entitlements = useQuery({
    queryKey: ['entitlements'],
    queryFn: () =>
      api.billing.entitlements() as Promise<Entitlements>,
  });

  const cancel = useMutation({
    mutationFn: () => api.billing.cancel(),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['entitlements'] }),
  });

  if (entitlements.isLoading) {
    return (
      <Screen>
        <LoadingState />
      </Screen>
    );
  }
  if (entitlements.isError) {
    return (
      <Screen>
        <ErrorState
          message={
            entitlements.error instanceof Error ? entitlements.error.message : t('error.generic')
          }
          onRetry={() => void entitlements.refetch()}
        />
      </Screen>
    );
  }

  const data = entitlements.data;
  if (!data) {
    return <Screen />;
  }
  const isPaid = data.plan !== 'free';

  return (
    <Screen>
      <Stack gap="xl">
        <Stack gap="xs">
          <Text variant="overline" tone="muted">
            {t('plan.currentPlan')}
          </Text>
          <Text variant="title" tone="strong" accessibilityRole="header">
            {tKey(data.plan_label_key)}
          </Text>
          {isPaid ? (
            <Text variant="caption" tone="muted">
              {data.renews
                ? t('plan.renews', { date: data.period_end })
                : t('plan.notRenewing')}
            </Text>
          ) : null}
        </Stack>

        {/* La promesa que más importa dejar comprobable, arriba del todo. */}
        <Card tone="accent">
          <Stack gap="sm">
            <Text variant="subheading" tone="accent">
              {t('plan.alwaysIncludedTitle')}
            </Text>
            <Text variant="callout" tone="muted">
              {t('plan.alwaysIncludedBody')}
            </Text>
            <Stack gap="xxs">
              {data.always_included.map((item) => (
                <Text key={item.feature} variant="caption">
                  · {tKey(item.label_key)}
                </Text>
              ))}
            </Stack>
          </Stack>
        </Card>

        <Stack gap="sm">
          <Text variant="subheading">{t('plan.whatYouGet')}</Text>
          {data.features.map((feature) => (
            <FeatureRow key={feature.feature} feature={feature} />
          ))}
          <Text variant="caption" tone="faint">
            {t('plan.periodResets', { date: data.period_end })}
          </Text>
        </Stack>

        {isPaid && data.renews ? (
          <Button label={t('plan.cancel')} variant="ghost" onPress={() => cancel.mutate()} />
        ) : null}
      </Stack>
    </Screen>
  );
}

function FeatureRow({ feature }: { feature: FeatureState }): React.ReactElement {
  const theme = useTheme();

  const detail = (): string => {
    if (feature.limit === null) {
      return t('plan.unlimited');
    }
    if (feature.limit === 0) {
      return t('plan.notIncluded');
    }
    return t('plan.remaining', { count: feature.remaining ?? 0, limit: feature.limit });
  };

  return (
    <View
      style={{
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: theme.spacing.md,
        paddingVertical: theme.spacing.sm,
        borderBottomWidth: 1,
        borderBottomColor: theme.colors.line,
      }}
    >
      <Text variant="callout" style={{ flex: 1 }}>
        {t(`feature.${feature.feature}`)}
      </Text>
      <Text
        variant="caption"
        tone={feature.limit === 0 ? 'faint' : feature.allowed ? 'accent' : 'warn'}
      >
        {detail()}
      </Text>
    </View>
  );
}

export { type Entitlements };
