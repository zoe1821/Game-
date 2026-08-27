import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React, { createContext, useContext, useMemo } from 'react';

import { secureTokenStore, useAuthStore } from '@/state/auth';

import { ApiClient, ApiError } from './client';
import { endpoints, type Endpoints } from './endpoints';

const ApiContext = createContext<Endpoints | null>(null);

function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60_000,
        retry(failureCount, error) {
          // Un 401 o una falta de consentimiento no se reintentan: reintentar
          // no los va a arreglar y solo gasta batería y datos.
          if (error instanceof ApiError && (error.status === 401 || error.isConsentRequired)) {
            return false;
          }
          return failureCount < 2;
        },
      },
      mutations: { retry: 0 },
    },
  });
}

export function ApiProvider({ children }: { children: React.ReactNode }): React.ReactElement {
  const setSignedOut = useAuthStore((state) => state.setSignedOut);

  const value = useMemo(() => {
    const client = new ApiClient({
      ...secureTokenStore,
      async clear() {
        await secureTokenStore.clear();
        setSignedOut();
      },
    });
    return endpoints(client);
  }, [setSignedOut]);

  const queryClient = useMemo(createQueryClient, []);

  return (
    <QueryClientProvider client={queryClient}>
      <ApiContext.Provider value={value}>{children}</ApiContext.Provider>
    </QueryClientProvider>
  );
}

export function useApi(): Endpoints {
  const api = useContext(ApiContext);
  if (api === null) {
    throw new Error('useApi debe usarse dentro de un ApiProvider');
  }
  return api;
}
