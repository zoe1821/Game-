import fixtures from './fixtures.json';

import type { Endpoints } from '@/api/endpoints';

/**
 * Modo demostración: la app funciona sin servidor.
 *
 * Existe por una razón concreta y no por comodidad de desarrollo: para poder
 * ver la app funcionando hace falta, si no, levantar un backend, y eso deja
 * fuera a cualquiera que solo tenga el teléfono.
 *
 * **Los datos no están escritos a mano.** Se generan ejecutando el motor real
 * (`backend/scripts/generate_demo_fixtures.py`) y congelando su salida, así
 * que las rutinas, las explicaciones, las confianzas y las incertidumbres que
 * se ven aquí son exactamente las que produce el sistema. Si el motor cambia,
 * se regeneran y la demostración cambia con él.
 *
 * Lo que **no** hace: escribir. Las mutaciones se aceptan y se reflejan en
 * memoria durante la sesión, pero no persisten. La app avisa de que está en
 * modo demostración; no se finge que se guardó algo que no se guardó.
 */

const delay = <T,>(value: T, ms = 180): Promise<T> =>
  new Promise((resolve) => setTimeout(() => resolve(value), ms));

/** Estado en memoria: se pierde al cerrar. Es honesto y suficiente para ver. */
interface DemoState {
  journal: unknown[];
  zones: unknown[];
}

export function createDemoEndpoints(): Endpoints {
  const state: DemoState = {
    journal: [...(fixtures.journal as unknown[])],
    zones: [...(fixtures.zones as unknown[])],
  };

  const notPersisted = <T,>(value: T): Promise<T> => delay(value);

  return {
    auth: {
      register: () => notPersisted({ access_token: 'demo', refresh_token: 'demo', token_type: 'bearer' }),
      login: () => notPersisted({ access_token: 'demo', refresh_token: 'demo', token_type: 'bearer' }),
      logout: () => notPersisted(undefined),
      me: () =>
        notPersisted({
          id: 'demo',
          email: 'demo@trichon.app',
          locale: 'es',
          depth_level: 'intermediate',
          profile_completeness: 0.68,
          consents: [
            { purpose: 'terms', granted: true, version: 1, granted_at: null, revoked_at: null },
            { purpose: 'privacy', granted: true, version: 1, granted_at: null, revoked_at: null },
          ],
        }),
      setConsents: (consents: Array<{ purpose: string; granted: boolean }>) =>
        notPersisted(
          consents.map((c: { purpose: string; granted: boolean }) => ({
            purpose: c.purpose,
            granted: c.granted,
            version: 1,
            granted_at: null,
            revoked_at: null,
          })),
        ),
      deleteAccount: () => notPersisted(undefined),
    },

    profile: {
      read: () => notPersisted(fixtures.profile),
      essentialOnboarding: () => notPersisted(fixtures.profile),
      deepOnboarding: () => notPersisted(fixtures.profile),
      setDepthLevel: () => notPersisted(fixtures.profile),
      setGoals: () => notPersisted(fixtures.profile),
      zones: () => notPersisted(state.zones),
      correctZone: (zone: string, field: string, value: unknown) => {
        // Se refleja en memoria para que la corrección se vea, aunque no
        // sobreviva a cerrar la app.
        const target = (state.zones as Array<Record<string, unknown>>).find(
          (z) => z.zone === zone,
        );
        if (target) {
          const measurements = target.measurements as Record<string, unknown>;
          measurements[field] = {
            value,
            confidence: 1,
            source: 'user',
            observed_at: null,
            notes: null,
          };
        }
        return notPersisted(target);
      },
      setDamage: (zone: string) =>
        notPersisted(
          (state.zones as Array<Record<string, unknown>>).find((z) => z.zone === zone),
        ),
    },

    routines: {
      generate: (payload: { kind?: string }) =>
        notPersisted(
          payload.kind && payload.kind.startsWith('quick')
            ? fixtures.routine_quick
            : fixtures.routine,
        ),
      techniques: () => notPersisted([]),
      forecast: () => notPersisted(fixtures.forecast),
    },

    scans: {
      requiredAngles: () => notPersisted({ angles: [], total_zones: 15 }),
      create: () => notPersisted({ id: 'demo-scan' }),
      uploadPhoto: () =>
        notPersisted({
          angle: 'front',
          score: 0.9,
          must_retake: false,
          issues: [],
          metrics: {},
        }),
      analyse: () => notPersisted({}),
      confirm: () => notPersisted({ scan_id: 'demo-scan', status: 'confirmed', outcomes: {} }),
    },

    inventory: {
      list: () => notPersisted([]),
      add: () => notPersisted({ id: 'demo-item' }),
      remove: () => notPersisted(undefined),
      duplicates: () => notPersisted([]),
      match: () => notPersisted({}),
      scanIngredients: () => notPersisted({}),
      analyseRoutine: () => notPersisted({}),
    },

    journal: {
      list: () => notPersisted(state.journal),
      create: (payload: Record<string, never> & { entry_date: string; product_ids?: string[]; technique_ids?: string[]; amounts_ml?: Record<string, number>; weather?: Record<string, number>; ratings?: Record<string, number>; notes?: string }) => {
        const entry = {
          id: `demo-${state.journal.length}`,
          date: payload.entry_date,
          product_ids: payload.product_ids ?? [],
          technique_ids: payload.technique_ids ?? [],
          amounts_ml: payload.amounts_ml ?? {},
          weather: payload.weather ?? {},
          ratings: payload.ratings ?? {},
          notes: payload.notes ?? null,
          experiment_arm_id: null,
          longevity_days: 0,
        };
        state.journal = [entry, ...state.journal];
        return notPersisted(entry);
      },
      rate: (entryId: string, ratings: Record<string, number>) => {
        const entry = (state.journal as Array<Record<string, unknown>>).find(
          (e) => e.id === entryId,
        );
        if (entry) {
          entry.ratings = { ...(entry.ratings as object), ...ratings };
        }
        return notPersisted(entry);
      },
      insights: () => notPersisted(fixtures.insights),
      coldStart: () => notPersisted(fixtures.cold_start),
      growth: () => notPersisted(fixtures.growth),
    },

    twin: {
      read: () => notPersisted(fixtures.twin),
      project: (scenario: string) =>
        notPersisted(
          (fixtures.projections as Record<string, unknown>)[scenario] ??
            (fixtures.projections as Record<string, unknown>).higher_humidity,
        ),
      scenarios: () =>
        notPersisted(
          Object.keys(fixtures.projections as Record<string, unknown>).map((scenario) => ({
            scenario,
            label_key: `twin.scenario.${scenario}`,
          })),
        ),
      snapshot: () => notPersisted({ id: 'demo', entry_count: 12 }),
    },

    experiments: {
      list: () => notPersisted([]),
      create: () => notPersisted({ id: 'demo', arm_ids: [] }),
      reading: () => notPersisted({}),
    },

    education: {
      myths: () => notPersisted(fixtures.myths),
      rules: () => notPersisted(fixtures.rules),
    },

    billing: {
      entitlements: () =>
        notPersisted({
          plan: 'free',
          plan_label_key: 'plan.free',
          renews: false,
          period_start: new Date().toISOString().slice(0, 10),
          period_end: new Date().toISOString().slice(0, 10),
          features: [],
          always_included: [
            { feature: 'journal_entry', label_key: 'feature.journal_entry' },
            { feature: 'explanation', label_key: 'feature.explanation' },
            { feature: 'data_export', label_key: 'feature.data_export' },
          ],
        }),
      check: () =>
        notPersisted({
          allowed: true,
          reason: 'allowed',
          used: 0,
          limit: null,
          remaining: null,
          message_key: 'entitlement.allowed',
        }),
      activate: () => notPersisted({}),
      cancel: () => notPersisted({}),
      plans: () => notPersisted([]),
    },

    meta: {
      disclaimer: () =>
        notPersisted({
          is_medical_device: false,
          message_key: 'meta.cosmetic_educational_only',
          referral_block_key: 'safety.referral_block',
        }),
    },
  } as unknown as Endpoints;
}
