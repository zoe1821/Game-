import { catalogs, SUPPORTED_LOCALES } from '../index';

function flatten(node: unknown, prefix = ''): string[] {
  if (node === null || typeof node !== 'object') {
    return [prefix];
  }
  return Object.entries(node as Record<string, unknown>).flatMap(([key, value]) =>
    flatten(value, prefix ? `${prefix}.${key}` : key),
  );
}

describe('catálogos i18n', () => {
  const keysByLocale = Object.fromEntries(
    SUPPORTED_LOCALES.map((locale) => [locale, flatten(catalogs[locale]).sort()]),
  ) as Record<string, string[]>;

  it('todos los idiomas tienen exactamente las mismas claves', () => {
    const reference = keysByLocale.es;
    for (const locale of SUPPORTED_LOCALES) {
      expect({ locale, keys: keysByLocale[locale] }).toEqual({ locale, keys: reference });
    }
  });

  it('ninguna cadena está vacía', () => {
    for (const locale of SUPPORTED_LOCALES) {
      const empty = flatten(catalogs[locale]).filter((key) => {
        const value = key
          .split('.')
          .reduce<unknown>((node, part) => (node as Record<string, unknown>)?.[part], catalogs[locale]);
        return typeof value === 'string' && value.trim() === '';
      });
      expect({ locale, empty }).toEqual({ locale, empty: [] });
    }
  });

  it('las interpolaciones coinciden entre idiomas', () => {
    const placeholders = (value: unknown): string[] =>
      typeof value === 'string' ? [...value.matchAll(/%\{(\w+)\}/g)].map((m) => m[1] as string).sort() : [];

    for (const key of keysByLocale.es as string[]) {
      const read = (locale: string): unknown =>
        key.split('.').reduce<unknown>((node, part) => (node as Record<string, unknown>)?.[part], catalogs[locale as keyof typeof catalogs]);
      const reference = placeholders(read('es'));
      for (const locale of SUPPORTED_LOCALES) {
        expect({ key, locale, placeholders: placeholders(read(locale)) }).toEqual({
          key,
          locale,
          placeholders: reference,
        });
      }
    }
  });
});
