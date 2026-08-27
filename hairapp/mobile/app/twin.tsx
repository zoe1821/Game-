import { useQuery } from '@tanstack/react-query';
import React, { useState } from 'react';
import { Pressable, View } from 'react-native';

import { useApi } from '@/api/provider';
import type { Projection, Trait } from '@/api/types';
import { Card } from '@/components/Card';
import { Screen } from '@/components/Screen';
import { Stack } from '@/components/Stack';
import { EmptyState, ErrorState, LoadingState } from '@/components/StateViews';
import { Text } from '@/components/Text';
import { WhyThis } from '@/components/WhyThis';
import { useTheme } from '@/design/theme';
import { sampleSizeLabel, t, tKey } from '@/i18n';

const SCENARIOS = [
  'higher_humidity',
  'more_product',
  'less_product',
  'add_protein',
  'stretch_wash_day',
  'refresh_instead_of_wash',
] as const;

/**
 * Hair Digital Twin (A24) — el segundo pilar del producto.
 *
 * Lo que se muestra aquí es lo que hemos **observado**, no una simulación. Un
 * rasgo desconocido se dice desconocido, y una proyección sin base histórica
 * devuelve qué registrar para poder responder, en vez de una cifra inventada.
 */
export default function TwinScreen(): React.ReactElement {
  const api = useApi();
  const [scenario, setScenario] = useState<string | null>(null);

  const twin = useQuery({ queryKey: ['twin'], queryFn: () => api.twin.read() });
  const projection = useQuery({
    queryKey: ['projection', scenario],
    queryFn: () => api.twin.project(scenario as string),
    enabled: scenario !== null,
  });

  if (twin.isLoading) {
    return (
      <Screen>
        <LoadingState />
      </Screen>
    );
  }
  if (twin.isError) {
    return (
      <Screen>
        <ErrorState
          message={twin.error instanceof Error ? twin.error.message : t('error.generic')}
          onRetry={() => void twin.refetch()}
        />
      </Screen>
    );
  }

  const data = twin.data;
  const known = (data?.traits ?? []).filter((trait) => trait.confidence > 0 && trait.sample_size > 0);
  const unknown = (data?.traits ?? []).filter(
    (trait) => trait.confidence === 0 || trait.sample_size === 0,
  );

  return (
    <Screen>
      <Stack gap="lg">
        <Stack gap="xs">
          <Text variant="title" tone="strong" accessibilityRole="header">
            {t('twin.title')}
          </Text>
          <Text variant="callout" tone="muted">
            {t('twin.subtitle')}
          </Text>
          <Text variant="caption" tone="faint">
            {t('twin.completeness', { percent: Math.round((data?.completeness ?? 0) * 100) })}
          </Text>
        </Stack>

        {known.length === 0 ? (
          <EmptyState title={t('journal.stillLearning')} body={t('journal.stillLearningBody')} />
        ) : (
          known.map((trait) => <TraitCard key={trait.key} trait={trait} />)
        )}

        {/* Lo que aún no sabemos se lista: dice qué registrar a continuación. */}
        {unknown.length > 0 ? (
          <Card tone="sunken">
            <Stack gap="sm">
              <Text variant="caption" tone="muted">
                {t('twin.unknownTrait')}
              </Text>
              {unknown.map((trait) => (
                <Text key={trait.key} variant="caption" tone="faint">
                  · {t(`twin.trait.${trait.key}`)}
                </Text>
              ))}
            </Stack>
          </Card>
        ) : null}

        <Stack gap="sm">
          <Text variant="subheading">{t('twin.projectTitle')}</Text>
          <Stack direction="row" gap="sm" wrap>
            {SCENARIOS.map((option) => (
              <ScenarioChip
                key={option}
                label={t(`twin.scenario.${option}`)}
                active={scenario === option}
                onPress={() => setScenario(option)}
              />
            ))}
          </Stack>
        </Stack>

        {projection.isLoading ? <LoadingState /> : null}
        {projection.data ? <ProjectionCard projection={projection.data} /> : null}
      </Stack>
    </Screen>
  );
}

function TraitCard({ trait }: { trait: Trait }): React.ReactElement {
  const theme = useTheme();
  const isDays = trait.key === 'style_longevity_days';

  return (
    <Card>
      <Stack gap="sm">
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' }}>
          <Text variant="subheading" style={{ flex: 1 }}>
            {t(`twin.trait.${trait.key}`)}
          </Text>
          <Text variant="bodyStrong" tone="accent">
            {isDays ? trait.value.toFixed(1) : `${Math.round(trait.value * 100)}`}
          </Text>
        </View>

        <View
          style={{
            height: 4,
            backgroundColor: theme.colors.surfaceSunken,
            borderRadius: theme.radius.pill,
          }}
        >
          <View
            style={{
              width: `${Math.round(trait.confidence * 100)}%`,
              height: '100%',
              backgroundColor: theme.colors.accent,
              borderRadius: theme.radius.pill,
            }}
          />
        </View>

        <Text variant="caption" tone="muted">
          {sampleSizeLabel(trait.sample_size)}
        </Text>

        {trait.is_controlled ? (
          <Text variant="caption" tone="accent">
            {t('experiment.title')}
          </Text>
        ) : null}
      </Stack>
    </Card>
  );
}

function ProjectionCard({ projection }: { projection: Projection }): React.ReactElement {
  return (
    <Card tone={projection.can_project ? 'default' : 'sunken'}>
      <Stack gap="md">
        <Text variant="subheading">{t(`twin.direction.${projection.direction}`)}</Text>

        {/* Sin base histórica no se proyecta: se dice qué falta registrar. */}
        {!projection.can_project ? (
          <Stack gap="xs">
            {projection.missing_data_keys.map((key) => (
              <Text key={key} variant="callout" tone="accent">
                → {tKey(key)}
              </Text>
            ))}
          </Stack>
        ) : null}

        <WhyThis explanation={projection.explanation} defaultOpen={projection.can_project} />
      </Stack>
    </Card>
  );
}

function ScenarioChip({
  label,
  active,
  onPress,
}: {
  label: string;
  active: boolean;
  onPress: () => void;
}): React.ReactElement {
  const theme = useTheme();
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityState={{ selected: active }}
      style={{
        minHeight: theme.touchTarget.minimum,
        paddingHorizontal: theme.spacing.md,
        justifyContent: 'center',
        borderRadius: theme.radius.pill,
        borderWidth: 1,
        borderColor: active ? theme.colors.accent : theme.colors.line,
        backgroundColor: active ? theme.colors.accentSoft : 'transparent',
      }}
    >
      <Text variant="caption" tone={active ? 'strong' : 'muted'}>
        {label}
      </Text>
    </Pressable>
  );
}
