import { useQuery } from '@tanstack/react-query';
import React from 'react';
import { View } from 'react-native';

import { useApi } from '@/api/provider';
import type { Explanation } from '@/api/types';
import { Card } from '@/components/Card';
import { Screen } from '@/components/Screen';
import { Stack } from '@/components/Stack';
import { EmptyState, ErrorState, LoadingState } from '@/components/StateViews';
import { Text } from '@/components/Text';
import { WhyThis } from '@/components/WhyThis';
import { useTheme } from '@/design/theme';
import { t, tKey } from '@/i18n';

interface GrowthReading {
  has_reading: boolean;
  measurement_count?: number;
  message_key?: string;
  hint_keys?: string[];
  months?: number;
  observed_gain_cm?: number;
  trimmed_cm?: number;
  growth_cm_per_month?: number;
  growth_is_measured?: boolean;
  total_growth_cm?: number;
  retention_ratio?: number;
  lost_to_breakage_cm?: number;
  is_retention_problem?: boolean;
  explanation?: Explanation;
}

/**
 * Crecimiento y retención (A13).
 *
 * La pantalla existe para hacer una distinción concreta: quien cree que su
 * cabello «no crece» casi siempre tiene un problema de retención. Crece igual
 * que siempre y se rompe por abajo. Decirle lo primero es falso y además
 * desmoraliza; decirle lo segundo le da algo sobre lo que actuar.
 *
 * Y se dice en voz alta cuando el ritmo de crecimiento está **estimado**: la
 * longitud de las puntas no puede distinguir las dos historias por sí sola.
 */
export default function Growth(): React.ReactElement {
  const api = useApi();
  const reading = useQuery({
    queryKey: ['growth'],
    queryFn: () => api.journal.growth() as Promise<GrowthReading>,
  });

  if (reading.isLoading) {
    return (
      <Screen>
        <LoadingState />
      </Screen>
    );
  }
  if (reading.isError) {
    return (
      <Screen>
        <ErrorState
          message={reading.error instanceof Error ? reading.error.message : t('error.generic')}
          onRetry={() => void reading.refetch()}
        />
      </Screen>
    );
  }

  const data = reading.data;

  return (
    <Screen>
      <Stack gap="lg">
        <Stack gap="xs">
          <Text variant="title" tone="strong" accessibilityRole="header">
            {t('growth.title')}
          </Text>
          <Text variant="callout" tone="muted">
            {t('growth.subtitle')}
          </Text>
        </Stack>

        {!data?.has_reading ? (
          <Stack gap="sm">
            <EmptyState title={t('growth.notEnough')} />
            {(data?.hint_keys ?? []).map((key) => (
              <Text key={key} variant="caption" tone="faint">
                · {tKey(key)}
              </Text>
            ))}
          </Stack>
        ) : (
          <Reading data={data} />
        )}
      </Stack>
    </Screen>
  );
}

function Reading({ data }: { data: GrowthReading }): React.ReactElement {
  const theme = useTheme();
  const retention = Math.round((data.retention_ratio ?? 0) * 100);

  return (
    <Stack gap="lg">
      {/* El titular: crecimiento y retención, nunca una sola cifra. */}
      <Card tone={data.is_retention_problem ? 'warn' : 'accent'}>
        <Stack gap="sm">
          <Text variant="subheading" tone={data.is_retention_problem ? 'warn' : 'accent'}>
            {data.is_retention_problem ? t('growth.retentionProblem') : t('growth.healthy')}
          </Text>
          {data.is_retention_problem ? (
            <Text variant="callout" tone="muted">
              {t('growth.retentionProblemBody')}
            </Text>
          ) : null}
        </Stack>
      </Card>

      <Card>
        <Stack gap="md">
          <Row
            label={t('growth.perMonth', { cm: (data.growth_cm_per_month ?? 0).toFixed(2) })}
            value={data.growth_is_measured ? t('growth.measured') : t('growth.assumed')}
            tone={data.growth_is_measured ? 'accent' : 'warn'}
          />

          {/* Si el ritmo está supuesto, se dice y se explica cómo medirlo. */}
          {!data.growth_is_measured ? (
            <Text variant="caption" tone="faint">
              {t('growth.assumedHint')}
            </Text>
          ) : null}

          <View style={{ height: 1, backgroundColor: theme.colors.line }} />

          <Row label={t('growth.grewTotal', { cm: (data.total_growth_cm ?? 0).toFixed(1) })} value="" />
          <Row label={t('growth.kept', { cm: (data.observed_gain_cm ?? 0).toFixed(1) })} value="" />
          {(data.trimmed_cm ?? 0) > 0 ? (
            <Row label={t('growth.trimmed', { cm: (data.trimmed_cm ?? 0).toFixed(1) })} value="" />
          ) : null}
          {(data.lost_to_breakage_cm ?? 0) > 0 ? (
            <Row
              label={t('growth.lost', { cm: (data.lost_to_breakage_cm ?? 0).toFixed(1) })}
              value=""
              tone="warn"
            />
          ) : null}

          <RetentionBar percent={retention} />
        </Stack>
      </Card>

      {data.explanation ? <WhyThis explanation={data.explanation} /> : null}
    </Stack>
  );
}

function Row({
  label,
  value,
  tone = 'default',
}: {
  label: string;
  value: string;
  tone?: 'default' | 'accent' | 'warn';
}): React.ReactElement {
  return (
    <View style={{ flexDirection: 'row', justifyContent: 'space-between', gap: 12 }}>
      <Text variant="callout" tone={tone} style={{ flex: 1 }}>
        {label}
      </Text>
      {value ? (
        <Text variant="caption" tone={tone === 'default' ? 'muted' : tone}>
          {value}
        </Text>
      ) : null}
    </View>
  );
}

function RetentionBar({ percent }: { percent: number }): React.ReactElement {
  const theme = useTheme();
  return (
    <Stack gap="xs">
      <View
        accessibilityRole="progressbar"
        accessibilityLabel={t('growth.retention', { percent })}
        accessibilityValue={{ min: 0, max: 100, now: percent }}
        style={{
          height: 6,
          borderRadius: theme.radius.pill,
          backgroundColor: theme.colors.surfaceSunken,
          overflow: 'hidden',
        }}
      >
        <View
          style={{
            width: `${Math.min(100, Math.max(0, percent))}%`,
            height: '100%',
            backgroundColor: percent < 60 ? theme.colors.warn : theme.colors.accent,
          }}
        />
      </View>
      <Text variant="caption" tone="muted">
        {t('growth.retention', { percent })}
      </Text>
    </Stack>
  );
}
