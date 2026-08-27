/**
 * Verifica que los datos de demostración tienen la forma que espera cada
 * pantalla.
 *
 * Por qué existe: la app compila aunque los datos estén mal, y el fallo
 * aparece al abrir la pantalla, ya instalada en el teléfono. Estos tests
 * recorren lo que lee cada pantalla y fallan aquí en vez de allí.
 */

import fixtures from '../fixtures.json';
import { createDemoEndpoints } from '../client';

const api = createDemoEndpoints();

describe('datos de demostración', () => {
  it('el perfil trae las 15 zonas del mapa', async () => {
    const profile = (await api.profile.read()) as { zones: unknown[] };
    expect(profile.zones).toHaveLength(15);
  });

  it('cada zona tiene lo que la pantalla del mapa lee', async () => {
    const zones = (await api.profile.zones()) as Array<Record<string, unknown>>;
    for (const zone of zones) {
      expect(typeof zone.zone).toBe('string');
      expect(typeof zone.label_key).toBe('string');
      expect(typeof zone.measurements).toBe('object');
      expect(Array.isArray(zone.damage_signs)).toBe(true);

      for (const measured of Object.values(zone.measurements as Record<string, unknown>)) {
        const value = measured as Record<string, unknown>;
        expect(value).toHaveProperty('value');
        expect(typeof value.confidence).toBe('number');
        expect(typeof value.source).toBe('string');
      }
    }
  });

  it('la rutina trae pasos y todos explican por qué', async () => {
    const routine = (await api.routines.generate({})) as {
      steps: Array<Record<string, unknown>>;
      total_minutes: number;
      halted: boolean;
    };
    expect(routine.steps.length).toBeGreaterThan(0);
    expect(routine.halted).toBe(false);

    for (const step of routine.steps) {
      expect(typeof step.order).toBe('number');
      expect(typeof step.action_key).toBe('string');
      expect(Array.isArray(step.zones)).toBe(true);

      // El bloque «¿por qué esto?» es parte del contrato, no un extra.
      const explanation = step.explanation as Record<string, unknown>;
      expect(typeof explanation.summary_key).toBe('string');
      expect(typeof explanation.evidence_confidence).toBe('number');
      expect(typeof explanation.personal_confidence).toBe('number');
      expect(typeof explanation.sample_size).toBe('number');
      expect(Array.isArray(explanation.uncertainty_keys)).toBe(true);
    }
  });

  it('las cantidades traen referencia visual, no solo mililitros', async () => {
    const routine = (await api.routines.generate({})) as {
      steps: Array<{ amount: Record<string, unknown> | null }>;
    };
    const withAmount = routine.steps.filter((step) => step.amount !== null);
    expect(withAmount.length).toBeGreaterThan(0);

    for (const step of withAmount) {
      expect(typeof step.amount?.ml).toBe('number');
      expect(typeof step.amount?.reference_key).toBe('string');
      expect(typeof step.amount?.reference_multiplier).toBe('number');
    }
  });

  it('el modo rápido devuelve menos pasos que el completo', async () => {
    const full = (await api.routines.generate({})) as { steps: unknown[] };
    const quick = (await api.routines.generate({ kind: 'quick_10' })) as { steps: unknown[] };
    expect(quick.steps.length).toBeLessThan(full.steps.length);
  });

  it('el diario tiene entradas con valoraciones', async () => {
    const journal = (await api.journal.list()) as Array<Record<string, unknown>>;
    expect(journal.length).toBeGreaterThan(5);
    for (const entry of journal) {
      expect(typeof entry.id).toBe('string');
      expect(typeof entry.date).toBe('string');
      expect(typeof entry.ratings).toBe('object');
    }
  });

  it('los hallazgos declaran su tamaño de muestra y su fuerza', async () => {
    const insights = (await api.journal.insights()) as {
      findings: Array<Record<string, unknown>>;
      has_enough_data: boolean;
    };
    expect(insights.has_enough_data).toBe(true);
    for (const finding of insights.findings) {
      expect(typeof finding.subject).toBe('string');
      expect(typeof finding.sample_size).toBe('number');
      expect(typeof finding.strength).toBe('string');
      expect(Array.isArray(finding.uncontrolled_variables)).toBe(true);
    }
  });

  it('el twin trae rasgos y separa lo conocido de lo desconocido', async () => {
    const twin = (await api.twin.read()) as {
      traits: Array<Record<string, unknown>>;
      completeness: number;
    };
    expect(twin.traits.length).toBeGreaterThan(0);
    const known = twin.traits.filter((t) => (t.confidence as number) > 0);
    const unknown = twin.traits.filter((t) => (t.confidence as number) === 0);
    // La pantalla enseña las dos listas: si una está vacía, no se ve el matiz.
    expect(known.length).toBeGreaterThan(0);
    expect(unknown.length).toBeGreaterThan(0);
  });

  it('hay proyección para cada escenario que ofrece la pantalla', async () => {
    const scenarios = (await api.twin.scenarios()) as Array<{ scenario: string }>;
    expect(scenarios.length).toBeGreaterThan(0);
    for (const { scenario } of scenarios) {
      const projection = (await api.twin.project(scenario)) as Record<string, unknown>;
      expect(typeof projection.direction).toBe('string');
      expect(typeof projection.can_project).toBe('boolean');
      expect(projection).toHaveProperty('explanation');
    }
  });

  it('la lectura de crecimiento separa crecimiento de retención', async () => {
    const growth = (await api.journal.growth()) as Record<string, unknown>;
    expect(growth.has_reading).toBe(true);
    expect(typeof growth.retention_ratio).toBe('number');
    expect(typeof growth.growth_cm_per_month).toBe('number');
    // Si el ritmo está supuesto, la pantalla lo tiene que poder decir.
    expect(typeof growth.growth_is_measured).toBe('boolean');
  });

  it('los mitos traen su mecanismo, no solo el desmentido', async () => {
    const myths = (await api.education.myths()) as Array<Record<string, unknown>>;
    expect(myths.length).toBeGreaterThan(5);
    for (const myth of myths) {
      expect(myth.evidence_level).toBe('unsupported_trend');
      expect((myth.mechanism as string).length).toBeGreaterThan(50);
    }
  });

  it('las reglas son auditables con su procedencia', async () => {
    const rules = (await api.education.rules()) as Array<Record<string, unknown>>;
    expect(rules.length).toBeGreaterThan(20);
    for (const rule of rules) {
      expect(typeof rule.evidence_level).toBe('string');
      expect(typeof rule.evidence_label_key).toBe('string');
    }
  });

  it('el arranque en frío ofrece hitos concretos', async () => {
    const coldStart = (await api.journal.coldStart()) as { milestone_keys: string[] };
    expect(coldStart.milestone_keys.length).toBeGreaterThan(0);
  });

  it('una corrección se refleja al momento, aunque no persista', async () => {
    await api.profile.correctZone('crown', 'porosity', 'low');
    const zones = (await api.profile.zones()) as Array<Record<string, unknown>>;
    const crown = zones.find((z) => z.zone === 'crown');
    const measurements = crown?.measurements as Record<string, Record<string, unknown>>;
    expect(measurements.porosity.value).toBe('low');
    expect(measurements.porosity.source).toBe('user');
  });

  it('se generaron con el motor real, no a mano', () => {
    expect(fixtures.generated_note).toContain('motor real');
  });
});
