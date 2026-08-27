import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import React from 'react';
import { View } from 'react-native';

import { ApiError } from '@/api/client';
import { useApi } from '@/api/provider';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Screen } from '@/components/Screen';
import { Stack } from '@/components/Stack';
import { EmptyState, ErrorState, LoadingState } from '@/components/StateViews';
import { Text } from '@/components/Text';
import { WhyThis } from '@/components/WhyThis';
import { useTheme } from '@/design/theme';
import { t, tKey } from '@/i18n';

/**
 * Inicio.
 *
 * Cuando todavía no hay historial, esta pantalla es sobre todo el arranque en
 * frío (B2): dice honestamente que aún no conoce a la persona y ofrece hitos
 * concretos, en vez de inventar una personalización que no existe.
 */
export default function Today(): React.ReactElement {
  const theme = useTheme();
  const router = useRouter();
  const api = useApi();

  const profile = useQuery({ queryKey: ['profile'], queryFn: () => api.profile.read() });
  const coldStart = useQuery({ queryKey: ['cold-start'], queryFn: () => api.journal.coldStart() });

  if (profile.isLoading) {
    return (
      <Screen>
        <LoadingState />
      </Screen>
    );
  }

  if (profile.isError) {
    const error = profile.error;
    if (error instanceof ApiError && error.status === 404) {
      return (
        <Screen>
          <EmptyState
            title={t('onboarding.welcomeTitle')}
            body={t('onboarding.welcomeBody')}
            actionLabel={t('common.continue')}
            onAction={() => router.push('/onboarding')}
          />
        </Screen>
      );
    }
    return (
      <Screen>
        <ErrorState
          message={error instanceof Error ? error.message : t('error.generic')}
          onRetry={() => void profile.refetch()}
        />
      </Screen>
    );
  }

  const data = profile.data;
  const percent = Math.round((data?.completeness ?? 0) * 100);

  return (
    <Screen>
      <Stack gap="xl">
        <Stack gap="sm">
          <Text variant="title" tone="strong" accessibilityRole="header">
            {t('home.todayTitle')}
          </Text>
          <ProfileProgress percent={percent} />
        </Stack>

        {coldStart.data ? (
          <Card>
            <Stack gap="md">
              <Text variant="overline" tone="muted">
                {t(`coldStart.stage.${coldStart.data.stage}`)}
              </Text>
              <Text variant="subheading">{tKey(coldStart.data.message_key)}</Text>

              {coldStart.data.based_on_reference_profiles ? (
                <Text variant="caption" tone="warn">
                  {t('coldStart.referenceHint', {
                    count: coldStart.data.reference_sample_size,
                  })}
                </Text>
              ) : null}

              {/* Los hitos son metas útiles, no una racha que castiga fallar (B7). */}
              <Stack gap="sm">
                {coldStart.data.milestone_keys.map((key) => (
                  <View
                    key={key}
                    style={{
                      flexDirection: 'row',
                      gap: theme.spacing.sm,
                      alignItems: 'flex-start',
                    }}
                  >
                    <Text variant="callout" tone="accent">
                      ·
                    </Text>
                    <Text variant="callout" style={{ flex: 1 }}>
                      {tKey(key)}
                    </Text>
                  </View>
                ))}
              </Stack>

              <WhyThis explanation={coldStart.data.explanation} />
            </Stack>
          </Card>
        ) : null}

        <Stack gap="sm">
          <Button label={t('routine.generate')} onPress={() => router.push('/(tabs)/routine')} />
          <Button
            label={t('home.startScan')}
            variant="secondary"
            onPress={() => router.push('/(tabs)/map')}
          />
        </Stack>
      </Stack>
    </Screen>
  );
}

function ProfileProgress({ percent }: { percent: number }): React.ReactElement {
  const theme = useTheme();
  return (
    <Stack gap="xs">
      <View
        accessibilityRole="progressbar"
        accessibilityLabel={t('home.profileCompleteness', { percent })}
        accessibilityValue={{ min: 0, max: 100, now: percent }}
        style={{
          height: 4,
          backgroundColor: theme.colors.surfaceSunken,
          borderRadius: theme.radius.pill,
        }}
      >
        <View
          style={{
            width: `${percent}%`,
            height: '100%',
            backgroundColor: theme.colors.accent,
            borderRadius: theme.radius.pill,
          }}
        />
      </View>
      <Text variant="caption" tone="muted">
        {t('home.profileCompleteness', { percent })}
      </Text>
      {/* Indicador sin presión: se dice explícitamente que nada se bloquea (B3). */}
      <Text variant="caption" tone="faint">
        {t('home.profileCompletenessHint')}
      </Text>
    </Stack>
  );
}
