import { I18n } from 'i18n-js';

import { en } from './en';
import { es, type Catalog } from './es';

export const SUPPORTED_LOCALES = ['es', 'en'] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];

export const DEFAULT_LOCALE: Locale = 'es';

export const catalogs: Record<Locale, Catalog> = { es, en };

export const i18n = new I18n({ es, en });
i18n.defaultLocale = DEFAULT_LOCALE;
i18n.locale = DEFAULT_LOCALE;
i18n.enableFallback = true;

export function setLocale(locale: string | null | undefined): Locale {
  const normalised = (locale ?? '').slice(0, 2).toLowerCase();
  const resolved = (SUPPORTED_LOCALES as readonly string[]).includes(normalised)
    ? (normalised as Locale)
    : DEFAULT_LOCALE;
  i18n.locale = resolved;
  return resolved;
}

export type TranslateOptions = Record<string, string | number>;

/**
 * Traduce una clave.
 *
 * En desarrollo, una clave que no existe se marca de forma llamativa en lugar
 * de mostrarse tal cual: un `routine.stepTitle.cleanse` colado en la pantalla
 * es un fallo que hay que ver, no un texto aceptable.
 */
export function t(key: string, options?: TranslateOptions): string {
  const translated = i18n.t(key, options);
  if (typeof translated === 'string' && translated.startsWith('[missing')) {
    if (__DEV__) {
      return `⟪${key}⟫`;
    }
    return '';
  }
  return String(translated);
}

/**
 * Traduce una clave que llega del backend.
 *
 * El backend nunca manda texto de interfaz: manda claves (A18). Si una clave
 * es desconocida se cae a un mensaje genérico en vez de enseñar el
 * identificador crudo.
 */
export function tKey(key: string | null | undefined, options?: TranslateOptions): string {
  if (!key) {
    return t('error.generic');
  }
  const translated = i18n.t(key, options);
  if (typeof translated === 'string' && translated.startsWith('[missing')) {
    return __DEV__ ? `⟪${key}⟫` : t('error.generic');
  }
  return String(translated);
}

/** Pluralización del tamaño de muestra, que aparece en todas las explicaciones. */
export function sampleSizeLabel(count: number): string {
  if (count <= 0) {
    return t('confidence.sampleSize.zero');
  }
  if (count === 1) {
    return t('confidence.sampleSize.one');
  }
  return t('confidence.sampleSize.other', { count });
}
