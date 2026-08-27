/**
 * Comprueba que existen las claves que las pantallas construyen al vuelo.
 *
 * Las pantallas hacen cosas como `t(\`zone.${zone}\`)` o
 * `tKey(step.explanation.summary_key)`. Una clave que falta no rompe la app:
 * deja un hueco vacío, que es peor, porque parece un fallo sin serlo y nadie
 * sabe qué debería poner ahí.
 *
 * Este test recorre los datos reales que la app va a mostrar y verifica que
 * cada clave que va a pedir existe en los dos idiomas.
 */

import fixtures from '@/demo/fixtures.json';
import { catalogs, SUPPORTED_LOCALES } from '../index';

function exists(locale: string, key: string): boolean {
  const value = key
    .split('.')
    .reduce<unknown>(
      (node, part) => (node as Record<string, unknown> | undefined)?.[part],
      catalogs[locale as keyof typeof catalogs],
    );
  return typeof value === 'string' && value.length > 0;
}

function expectKeys(keys: Iterable<string>, label: string): void {
  const missing: string[] = [];
  for (const key of new Set(keys)) {
    for (const locale of SUPPORTED_LOCALES) {
      if (!exists(locale, key)) {
        missing.push(`${locale}:${key}`);
      }
    }
  }
  expect({ label, missing }).toEqual({ label, missing: [] });
}

describe('claves construidas al vuelo por las pantallas', () => {
  it('todas las zonas del mapa tienen nombre', () => {
    const zones = fixtures.zones as Array<{ zone: string; label_key: string }>;
    expectKeys(
      zones.flatMap((z) => [z.label_key, `zone.${z.zone}`]),
      'zonas',
    );
  });

  it('cada propiedad medida tiene etiqueta', () => {
    const zones = fixtures.zones as Array<{ measurements: Record<string, unknown> }>;
    expectKeys(
      zones.flatMap((z) => Object.keys(z.measurements).map((f) => `zoneDetail.fields.${f}`)),
      'propiedades',
    );
  });

  it('cada paso de la rutina tiene título', () => {
    const routine = fixtures.routine as { steps: Array<{ action_key: string }> };
    expectKeys(
      routine.steps.map((s) => `routine.stepTitle.${s.action_key.replace('step.', '')}`),
      'pasos',
    );
  });

  it('cada referencia de cantidad tiene traducción', () => {
    const routine = fixtures.routine as {
      steps: Array<{ amount: { reference_key: string } | null }>;
    };
    expectKeys(
      routine.steps
        .filter((s) => s.amount !== null)
        .map((s) => s.amount!.reference_key),
      'cantidades',
    );
  });

  it('cada incertidumbre que se va a mostrar tiene texto', () => {
    const routine = fixtures.routine as {
      steps: Array<{ explanation: { uncertainty_keys: string[] } }>;
    };
    const twin = fixtures.projections as Record<
      string,
      { explanation: { uncertainty_keys: string[] } }
    >;
    const insights = fixtures.insights as {
      findings: Array<{ explanation: { uncertainty_keys: string[] } }>;
    };
    expectKeys(
      [
        ...routine.steps.flatMap((s) => s.explanation.uncertainty_keys),
        ...Object.values(twin).flatMap((p) => p.explanation.uncertainty_keys),
        ...insights.findings.flatMap((f) => f.explanation.uncertainty_keys),
      ],
      'incertidumbres',
    );
  });

  it('cada nivel de evidencia tiene nombre', () => {
    const rules = fixtures.rules as Array<{ evidence_level: string }>;
    expectKeys(
      rules.map((r) => `evidence.${r.evidence_level}`),
      'evidencia',
    );
  });

  it('cada objetivo del perfil tiene nombre', () => {
    const profile = fixtures.profile as { goals: string[] };
    expectKeys(
      profile.goals.map((g) => `goal.${g}`),
      'objetivos',
    );
  });

  it('cada rasgo y escenario del twin tiene nombre', () => {
    const twin = fixtures.twin as { traits: Array<{ key: string }> };
    const projections = fixtures.projections as Record<string, { direction: string }>;
    expectKeys(
      [
        ...twin.traits.map((t) => `twin.trait.${t.key}`),
        ...Object.keys(projections).map((s) => `twin.scenario.${s}`),
        ...Object.values(projections).map((p) => `twin.direction.${p.direction}`),
      ],
      'twin',
    );
  });

  it('cada hito del arranque en frío tiene texto', () => {
    const coldStart = fixtures.cold_start as { milestone_keys: string[]; message_key: string };
    expectKeys([...coldStart.milestone_keys, coldStart.message_key], 'hitos');
  });

  it('cada consejo del pronóstico tiene texto', () => {
    const forecast = fixtures.forecast as { advice_keys: string[]; band: string };
    expectKeys([...forecast.advice_keys, `weather.band.${forecast.band}`], 'clima');
  });

  it('cada variable sin controlar de los hallazgos tiene explicación', () => {
    const insights = fixtures.insights as {
      findings: Array<{ uncontrolled_variables: string[]; strength: string }>;
    };
    expectKeys(
      [
        ...insights.findings.flatMap((f) =>
          f.uncontrolled_variables.map((v) => `learning.uncontrolled.${v}`),
        ),
        ...insights.findings.map((f) => `learning.strength.${f.strength}`),
      ],
      'variables',
    );
  });

  it('las pistas del growth tracker tienen texto', () => {
    const growth = fixtures.growth as { explanation?: { uncertainty_keys: string[] } };
    expectKeys(growth.explanation?.uncertainty_keys ?? [], 'crecimiento');
  });
});
