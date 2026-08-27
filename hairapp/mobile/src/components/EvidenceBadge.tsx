import React from 'react';
import { View } from 'react-native';

import { useTheme } from '@/design/theme';
import { t } from '@/i18n';
import type { EvidenceLevel } from '@/api/types';

import { Text } from './Text';

export interface EvidenceBadgeProps {
  level: EvidenceLevel;
}

/**
 * Etiqueta de nivel de evidencia (B4).
 *
 * Va visible en el contenido educativo y en las técnicas, no escondida detrás
 * de un despliegue: la persona debe poder distinguir «esto está medido» de
 * «esto lo hace mucha gente» de un vistazo.
 */
export function EvidenceBadge({ level }: EvidenceBadgeProps): React.ReactElement {
  const theme = useTheme();

  const toneByLevel: Record<EvidenceLevel, { border: string; ink: string }> = {
    scientific_evidence: { border: theme.colors.accent, ink: theme.colors.accent },
    professional_consensus: { border: theme.colors.lineStrong, ink: theme.colors.ink },
    extended_anecdote: { border: theme.colors.warn, ink: theme.colors.warn },
    unsupported_trend: { border: theme.colors.alert, ink: theme.colors.alert },
  };
  const tone = toneByLevel[level];

  return (
    <View
      style={{
        alignSelf: 'flex-start',
        borderWidth: 1,
        borderColor: tone.border,
        borderRadius: theme.radius.pill,
        paddingHorizontal: theme.spacing.sm,
        paddingVertical: theme.spacing.xxs,
      }}
    >
      <Text variant="overline" style={{ color: tone.ink }}>
        {t(`evidence.${level}`).toUpperCase()}
      </Text>
    </View>
  );
}
