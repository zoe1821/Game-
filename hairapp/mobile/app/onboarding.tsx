import { useRouter } from 'expo-router';
import { useMutation } from '@tanstack/react-query';
import React, { useState } from 'react';
import { Pressable, View } from 'react-native';

import { useApi } from '@/api/provider';
import { ApiError } from '@/api/client';
import { Button } from '@/components/Button';
import { Screen } from '@/components/Screen';
import { Stack } from '@/components/Stack';
import { ErrorState } from '@/components/StateViews';
import { Text } from '@/components/Text';
import { useTheme } from '@/design/theme';
import { t } from '@/i18n';
import { useOnboardingStore } from '@/state/auth';

const PATTERNS = ['1b', '2a', '2b', '2c', '3a', '3b', '3c', '4a', '4b', '4c'] as const;
const GOALS = [
  'definition',
  'volume',
  'frizz_control',
  'hydration',
  'damage_recovery',
  'length_retention',
  'scalp_comfort',
] as const;

interface Step {
  key: string;
  question: string;
  hint?: string;
}

/**
 * Onboarding esencial (B3).
 *
 * Cuatro pasos, uno por pantalla. Cada uno tiene que pasar la prueba de los
 * diez segundos: alguien que no sabe nada de cabello entiende qué se le pide y
 * por qué. Todo lo demás es profundización opcional, después.
 */
export default function Onboarding(): React.ReactElement {
  const theme = useTheme();
  const router = useRouter();
  const api = useApi();
  const { draft, setField, reset } = useOnboardingStore();
  const [index, setIndex] = useState(0);

  const steps: Step[] = [
    { key: 'welcome', question: t('onboarding.welcomeTitle'), hint: t('onboarding.welcomeBody') },
    { key: 'pattern', question: t('onboarding.patternQuestion'), hint: t('onboarding.patternHint') },
    { key: 'goal', question: t('onboarding.goalQuestion'), hint: t('onboarding.goalHint') },
    {
      key: 'processed',
      question: t('onboarding.processedQuestion'),
      hint: t('onboarding.processedHint'),
    },
  ];

  const submit = useMutation({
    mutationFn: () =>
      api.profile.essentialOnboarding({
        primary_goal: draft.primary_goal ?? 'definition',
        ...(draft.dominant_pattern ? { dominant_pattern: draft.dominant_pattern } : {}),
        ...(draft.approximate_length_cm ? { approximate_length_cm: draft.approximate_length_cm } : {}),
        ...(draft.wash_frequency_days ? { wash_frequency_days: draft.wash_frequency_days } : {}),
        ...(draft.country ? { country: draft.country } : {}),
        is_chemically_processed: draft.is_chemically_processed ?? false,
      }),
    onSuccess: () => {
      reset();
      router.replace('/(tabs)');
    },
  });

  const step = steps[index];
  if (!step) {
    return <Screen />;
  }

  const canContinue =
    step.key === 'welcome' ||
    (step.key === 'pattern' && draft.dominant_pattern !== undefined) ||
    (step.key === 'goal' && draft.primary_goal !== undefined) ||
    (step.key === 'processed' && draft.is_chemically_processed !== undefined);

  const isLast = index === steps.length - 1;

  return (
    <Screen>
      <Stack gap="xl">
        <Stack gap="xs">
          <Text variant="overline" tone="muted">
            {`${index + 1} ${t('common.of')} ${steps.length}`}
          </Text>
          <View
            accessibilityRole="progressbar"
            accessibilityValue={{ min: 0, max: steps.length, now: index + 1 }}
            style={{
              height: 3,
              backgroundColor: theme.colors.surfaceSunken,
              borderRadius: theme.radius.pill,
            }}
          >
            <View
              style={{
                width: `${((index + 1) / steps.length) * 100}%`,
                height: '100%',
                backgroundColor: theme.colors.accent,
                borderRadius: theme.radius.pill,
              }}
            />
          </View>
        </Stack>

        <Stack gap="sm">
          <Text variant="title" tone="strong" accessibilityRole="header">
            {step.question}
          </Text>
          {step.hint ? (
            <Text variant="callout" tone="muted">
              {step.hint}
            </Text>
          ) : null}
        </Stack>

        {step.key === 'pattern' ? (
          <ChoiceGrid
            options={PATTERNS.map((p) => ({ value: p, label: p.toUpperCase() }))}
            selected={draft.dominant_pattern}
            onSelect={(value) => setField('dominant_pattern', value)}
          />
        ) : null}

        {step.key === 'goal' ? (
          <ChoiceGrid
            options={GOALS.map((g) => ({ value: g, label: t(`goal.${g}`) }))}
            selected={draft.primary_goal}
            onSelect={(value) => setField('primary_goal', value)}
          />
        ) : null}

        {step.key === 'processed' ? (
          <ChoiceGrid
            options={[
              { value: 'yes', label: t('common.done') },
              { value: 'no', label: t('common.notNow') },
            ]}
            selected={
              draft.is_chemically_processed === undefined
                ? undefined
                : draft.is_chemically_processed
                  ? 'yes'
                  : 'no'
            }
            onSelect={(value) => setField('is_chemically_processed', value === 'yes')}
          />
        ) : null}

        {submit.isError ? (
          <ErrorState
            message={
              submit.error instanceof ApiError ? submit.error.message : t('error.generic')
            }
            onRetry={() => submit.mutate()}
          />
        ) : null}

        <Stack gap="sm">
          <Button
            label={isLast ? t('common.done') : t('common.continue')}
            disabled={!canContinue}
            loading={submit.isPending}
            onPress={() => {
              if (isLast) {
                submit.mutate();
              } else {
                setIndex((current) => current + 1);
              }
            }}
          />
          {index > 0 ? (
            <Button
              label={t('common.back')}
              variant="ghost"
              onPress={() => setIndex((current) => current - 1)}
            />
          ) : null}
        </Stack>
      </Stack>
    </Screen>
  );
}

interface ChoiceGridProps {
  options: Array<{ value: string; label: string }>;
  selected: string | undefined;
  onSelect: (value: string) => void;
}

function ChoiceGrid({ options, selected, onSelect }: ChoiceGridProps): React.ReactElement {
  const theme = useTheme();
  return (
    <Stack direction="row" gap="sm" wrap>
      {options.map((option) => {
        const isSelected = selected === option.value;
        return (
          <Pressable
            key={option.value}
            onPress={() => onSelect(option.value)}
            accessibilityRole="radio"
            accessibilityState={{ selected: isSelected }}
            style={{
              minHeight: theme.touchTarget.comfortable,
              paddingHorizontal: theme.spacing.lg,
              paddingVertical: theme.spacing.md,
              borderRadius: theme.radius.md,
              borderWidth: 1,
              borderColor: isSelected ? theme.colors.accent : theme.colors.line,
              backgroundColor: isSelected ? theme.colors.accentSoft : theme.colors.surface,
              justifyContent: 'center',
            }}
          >
            <Text variant="callout" tone={isSelected ? 'strong' : 'default'}>
              {option.label}
            </Text>
          </Pressable>
        );
      })}
    </Stack>
  );
}
