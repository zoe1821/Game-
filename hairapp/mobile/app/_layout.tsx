import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import * as Localization from 'expo-localization';
import React, { useEffect } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { ApiProvider } from '@/api/provider';
import { ThemeProvider, useTheme } from '@/design/theme';
import { setLocale } from '@/i18n';
import { useAuthStore, useOnboardingStore } from '@/state/auth';

function Navigator(): React.ReactElement {
  const theme = useTheme();
  return (
    <>
      <StatusBar style={theme.scheme === 'dark' ? 'light' : 'dark'} />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: theme.colors.background },
          headerTintColor: theme.colors.ink,
          headerShadowVisible: false,
          headerTitleStyle: {
            fontSize: theme.typography.subheading.fontSize,
            fontWeight: theme.typography.subheading.fontWeight,
          },
          contentStyle: { backgroundColor: theme.colors.background },
        }}
      >
        <Stack.Screen name="index" options={{ headerShown: false }} />
        <Stack.Screen name="onboarding" options={{ headerShown: false }} />
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      </Stack>
    </>
  );
}

export default function RootLayout(): React.ReactElement {
  const hydrateAuth = useAuthStore((state) => state.hydrate);
  const hydrateOnboarding = useOnboardingStore((state) => state.hydrate);

  useEffect(() => {
    // El idioma sale del dispositivo. Nada de un selector obligatorio al
    // arrancar: si el sistema está en inglés, la app está en inglés.
    setLocale(Localization.getLocales()[0]?.languageCode);
    void hydrateAuth();
    void hydrateOnboarding();
  }, [hydrateAuth, hydrateOnboarding]);

  return (
    <SafeAreaProvider>
      <ThemeProvider>
        <ApiProvider>
          <Navigator />
        </ApiProvider>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}
