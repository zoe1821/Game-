import React from 'react';
import { View, type StyleProp, type ViewStyle } from 'react-native';

import { useTheme } from '@/design/theme';
import type { SpacingToken } from '@/design/tokens';

export interface StackProps {
  children: React.ReactNode;
  gap?: SpacingToken;
  direction?: 'column' | 'row';
  align?: ViewStyle['alignItems'];
  justify?: ViewStyle['justifyContent'];
  wrap?: boolean;
  style?: StyleProp<ViewStyle>;
}

/** Layout por tokens: nada de márgenes sueltos repartidos por las pantallas. */
export function Stack({
  children,
  gap = 'md',
  direction = 'column',
  align,
  justify,
  wrap = false,
  style,
}: StackProps): React.ReactElement {
  const theme = useTheme();
  return (
    <View
      style={[
        {
          flexDirection: direction,
          gap: theme.spacing[gap],
          alignItems: align,
          justifyContent: justify,
          flexWrap: wrap ? 'wrap' : 'nowrap',
        },
        style,
      ]}
    >
      {children}
    </View>
  );
}
