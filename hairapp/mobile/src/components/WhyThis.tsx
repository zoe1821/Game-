import React, { useState } from 'react';
import { Pressable, View } from 'react-native';

import { useTheme } from '@/design/theme';
import { sampleSizeLabel, t, tKey } from '@/i18n';
import type { Explanation } from '@/api/types';

import { ConfidenceBar } from './ConfidenceBar';
import { Card } from './Card';
import { Stack } from './Stack';
import { Text } from './Text';

export interface WhyThisProps {
  explanation: Explanation;
  /** Abierto de inicio en pantallas donde la explicación *es* el contenido. */
  defaultOpen?: boolean;
}

/**
 * El bloque «¿por qué esto?» (A21).
 *
 * Es el componente más importante del producto y por eso es también el más
 * literal: enseña qué datos se usaron, qué se observó, qué incertidumbre hay y
 * qué alternativas existen.
 *
 * Las dos confianzas se muestran **por separado y siempre juntas**. No se
 * promedian: una regla sólida sin datos tuyos y una regla floja con catorce
 * registros tuyos son situaciones opuestas, y un solo número las haría
 * idénticas (docs/08-EVIDENCE-POLICY.md §2).
 */
export function WhyThis({ explanation, defaultOpen = false }: WhyThisProps): React.ReactElement {
  const theme = useTheme();
  const [open, setOpen] = useState(defaultOpen);

  const contradicts =
    typeof explanation.params.personal_direction === 'string' &&
    explanation.params.personal_direction === 'contradicts';

  return (
    <View>
      <Pressable
        onPress={() => setOpen((previous) => !previous)}
        accessibilityRole="button"
        accessibilityState={{ expanded: open }}
        hitSlop={theme.spacing.sm}
        style={{ minHeight: theme.touchTarget.minimum, justifyContent: 'center' }}
      >
        <Text variant="caption" tone="accent">
          {open ? `${t('common.whyThis')} ↑` : `${t('common.whyThis')} ↓`}
        </Text>
      </Pressable>

      {open ? (
        <Card tone="sunken" style={{ marginTop: theme.spacing.sm }}>
          <Stack gap="lg">
            <Text variant="callout">{tKey(explanation.summary_key, explanation.params as never)}</Text>

            <Stack gap="md">
              <ConfidenceBar
                label={`${t('confidence.evidenceLabel')} · ${tKey(`evidence.${explanation.evidence_level}`)}`}
                value={explanation.evidence_confidence}
                tone="evidence"
              />
              <ConfidenceBar
                label={t('confidence.personalLabel')}
                value={explanation.personal_confidence}
                tone="personal"
                contradicts={contradicts}
              />
              {/* El tamaño de muestra viaja siempre, nunca es opcional. */}
              <Text variant="caption" tone="muted">
                {sampleSizeLabel(explanation.sample_size)}
              </Text>
              {contradicts ? (
                <Text variant="caption" tone="warn">
                  {t('confidence.contradicts')}
                </Text>
              ) : null}
            </Stack>

            <Text variant="caption" tone="faint">
              {t('confidence.explainer')}
            </Text>

            {explanation.uncertainty_keys.length > 0 ? (
              <Stack gap="xs">
                {explanation.uncertainty_keys.map((key) => (
                  <Text key={key} variant="caption" tone="muted">
                    · {tKey(key)}
                  </Text>
                ))}
              </Stack>
            ) : null}

            {explanation.alternatives.length > 0 ? (
              <Stack gap="xs">
                {explanation.alternatives.map((key) => (
                  <Text key={key} variant="caption" tone="accent">
                    → {tKey(key)}
                  </Text>
                ))}
              </Stack>
            ) : null}
          </Stack>
        </Card>
      ) : null}
    </View>
  );
}
