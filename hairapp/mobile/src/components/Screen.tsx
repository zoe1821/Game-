import React from 'react';
import { ScrollView, View, type StyleProp, type ViewStyle } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '@/design/theme';

export interface ScreenProps {
  children?: React.ReactNode;
  scroll?: boolean;
  style?: StyleProp<ViewStyle>;
  contentStyle?: StyleProp<ViewStyle>;
}

export function Screen({ children, scroll = true, style, contentStyle }: ScreenProps): React.ReactElement {
  const theme = useTheme();
  const insets = useSafeAreaInsets();

  const padding = {
    paddingHorizontal: theme.spacing.lg,
    paddingTop: theme.spacing.lg,
    paddingBottom: insets.bottom + theme.spacing.xxl,
  };

  if (!scroll) {
    return (
      <View style={[{ flex: 1, backgroundColor: theme.colors.background }, padding, style]}>
        {children}
      </View>
    );
  }

  return (
    <ScrollView
      style={[{ flex: 1, backgroundColor: theme.colors.background }, style]}
      contentContainerStyle={[padding, contentStyle]}
      keyboardShouldPersistTaps="handled"
    >
      {children}
    </ScrollView>
  );
}
