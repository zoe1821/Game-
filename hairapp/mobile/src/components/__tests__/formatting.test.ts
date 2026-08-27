import { sampleSizeLabel, setLocale, t, tKey } from '@/i18n';

describe('traducción de claves del backend', () => {
  afterEach(() => setLocale('es'));

  it('resuelve una clave conocida en cada idioma', () => {
    setLocale('es');
    expect(tKey('evidence.scientific_evidence')).toBe('Evidencia científica');
    setLocale('en');
    expect(tKey('evidence.scientific_evidence')).toBe('Scientific evidence');
  });

  it('una clave vacía cae al error genérico', () => {
    setLocale('es');
    expect(tKey(null)).toBe(t('error.generic'));
    expect(tKey(undefined)).toBe(t('error.generic'));
  });

  it('interpola parámetros', () => {
    setLocale('es');
    expect(t('home.profileCompleteness', { percent: 42 })).toContain('42');
  });

  it('un idioma no soportado cae al de origen', () => {
    expect(setLocale('de')).toBe('es');
    expect(setLocale('fr-CA')).toBe('es');
    expect(setLocale(null)).toBe('es');
  });

  it('reconoce las variantes regionales del idioma soportado', () => {
    expect(setLocale('en-GB')).toBe('en');
    expect(setLocale('es-MX')).toBe('es');
  });
});

describe('etiqueta de tamaño de muestra', () => {
  beforeEach(() => setLocale('es'));

  it('distingue cero, uno y varios', () => {
    // El tamaño de muestra viaja en toda explicación: si se pluralizara mal,
    // se leería como descuido justo en lo que da credibilidad al producto.
    expect(sampleSizeLabel(0)).toContain('Todavía');
    expect(sampleSizeLabel(1)).toContain('1');
    expect(sampleSizeLabel(14)).toContain('14');
    expect(sampleSizeLabel(1)).not.toBe(sampleSizeLabel(14));
  });

  it('trata un valor negativo como cero', () => {
    expect(sampleSizeLabel(-3)).toBe(sampleSizeLabel(0));
  });
});
