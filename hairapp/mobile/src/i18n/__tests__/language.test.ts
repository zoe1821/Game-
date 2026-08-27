/**
 * El glosario de lenguaje controlado, aplicado al cliente (requisito B6).
 *
 * El backend tiene su propio checker sobre las reglas; este cubre el otro
 * sitio donde vive texto de usuario: los catálogos i18n. Si un término con
 * implicación médica llega a la interfaz, el build falla.
 */

import { catalogs, SUPPORTED_LOCALES } from '../index';

/** Espejo de `backend/app/data/controlled_language.yaml`. */
const BLOCKED_TERMS = [
  'dermatitis',
  'seborrea',
  'seborreica',
  'psoriasis',
  'alopecia',
  'calvicie',
  'foliculitis',
  'infeccion',
  'hongos',
  'diagnostico',
  'diagnosticar',
  'diagnostica',
  'diagnose',
  'diagnoses',
  'diagnosis',
  'curar',
  'sanar',
  'regenerar',
  'detox',
  'desintoxicar',
  'garantizado',
  'guaranteed',
  'clinically proven',
  'clinicamente probado',
  'cure',
  'heal',
];

/**
 * Claves exentas: las que niegan explícitamente que la app haga valoración
 * médica. Son las únicas donde nombrar el acto médico es correcto.
 */
const EXEMPT_PREFIXES = ['safety.', 'meta.'];

/** Términos que sugieren género donde no debe haberlo (A19). */
const GENDERED_TERMS = ['chicas', 'chicos', 'guapa', 'guapo', 'reina', 'girls', 'ladies', 'queen'];

function stripAccents(value: string): string {
  return value.normalize('NFD').replace(/[̀-ͯ]/g, '');
}

function collectStrings(node: unknown, prefix = ''): Array<[string, string]> {
  if (typeof node === 'string') {
    return [[prefix, node]];
  }
  if (node === null || typeof node !== 'object') {
    return [];
  }
  return Object.entries(node as Record<string, unknown>).flatMap(([key, value]) =>
    collectStrings(value, prefix ? `${prefix}.${key}` : key),
  );
}

describe('lenguaje controlado en la interfaz', () => {
  const entries = SUPPORTED_LOCALES.flatMap((locale) =>
    collectStrings(catalogs[locale]).map(([key, value]) => ({ locale, key, value })),
  );

  it.each(BLOCKED_TERMS)('no aparece el término bloqueado «%s»', (term) => {
    const offenders = entries.filter(({ key, value }) => {
      // Las claves exentas son las que **niegan** la capacidad médica: el
      // bloque de derivación y el aviso de app cosmética. «No diagnostica» es
      // precisamente la redacción que exige el cumplimiento normativo
      // (docs/04-LEGAL-CHECKLIST.md §1); prohibirla sería contraproducente.
      if (EXEMPT_PREFIXES.some((prefix) => key.startsWith(prefix))) {
        return false;
      }
      const haystack = stripAccents(value.toLowerCase());
      return new RegExp(`(?<!\\w)${stripAccents(term)}(?!\\w)`).test(haystack);
    });
    expect(offenders.map((o) => `${o.locale}:${o.key}`)).toEqual([]);
  });

  it.each(GENDERED_TERMS)('no aparece el término generizado «%s»', (term) => {
    const offenders = entries.filter(({ value }) =>
      new RegExp(`(?<!\\w)${term}(?!\\w)`).test(stripAccents(value.toLowerCase())),
    );
    expect(offenders.map((o) => `${o.locale}:${o.key}`)).toEqual([]);
  });

  it('el bloque de derivación deriva sin interpretar', () => {
    for (const locale of SUPPORTED_LOCALES) {
      const block = catalogs[locale].safety.referralBlock.toLowerCase();
      expect(block.length).toBeGreaterThan(80);
      // Deriva a alguien, y dice que no puede estimar.
      expect(/profesional|professional/.test(block)).toBe(true);
    }
  });

  it('el aviso de app cosmética está presente en ambos idiomas', () => {
    for (const locale of SUPPORTED_LOCALES) {
      expect(catalogs[locale].meta.cosmetic_educational_only.length).toBeGreaterThan(40);
    }
  });
});
