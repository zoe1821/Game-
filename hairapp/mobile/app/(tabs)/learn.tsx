import { useQuery } from '@tanstack/react-query';
import React, { useState } from 'react';
import { Pressable } from 'react-native';

import { useApi } from '@/api/provider';
import type { Myth } from '@/api/types';
import { Card } from '@/components/Card';
import { EvidenceBadge } from '@/components/EvidenceBadge';
import { Screen } from '@/components/Screen';
import { Stack } from '@/components/Stack';
import { ErrorState, LoadingState } from '@/components/StateViews';
import { Text } from '@/components/Text';
import { useTheme } from '@/design/theme';
import { t, tKey } from '@/i18n';

/**
 * Enciclopedia y detector de mitos (A17).
 *
 * Cada entrada lleva su etiqueta de evidencia visible (B4) y, sobre todo, el
 * **mecanismo**: por qué ocurre lo que ocurre. Un mito desmontado sin explicar
 * por qué circula no convence a nadie.
 */
export default function Learn(): React.ReactElement {
  const api = useApi();
  const [tab, setTab] = useState<'myths' | 'rules'>('myths');

  const myths = useQuery({ queryKey: ['myths'], queryFn: () => api.education.myths() });
  const rules = useQuery({
    queryKey: ['rules'],
    queryFn: () => api.education.rules(),
    enabled: tab === 'rules',
  });

  return (
    <Screen>
      <Stack gap="lg">
        <Stack gap="xs">
          <Text variant="title" tone="strong" accessibilityRole="header">
            {t('education.title')}
          </Text>
          <Text variant="callout" tone="muted">
            {tab === 'myths' ? t('education.mythsSubtitle') : t('education.rulesSubtitle')}
          </Text>
        </Stack>

        <Stack direction="row" gap="sm">
          <TabButton
            label={t('education.mythsTitle')}
            active={tab === 'myths'}
            onPress={() => setTab('myths')}
          />
          <TabButton
            label={t('education.rulesTitle')}
            active={tab === 'rules'}
            onPress={() => setTab('rules')}
          />
        </Stack>

        {tab === 'myths' ? (
          myths.isLoading ? (
            <LoadingState />
          ) : myths.isError ? (
            <ErrorState
              message={myths.error instanceof Error ? myths.error.message : t('error.generic')}
              onRetry={() => void myths.refetch()}
            />
          ) : (
            (myths.data ?? []).map((myth) => <MythCard key={myth.id} myth={myth} />)
          )
        ) : rules.isLoading ? (
          <LoadingState />
        ) : (
          (rules.data ?? []).map((rule) => (
            <Card key={rule.id} tone="sunken">
              <Stack gap="sm">
                <EvidenceBadge level={rule.evidence_level as Myth['evidence_level']} />
                <Text variant="caption" tone="muted">
                  {rule.id}
                </Text>
                <Text variant="callout">{rule.mechanism}</Text>
                {rule.sources.length > 0 ? (
                  <Text variant="caption" tone="faint">
                    {rule.sources.join(' · ')}
                  </Text>
                ) : null}
              </Stack>
            </Card>
          ))
        )}
      </Stack>
    </Screen>
  );
}

function MythCard({ myth }: { myth: Myth }): React.ReactElement {
  return (
    <Card tone="alert">
      <Stack gap="sm">
        <EvidenceBadge level={myth.evidence_level} />
        <Text variant="subheading">{tKey(myth.message_key)}</Text>
        <Text variant="caption" tone="muted">
          {t('education.mechanism')}
        </Text>
        <Text variant="callout">{myth.mechanism}</Text>
      </Stack>
    </Card>
  );
}

function TabButton({
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
      accessibilityRole="tab"
      accessibilityState={{ selected: active }}
      style={{
        minHeight: theme.touchTarget.minimum,
        paddingHorizontal: theme.spacing.lg,
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
