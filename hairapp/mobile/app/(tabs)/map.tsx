import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import React, { useState } from 'react';
import { Pressable, View } from 'react-native';

import { useApi } from '@/api/provider';
import type { Measured, Zone } from '@/api/types';
import { Card } from '@/components/Card';
import { Screen } from '@/components/Screen';
import { Stack } from '@/components/Stack';
import { ErrorState, LoadingState } from '@/components/StateViews';
import { Text } from '@/components/Text';
import { useTheme } from '@/design/theme';
import { t, tKey } from '@/i18n';

/**
 * Mapa capilar por zonas (A4) — el primer pilar del producto.
 *
 * Lo que esta pantalla tiene que dejar claro de un vistazo:
 *  1. Que la cabeza tiene zonas distintas y pueden comportarse distinto.
 *  2. Qué sabemos de cada una y con cuánta seguridad.
 *  3. Qué **no** sabemos, sin disimularlo con un valor por defecto.
 *  4. Que cualquier cosa se puede corregir, y que la corrección manda.
 */
export default function HairMap(): React.ReactElement {
  const api = useApi();
  const [openZone, setOpenZone] = useState<string | null>(null);

  const zones = useQuery({ queryKey: ['zones'], queryFn: () => api.profile.zones() });

  if (zones.isLoading) {
    return (
      <Screen>
        <LoadingState />
      </Screen>
    );
  }
  if (zones.isError) {
    return (
      <Screen>
        <ErrorState
          message={zones.error instanceof Error ? zones.error.message : t('error.generic')}
          onRetry={() => void zones.refetch()}
        />
      </Screen>
    );
  }

  return (
    <Screen>
      <Stack gap="lg">
        <Stack gap="xs">
          <Text variant="title" tone="strong" accessibilityRole="header">
            {t('zoneDetail.title')}
          </Text>
          <Text variant="callout" tone="muted">
            {t('zoneDetail.subtitle')}
          </Text>
        </Stack>

        <Stack gap="sm">
          {(zones.data ?? []).map((zone) => (
            <ZoneRow
              key={zone.zone}
              zone={zone}
              expanded={openZone === zone.zone}
              onToggle={() => setOpenZone((current) => (current === zone.zone ? null : zone.zone))}
            />
          ))}
        </Stack>
      </Stack>
    </Screen>
  );
}

interface ZoneRowProps {
  zone: Zone;
  expanded: boolean;
  onToggle: () => void;
}

function ZoneRow({ zone, expanded, onToggle }: ZoneRowProps): React.ReactElement {
  const theme = useTheme();
  const fields = Object.entries(zone.measurements);
  const hasData = fields.length > 0;

  return (
    <Card tone={expanded ? 'default' : 'sunken'}>
      <Pressable
        onPress={onToggle}
        accessibilityRole="button"
        accessibilityState={{ expanded }}
        accessibilityLabel={tKey(zone.label_key)}
        style={{ minHeight: theme.touchTarget.minimum, justifyContent: 'center' }}
      >
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text variant="subheading">{tKey(zone.label_key)}</Text>
          <Text variant="caption" tone={hasData ? 'muted' : 'faint'}>
            {hasData ? `${fields.length}` : t('zoneDetail.notObserved')}
          </Text>
        </View>
      </Pressable>

      {expanded ? (
        <Stack gap="md" style={{ marginTop: theme.spacing.md }}>
          {hasData ? (
            fields.map(([field, measured]) => (
              <MeasurementRow key={field} zone={zone.zone} field={field} measured={measured} />
            ))
          ) : (
            <Text variant="callout" tone="faint">
              {t('zoneDetail.notObserved')}
            </Text>
          )}

          {zone.damage_signs.length > 0 ? (
            <Text variant="caption" tone="warn">
              {zone.damage_signs.join(' · ')}
            </Text>
          ) : null}
        </Stack>
      ) : null}
    </Card>
  );
}

interface MeasurementRowProps {
  zone: string;
  field: string;
  measured: Measured;
}

function MeasurementRow({ zone, field, measured }: MeasurementRowProps): React.ReactElement {
  const theme = useTheme();
  const api = useApi();
  const queryClient = useQueryClient();

  const correct = useMutation({
    mutationFn: (value: unknown) => api.profile.correctZone(zone, field, value),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['zones'] });
      void queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
  });

  const isUserValue = measured.source === 'user';

  return (
    <View style={{ gap: theme.spacing.xs }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <Text variant="caption" tone="muted">
          {t(`zoneDetail.fields.${field}`)}
        </Text>
        <Text variant="bodyStrong">{formatValue(measured.value)}</Text>
      </View>

      {/* La procedencia es visible siempre: no es lo mismo lo que dijiste tú
          que lo que dedujimos nosotros. */}
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <Text variant="caption" tone={isUserValue ? 'accent' : 'faint'}>
          {isUserValue
            ? t('zoneDetail.corrected')
            : t('zoneDetail.estimatedBy', { source: measured.source })}
        </Text>
        {!isUserValue ? (
          <View
            style={{
              width: 40,
              height: 3,
              backgroundColor: theme.colors.surfaceSunken,
              borderRadius: theme.radius.pill,
            }}
          >
            <View
              style={{
                width: `${Math.round(measured.confidence * 100)}%`,
                height: '100%',
                backgroundColor: theme.colors.accent,
                borderRadius: theme.radius.pill,
              }}
            />
          </View>
        ) : null}
      </View>

      {correct.isError ? (
        <Text variant="caption" tone="alert">
          {correct.error instanceof Error ? correct.error.message : t('error.generic')}
        </Text>
      ) : null}
    </View>
  );
}

function formatValue(value: Measured['value']): string {
  if (typeof value === 'number') {
    return Number.isInteger(value) ? String(value) : value.toFixed(2);
  }
  if (typeof value === 'boolean') {
    return value ? '✓' : '—';
  }
  return String(value);
}
