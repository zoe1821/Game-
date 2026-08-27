import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import React, { useState } from 'react';
import { TextInput, View } from 'react-native';

import { useApi } from '@/api/provider';
import type { MatchResult } from '@/api/types';
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
 * Inventario y escáner de ingredientes (A11, A15).
 *
 * El orden de la pantalla es la tesis anti-consumista: primero lo que ya
 * tienes, después los duplicados que ya tienes de más, y solo al final algo
 * que comprar — si hace falta.
 */
export default function Inventory(): React.ReactElement {
  const api = useApi();
  const queryClient = useQueryClient();
  const [inci, setInci] = useState('');

  const items = useQuery({ queryKey: ['inventory'], queryFn: () => api.inventory.list() });
  const duplicates = useQuery({
    queryKey: ['inventory-duplicates'],
    queryFn: () => api.inventory.duplicates(),
  });

  const scan = useMutation({ mutationFn: (value: string) => api.inventory.scanIngredients(value) });

  const remove = useMutation({
    mutationFn: (id: string) => api.inventory.remove(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['inventory'] });
      void queryClient.invalidateQueries({ queryKey: ['inventory-duplicates'] });
    },
  });

  if (items.isLoading) {
    return (
      <Screen>
        <LoadingState />
      </Screen>
    );
  }
  if (items.isError) {
    return (
      <Screen>
        <ErrorState
          message={items.error instanceof Error ? items.error.message : t('error.generic')}
          onRetry={() => void items.refetch()}
        />
      </Screen>
    );
  }

  const list = items.data ?? [];

  return (
    <Screen>
      <Stack gap="lg">
        <Stack gap="xs">
          <Text variant="title" tone="strong" accessibilityRole="header">
            {t('inventory.title')}
          </Text>
          <Text variant="callout" tone="muted">
            {t('inventory.subtitle')}
          </Text>
        </Stack>

        {/* Los duplicados se muestran antes que cualquier sugerencia de compra. */}
        {(duplicates.data ?? []).map((duplicate) => (
          <Card key={duplicate.category} tone="warn">
            <Text variant="callout">
              {t('inventory.duplicateWarning', { count: duplicate.count })}
            </Text>
          </Card>
        ))}

        {list.length === 0 ? (
          <EmptyState title={t('inventory.empty')} />
        ) : (
          list.map((item) => (
            <Card key={item.id} tone={item.expired ? 'warn' : 'default'}>
              <Stack gap="sm">
                <View
                  style={{ flexDirection: 'row', justifyContent: 'space-between', gap: 12 }}
                >
                  <Text variant="bodyStrong" style={{ flex: 1 }}>
                    {item.display_name}
                  </Text>
                  <Text variant="caption" tone="muted">
                    {item.category ?? ''}
                  </Text>
                </View>
                {item.expires_on ? (
                  <Text variant="caption" tone={item.expired ? 'warn' : 'faint'}>
                    {item.expired
                      ? t('inventory.expired', { date: item.expires_on })
                      : t('inventory.expiresOn', { date: item.expires_on })}
                  </Text>
                ) : null}
                <Button
                  label={t('common.delete')}
                  variant="ghost"
                  fullWidth={false}
                  onPress={() => remove.mutate(item.id)}
                />
              </Stack>
            </Card>
          ))
        )}

        <IngredientScanner
          value={inci}
          onChange={setInci}
          onScan={() => scan.mutate(inci)}
          loading={scan.isPending}
          result={scan.data}
        />
      </Stack>
    </Screen>
  );
}

interface ScannerProps {
  value: string;
  onChange: (value: string) => void;
  onScan: () => void;
  loading: boolean;
  result:
    | {
        ingredients: Array<{ inci_name: string; functions: string[] }>;
        by_function: Record<string, string[]>;
        findings: Array<{ key: string; severity: string; function: string | null }>;
        declared_sensitivity_matches: string[];
        unrecognised_count: number;
      }
    | undefined;
}

function IngredientScanner({
  value,
  onChange,
  onScan,
  loading,
  result,
}: ScannerProps): React.ReactElement {
  const theme = useTheme();

  return (
    <Card tone="sunken">
      <Stack gap="md">
        <Text variant="subheading">{t('ingredients.title')}</Text>
        <TextInput
          value={value}
          onChangeText={onChange}
          placeholder={t('ingredients.paste')}
          placeholderTextColor={theme.colors.inkFaint}
          multiline
          accessibilityLabel={t('ingredients.paste')}
          style={{
            minHeight: 96,
            borderWidth: 1,
            borderColor: theme.colors.line,
            borderRadius: theme.radius.md,
            padding: theme.spacing.md,
            color: theme.colors.ink,
            fontSize: theme.typography.body.fontSize,
            textAlignVertical: 'top',
          }}
        />
        <Button
          label={t('common.continue')}
          onPress={onScan}
          loading={loading}
          disabled={value.trim().length < 3}
        />

        {result ? (
          <Stack gap="md">
            {result.declared_sensitivity_matches.length > 0 ? (
              <Card tone="alert">
                <Text variant="callout">{t('ingredients.sensitivityMatch')}</Text>
              </Card>
            ) : null}

            {/* Análisis por función, nunca un semáforo de bueno/malo. */}
            <Text variant="caption" tone="muted">
              {t('ingredients.byFunction')}
            </Text>
            {Object.entries(result.by_function).map(([fn, names]) => (
              <View key={fn} style={{ gap: theme.spacing.xxs }}>
                <Text variant="caption" tone="accent">
                  {t(`ingredients.function.${fn}`)}
                </Text>
                <Text variant="caption" tone="faint">
                  {names.join(', ')}
                </Text>
              </View>
            ))}

            {result.findings.map((finding) => (
              <Text
                key={finding.key}
                variant="callout"
                tone={finding.severity === 'conflict' ? 'warn' : 'default'}
              >
                {tKey(finding.key)}
              </Text>
            ))}

            {/* Lo desconocido se declara: no cuenta ni a favor ni en contra. */}
            {result.unrecognised_count > 0 ? (
              <Stack gap="xxs">
                <Text variant="caption" tone="muted">
                  {t('ingredients.unrecognised', { count: result.unrecognised_count })}
                </Text>
                <Text variant="caption" tone="faint">
                  {t('ingredients.unrecognisedHint')}
                </Text>
              </Stack>
            ) : null}
          </Stack>
        ) : null}
      </Stack>
    </Card>
  );
}

export function MatchOutcomeCard({ match }: { match: MatchResult }): React.ReactElement {
  const titles: Record<MatchResult['outcome'], string> = {
    already_owned: t('inventory.alreadyOwned'),
    owned_partial: t('inventory.ownedPartial'),
    needs_product: t('inventory.needsProduct'),
    unverifiable: t('match.no_data'),
  };

  return (
    <Card tone={match.outcome === 'already_owned' ? 'accent' : 'default'}>
      <Stack gap="sm">
        <Text variant="subheading">{titles[match.outcome]}</Text>
        {match.outcome === 'already_owned' ? (
          <Text variant="callout" tone="muted">
            {t('inventory.alreadyOwnedBody')}
          </Text>
        ) : null}
        {match.outcome === 'owned_partial' ? (
          <Text variant="callout" tone="muted">
            {t('inventory.ownedPartialBody', { missing: match.unmet_attributes.join(', ') })}
          </Text>
        ) : null}
        <WhyThis explanation={match.explanation} />
      </Stack>
    </Card>
  );
}
