import type { ApiClient } from './client';
import type {
  ColdStartGuidance,
  Consent,
  ConsentPurpose,
  DepthLevel,
  DigitalTwin,
  HairForecast,
  Insights,
  JournalEntry,
  MatchResult,
  Me,
  Myth,
  Profile,
  Projection,
  Routine,
  ScanResult,
  Technique,
  Tokens,
  Zone,
} from './types';

export interface EssentialOnboarding {
  dominant_pattern?: string;
  approximate_length_cm?: number;
  wash_frequency_days?: number;
  primary_goal: string;
  country?: string;
  is_chemically_processed?: boolean;
}

export interface RoutineRequest {
  kind?: string;
  available_minutes?: number;
  temperature_c?: number;
  relative_humidity?: number;
  uv_index?: number;
  scalp_observations?: string[];
  scalp_referral_signs?: string[];
}

/** Todas las llamadas en un sitio: las pantallas no construyen rutas. */
export function endpoints(client: ApiClient) {
  return {
    auth: {
      register: (payload: {
        email: string;
        password: string;
        birth_date: string;
        locale: string;
        accepted_terms: boolean;
        accepted_privacy: boolean;
      }) => client.request<Tokens>('/api/v1/auth/register', { method: 'POST', body: payload }),

      login: (payload: { email: string; password: string }) =>
        client.request<Tokens>('/api/v1/auth/login', { method: 'POST', body: payload }),

      logout: () => client.request<void>('/api/v1/auth/logout', { method: 'POST' }),

      me: () => client.request<Me>('/api/v1/auth/me'),

      setConsents: (consents: Array<{ purpose: ConsentPurpose; granted: boolean }>) =>
        client.request<Consent[]>('/api/v1/auth/consents', { method: 'PUT', body: consents }),

      deleteAccount: () => client.request<void>('/api/v1/auth/account', { method: 'DELETE' }),
    },

    profile: {
      read: () => client.request<Profile>('/api/v1/profile'),

      essentialOnboarding: (payload: EssentialOnboarding) =>
        client.request<Profile>('/api/v1/profile/onboarding/essential', {
          method: 'POST',
          body: payload,
        }),

      deepOnboarding: (section: string, answers: Record<string, unknown>) =>
        client.request<Profile>('/api/v1/profile/onboarding/deep', {
          method: 'POST',
          body: { section, answers },
        }),

      setDepthLevel: (level: DepthLevel) =>
        client.request<Profile>('/api/v1/profile/depth-level', {
          method: 'PUT',
          query: { level },
        }),

      setGoals: (goals: string[]) =>
        client.request<Profile>('/api/v1/profile/goals', { method: 'PUT', body: { goals } }),

      zones: () => client.request<Zone[]>('/api/v1/profile/zones'),

      /** Corrección manual. A partir de aquí el valor es definitivo (A1.4). */
      correctZone: (zone: string, field: string, value: unknown) =>
        client.request<Zone>(`/api/v1/profile/zones/${zone}`, {
          method: 'PUT',
          body: { field, value },
        }),

      setDamage: (zone: string, signs: string[]) =>
        client.request<Zone>(`/api/v1/profile/zones/${zone}/damage`, {
          method: 'PUT',
          body: signs,
        }),
    },

    routines: {
      generate: (payload: RoutineRequest) =>
        client.request<Routine>('/api/v1/routines/generate', { method: 'POST', body: payload }),

      techniques: () => client.request<Technique[]>('/api/v1/routines/techniques'),

      forecast: (params: {
        temperature_c: number;
        relative_humidity: number;
        uv_index?: number;
        wind_kph?: number;
      }) => client.request<HairForecast>('/api/v1/routines/weather-forecast', { query: params }),
    },

    scans: {
      requiredAngles: () =>
        client.request<{
          angles: Array<{
            angle: string;
            required: boolean;
            label_key: string;
            covers_zones: string[];
          }>;
          total_zones: number;
        }>('/api/v1/scans/required-angles'),

      create: () => client.request<{ id: string }>('/api/v1/scans', { method: 'POST' }),

      uploadPhoto: (scanId: string, formData: FormData) =>
        client.request<import('./types').PhotoQuality>(`/api/v1/scans/${scanId}/photos`, {
          method: 'POST',
          formData,
        }),

      analyse: (scanId: string) =>
        client.request<ScanResult>(`/api/v1/scans/${scanId}/analyse`, { method: 'POST' }),

      confirm: (scanId: string, corrections?: Record<string, Record<string, unknown>>) =>
        client.request<{ scan_id: string; status: string; outcomes: Record<string, Record<string, string>> }>(
          `/api/v1/scans/${scanId}/confirm`,
          { method: 'POST', body: corrections ?? {} },
        ),
    },

    inventory: {
      list: () =>
        client.request<
          Array<{
            id: string;
            display_name: string;
            category: string | null;
            amount_left_ratio: number;
            disliked: boolean;
            is_usable: boolean;
            expires_on: string | null;
            expired: boolean;
            notes: string | null;
          }>
        >('/api/v1/inventory'),

      add: (payload: {
        product_id?: string;
        custom_name?: string;
        custom_category?: string;
        custom_inci?: string;
        opened_at?: string;
        pao_months?: number;
      }) => client.request<{ id: string }>('/api/v1/inventory', { method: 'POST', body: payload }),

      remove: (itemId: string) =>
        client.request<void>(`/api/v1/inventory/${itemId}`, { method: 'DELETE' }),

      duplicates: () =>
        client.request<Array<{ category: string; count: number; item_ids: string[]; message_key: string }>>(
          '/api/v1/inventory/duplicates',
        ),

      /** Empieza siempre por el inventario, nunca por el catálogo (A15). */
      match: (category: string, wantedAttributes: Record<string, unknown>) =>
        client.request<MatchResult>('/api/v1/inventory/match', {
          method: 'POST',
          body: { category, wanted_attributes: wantedAttributes },
        }),

      scanIngredients: (inci: string) =>
        client.request<{
          ingredients: Array<{ inci_name: string; functions: string[] }>;
          by_function: Record<string, string[]>;
          findings: Array<{
            key: string;
            severity: string;
            function: string | null;
            params: Record<string, unknown>;
          }>;
          declared_sensitivity_matches: string[];
          unrecognised_count: number;
        }>('/api/v1/inventory/scan-ingredients', { method: 'POST', body: { inci } }),

      analyseRoutine: (productIds?: string[]) =>
        client.request<{
          findings: Array<{
            key: string;
            severity: string;
            product_ids: string[];
            params: Record<string, unknown>;
            suggestion_key: string | null;
          }>;
          explanation: import('./types').Explanation;
        }>('/api/v1/inventory/analyse-routine', { method: 'POST', body: productIds ?? [] }),
    },

    journal: {
      list: (limit = 50) => client.request<JournalEntry[]>('/api/v1/journal', { query: { limit } }),

      create: (payload: {
        entry_date: string;
        product_ids?: string[];
        technique_ids?: string[];
        amounts_ml?: Record<string, number>;
        weather?: Record<string, number>;
        ratings?: Record<string, number>;
        notes?: string;
        experiment_arm_id?: string;
      }) => client.request<JournalEntry>('/api/v1/journal', { method: 'POST', body: payload }),

      rate: (entryId: string, ratings: Record<string, number>) =>
        client.request<JournalEntry>(`/api/v1/journal/${entryId}/ratings`, {
          method: 'PUT',
          body: { ratings },
        }),

      insights: () => client.request<Insights>('/api/v1/journal/insights'),

      coldStart: () => client.request<ColdStartGuidance>('/api/v1/journal/cold-start'),

      /** Crecimiento y retención, separados: son cosas distintas (A13). */
      growth: () => client.request<unknown>('/api/v1/journal/growth'),
    },

    twin: {
      read: () => client.request<DigitalTwin>('/api/v1/twin'),

      project: (scenario: string) =>
        client.request<Projection>('/api/v1/twin/project', { query: { scenario } }),

      scenarios: () =>
        client.request<Array<{ scenario: string; label_key: string }>>('/api/v1/twin/scenarios'),

      snapshot: () =>
        client.request<{ id: string; entry_count: number }>('/api/v1/twin/snapshot', {
          method: 'POST',
        }),
    },

    experiments: {
      list: () =>
        client.request<
          Array<{
            id: string;
            question_key: string;
            status: string;
            controlled_variables: string[];
            target_repetitions_per_arm: number;
            arms: Array<{ id: string; label_key: string; product_ids: string[] }>;
          }>
        >('/api/v1/experiments'),

      create: (payload: {
        question_key: string;
        arms: Array<{ label_key: string; product_ids?: string[]; technique_ids?: string[] }>;
        controlled_variables?: string[];
        target_repetitions_per_arm?: number;
        is_premium?: boolean;
      }) =>
        client.request<{ id: string; arm_ids: string[] }>('/api/v1/experiments', {
          method: 'POST',
          body: payload,
        }),

      reading: (experimentId: string) =>
        client.request<{
          experiment_id: string;
          status: string;
          arms: Array<{ arm_id: string; label_key: string; n: number; mean_rating: number }>;
          winner_arm_id: string | null;
          is_distinguishable_from_noise: boolean;
          is_conclusive: boolean;
          protocol_issues: Array<{ key: string; arm_id: string | null }>;
          explanation: import('./types').Explanation;
        }>(`/api/v1/experiments/${experimentId}/reading`),
    },

    education: {
      myths: () => client.request<Myth[]>('/api/v1/education/myths'),

      rules: (evidenceLevel?: string) =>
        client.request<
          Array<{
            id: string;
            kind: string;
            evidence_level: string;
            evidence_label_key: string;
            evidence_confidence: number;
            mechanism: string;
            sources: string[];
            tags: string[];
          }>
        >('/api/v1/education/rules', { query: { evidence_level: evidenceLevel } }),
    },

    billing: {
      entitlements: () => client.request<unknown>('/api/v1/billing/entitlements'),

      check: (feature: string) =>
        client.request<{
          allowed: boolean;
          reason: string;
          used: number;
          limit: number | null;
          remaining: number | null;
          message_key: string;
        }>('/api/v1/billing/check', { query: { feature } }),

      /** El cobro lo hace la tienda; aquí solo se registra el resultado. */
      activate: (params: {
        plan: string;
        store: 'app_store' | 'play_store';
        store_transaction_id: string;
        period_end: string;
        billing_country?: string;
      }) => client.request<unknown>('/api/v1/billing/activate', { method: 'POST', query: params }),

      cancel: () => client.request<unknown>('/api/v1/billing/cancel', { method: 'POST' }),

      plans: () => client.request<unknown>('/api/v1/billing/plans'),
    },

    meta: {
      disclaimer: () =>
        client.request<{
          is_medical_device: boolean;
          message_key: string;
          referral_block_key: string;
        }>('/api/v1/meta/disclaimer'),
    },
  };
}

export type Endpoints = ReturnType<typeof endpoints>;
