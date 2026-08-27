import { useMutation } from '@tanstack/react-query';
import React, { useState } from 'react';
import { Pressable, View } from 'react-native';

import { ApiError } from '@/api/client';
import { useApi } from '@/api/provider';
import type { RoutineStep } from '@/api/types';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { ReferralBlock } from '@/components/ReferralBlock';
import { Screen } from '@/components/Screen';
import { Stack } from '@/components/Stack';
import { EmptyState, ErrorState } from '@/components/StateViews';
import { Text } from '@/components/Text';
import { WhyThis } from '@/components/WhyThis';
import { useTheme } from '@/design/theme';
import { t, tKey } from '@/i18n';

const QUICK_MODES = [
  { kind: 'wash_day', labelKey: 'routine.generate' },
  { kind: 'quick_20', labelKey: 'routine.quick20' },
  { kind: 'quick_10', labelKey: 'routine.quick10' },
  { kind: 'quick_5', labelKey: 'routine.quick5' },
] as const;

/**
 * Rutina generada (A8).
 *
 * Cada paso muestra zona, producto, cantidad con referencia visual, técnica y
 * parámetros concretos. Nada de «aplica producto y define».
 */
export default function RoutineScreen(): React.ReactElement {
  const theme = useTheme();
  const api = useApi();
  const [kind, setKind] = useState<string>('wash_day');

  const generate = useMutation({
    mutationFn: (selectedKind: string) => api.routines.generate({ kind: selectedKind }),
  });

  const routine = generate.data;

  return (
    <Screen>
      <Stack gap="lg">
        <Stack gap="xs">
          <Text variant="title" tone="strong" accessibilityRole="header">
            {t('routine.title')}
          </Text>
          {routine && !routine.halted ? (
            <Text variant="callout" tone="muted">
              {t('routine.totalMinutes', { minutes: routine.total_minutes })}
            </Text>
          ) : null}
        </Stack>

        {/* Modos rápidos por tiempo disponible (A14). */}
        <Stack direction="row" gap="sm" wrap>
          {QUICK_MODES.map((mode) => (
            <Pressable
              key={mode.kind}
              onPress={() => {
                setKind(mode.kind);
                generate.mutate(mode.kind);
              }}
              accessibilityRole="button"
              accessibilityState={{ selected: kind === mode.kind }}
              style={{
                minHeight: theme.touchTarget.minimum,
                paddingHorizontal: theme.spacing.lg,
                justifyContent: 'center',
                borderRadius: theme.radius.pill,
                borderWidth: 1,
                borderColor: kind === mode.kind ? theme.colors.accent : theme.colors.line,
                backgroundColor:
                  kind === mode.kind ? theme.colors.accentSoft : theme.colors.surface,
              }}
            >
              <Text variant="caption">{t(mode.labelKey)}</Text>
            </Pressable>
          ))}
        </Stack>

        {generate.isPending ? <Text tone="muted">{t('common.loading')}</Text> : null}

        {generate.isError ? (
          <ErrorState
            message={
              generate.error instanceof ApiError ? generate.error.message : t('error.generic')
            }
            onRetry={() => generate.mutate(kind)}
          />
        ) : null}

        {/* Señal de derivación: se muestra el bloque y nada más (A23). */}
        {routine?.halted ? <ReferralBlock /> : null}

        {routine && !routine.halted && routine.steps.length === 0 ? (
          <EmptyState title={t('routine.noSteps')} />
        ) : null}

        {routine && !routine.halted
          ? routine.steps.map((step) => <StepCard key={step.order} step={step} />)
          : null}

        {routine?.warnings.map((warning) => (
          <Card key={warning.summary_key} tone="warn">
            <Stack gap="sm">
              <Text variant="callout">{tKey(warning.summary_key, warning.params as never)}</Text>
              <WhyThis explanation={warning} />
            </Stack>
          </Card>
        ))}

        {routine?.education.map((entry) => (
          <Card key={entry.summary_key} tone="sunken">
            <Stack gap="sm">
              <Text variant="callout">{tKey(entry.summary_key, entry.params as never)}</Text>
              <WhyThis explanation={entry} />
            </Stack>
          </Card>
        ))}

        {/* Lo omitido por tiempo se dice, nunca se recorta en silencio (A14). */}
        {routine && routine.skipped_reason_keys.length > 0 ? (
          <Card tone="sunken">
            <Stack gap="sm">
              <Text variant="caption" tone="muted">
                {t('routine.skipped')}
              </Text>
              {[...new Set(routine.skipped_reason_keys)].map((key) => (
                <Text key={key} variant="caption" tone="faint">
                  · {tKey(key)}
                </Text>
              ))}
            </Stack>
          </Card>
        ) : null}

        {!routine && !generate.isPending ? (
          <Button label={t('routine.generate')} onPress={() => generate.mutate(kind)} />
        ) : null}
      </Stack>
    </Screen>
  );
}

function StepCard({ step }: { step: RoutineStep }): React.ReactElement {
  const theme = useTheme();
  const zoneLabels = step.zones.map((zone) => t(`zone.${zone}`)).join(', ');

  return (
    <Card>
      <Stack gap="md">
        <View style={{ flexDirection: 'row', gap: theme.spacing.md, alignItems: 'baseline' }}>
          <Text variant="caption" tone="accent">
            {String(step.order).padStart(2, '0')}
          </Text>
          <Text variant="subheading" style={{ flex: 1 }}>
            {t(`routine.stepTitle.${step.action_key.replace('step.', '')}`)}
          </Text>
        </View>

        {/* La zona es parte de la instrucción, no un detalle: es el pilar 1. */}
        <Text variant="caption" tone="muted">
          {t('routine.inZones', { zones: zoneLabels })}
        </Text>

        {step.amount ? (
          <Row
            label={t('routine.amount')}
            value={`${t('amount.times', {
              count: step.amount.reference_multiplier,
              reference: t(step.amount.reference_key),
            })} · ${step.amount.ml.toFixed(1)} ml`}
          />
        ) : null}

        {step.technique_id ? (
          <Row label={t('routine.technique')} value={step.technique_id} />
        ) : null}

        {step.follow_up_technique_ids.length > 0 ? (
          <Row label={t('routine.thenAlso')} value={step.follow_up_technique_ids.join(' → ')} />
        ) : null}

        {Object.entries(step.params).length > 0 ? (
          <Stack gap="xxs">
            {Object.entries(step.params).map(([key, value]) => (
              <Text key={key} variant="caption" tone="faint">
                {key}: {String(value)}
              </Text>
            ))}
          </Stack>
        ) : null}

        <WhyThis explanation={step.explanation} />
      </Stack>
    </Card>
  );
}

function Row({ label, value }: { label: string; value: string }): React.ReactElement {
  return (
    <View style={{ flexDirection: 'row', justifyContent: 'space-between', gap: 12 }}>
      <Text variant="caption" tone="muted">
        {label}
      </Text>
      <Text variant="callout" style={{ flex: 1, textAlign: 'right' }}>
        {value}
      </Text>
    </View>
  );
}
