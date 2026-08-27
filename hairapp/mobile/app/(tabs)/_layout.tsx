import { Tabs } from 'expo-router';
import React from 'react';

import { useTheme } from '@/design/theme';
import { t } from '@/i18n';

/**
 * Navegación principal. Cinco pestañas, no más: una barra con siete iconos es
 * una barra que nadie lee.
 *
 * Sin emojis como iconografía (A19): las etiquetas son texto, que además es lo
 * que mejor funciona con lector de pantalla y con tamaños de texto grandes.
 */
export default function TabsLayout(): React.ReactElement {
  const theme = useTheme();
  return (
    <Tabs
      sceneContainerStyle={{ backgroundColor: theme.colors.background }}
      screenOptions={{
        tabBarActiveTintColor: theme.colors.accent,
        tabBarInactiveTintColor: theme.colors.inkMuted,
        tabBarStyle: {
          backgroundColor: theme.colors.surface,
          borderTopColor: theme.colors.line,
        },
        tabBarLabelStyle: { fontSize: theme.typography.caption.fontSize },
        headerStyle: { backgroundColor: theme.colors.background },
        headerTintColor: theme.colors.ink,
        headerShadowVisible: false,
      }}
    >
      <Tabs.Screen name="index" options={{ title: t('home.todayTitle') }} />
      <Tabs.Screen name="map" options={{ title: t('zoneDetail.title') }} />
      <Tabs.Screen name="routine" options={{ title: t('routine.title') }} />
      <Tabs.Screen name="journal" options={{ title: t('journal.title') }} />
      <Tabs.Screen name="learn" options={{ title: t('education.title') }} />
    </Tabs>
  );
}
