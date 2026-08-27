import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import React from 'react';
import { Pressable, View } from 'react-native';

import { useApi } from '@/api/provider';
import type { Finding, JournalEntry } from '@/api/types';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Screen } from '@/components/Screen';
import { Stack } from '@/components/Stack';
import { EmptyState, ErrorState, LoadingState } from '@/components/StateViews';
import { Text } from '@/components/Text';
import { WhyThis } from '@/components/WhyThis';
import { useTheme } from '@/design/theme';
import { t, tKey } from '@/i18n';

const RATING_DAYS = ['day1', 'day2', 'day3', 'day4_plus'] as const;

/**
 * Diario de wash day (A13).
 *
 * La parte que de verdad importa es valorar los días 2, 3 y 4: sin eso el twin
 * no puede aprender cuánto dura un resultado, que es una de las preguntas que
 * la gente se hace de verdad.
 */
export default function Journal(): React.ReactElement {
  const api = useApi();
  const queryClient = useQueryClient();

  const entries = useQuery({ queryKey: ['journal'], queryFn: () => api.journal.list() });
  const insights = useQuery({ queryKey: ['insights'], queryFn: () => api.journal.insights() });

  const create = useMutation({
    mutationFn: () =>
      api.journal.create({ entry_date: new Date().toISOString().slice(0, 10) }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['journal'] });
      void queryClient.invalidateQueries({ queryKey: ['insights'] });
      void queryClient.invalidateQueries({ queryKey: ['cold-start'] });
    },
  });

  if (entries.isLoading) {
    return (
      <Screen>
        <LoadingState />
      </Screen>
    );
  }
  if (entries.isError) {
    return (
      <Screen>
        <ErrorState
          message={entries.error instanceof Error ? entries.error.message : t('error.generic')}
          onRetry={() => void entries.refetch()}
        />
      </Screen>
    );
  }

  const list = entries.data ?? [];

  return (
    <Screen>
      <Stack gap="lg">
        <Stack gap="xs">
          <Text variant="title" tone="strong" accessibilityRole="header">
            {t('journal.title')}
          </Text>
          <Text variant="callout" tone="muted">
            {t('journal.subtitle')}
          </Text>
        </Stack>

        <Button
          label={t('journal.newEntry')}
          onPress={() => create.mutate()}
          loading={create.isPending}
        />

        {/* Sin datos suficientes se dice, sin disculparse ni inventar (B2). */}
        {insights.data && !insights.data.has_enough_data ? (
          <Card tone="sunken">
            <Stack gap="sm">
              <Text variant="subheading">{t('journal.stillLearning')}</Text>
              <Text variant="callout" tone="muted">
                {t('journal.stillLearningBody')}
              </Text>
            </Stack>
          </Card>
        ) : null}

        {insights.data?.findings.map((finding) => (
          <FindingCard key={`${finding.kind}:${finding.subject}`} finding={finding} />
        ))}

        {list.length === 0 ? (
          <EmptyState title={t('journal.empty')} />
        ) : (
          list.map((entry) => <EntryCard key={entry.id} entry={entry} />)
        )}
      </Stack>
    </Screen>
  );
}

function EntryCard({ entry }: { entry: JournalEntry }): React.ReactElement {
  const theme = useTheme();
  const api = useApi();
  const queryClient = useQueryClient();

  const rate = useMutation({
    mutationFn: (ratings: Record<string, number>) => api.journal.rate(entry.id, ratings),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['journal'] });
      void queryClient.invalidateQueries({ queryKey: ['insights'] });
      void queryClient.invalidateQueries({ queryKey: ['twin'] });
    },
  });

  return (
    <Card>
      <Stack gap="md">
        <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
          <Text variant="bodyStrong">{entry.date}</Text>
          {entry.longevity_days > 0 ? (
            <Text variant="caption" tone="accent">
              {t('journal.lastedDays', { count: entry.longevity_days })}
            </Text>
          ) : null}
        </View>

        {RATING_DAYS.map((day, index) => (
          <View key={day} style={{ gap: theme.spacing.xs }}>
            <Text variant="caption" tone="muted">
              {t('journal.rateDay', { day: index === 3 ? '4+' : index + 1 })}
            </Text>
            <Stack direction="row" gap="xs">
              {[1, 2, 3, 4].map((value) => {
                const selected = entry.ratings[day] === value;
                return (
                  <Pressable
                    key={value}
                    onPress={() => rate.mutate({ [day]: value })}
                    accessibilityRole="radio"
                    accessibilityState={{ selected }}
                    accessibilityLabel={t(`journal.rating.${value}`)}
                    style={{
                      flex: 1,
                      minHeight: theme.touchTarget.minimum,
                      alignItems: 'center',
                      justifyContent: 'center',
                      borderRadius: theme.radius.md,
                      borderWidth: 1,
                      borderColor: selected ? theme.colors.accent : theme.colors.line,
                      backgroundColor: selected ? theme.colors.accentSoft : 'transparent',
                    }}
                  >
                    <Text variant="caption">{t(`journal.rating.${value}`)}</Text>
                  </Pressable>
                );
              })}
            </Stack>
          </View>
        ))}
      </Stack>
    </Card>
  );
}

function FindingCard({ finding }: { finding: Finding }): React.ReactElement {
  return (
    <Card tone={finding.is_actionable ? 'accent' : 'default'}>
      <Stack gap="sm">
        <Text variant="overline" tone="muted">
          {t(`learning.strength.${finding.strength}`)}
        </Text>
        <Text variant="subheading">{finding.subject}</Text>
        <Text variant="caption" tone="muted">
          {`${finding.with_n} / ${finding.without_n} · ${finding.difference > 0 ? '+' : ''}${finding.difference.toFixed(2)}`}
        </Text>

        {/* Las variables sin controlar se enseñan: es la diferencia entre una
            herramienta y un horóscopo. */}
        {finding.uncontrolled_variables.length > 0 ? (
          <Stack gap="xxs">
            <Text variant="caption" tone="warn">
              {t('learning.uncontrolledIntro')}
            </Text>
            {finding.uncontrolled_variables.map((variable) => (
              <Text key={variable} variant="caption" tone="faint">
                · {tKey(`learning.uncontrolled.${variable}`)}
              </Text>
            ))}
          </Stack>
        ) : null}

        <WhyThis explanation={finding.explanation} />
      </Stack>
    </Card>
  );
}
