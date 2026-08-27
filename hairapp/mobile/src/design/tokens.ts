/**
 * Tokens del design system.
 *
 * Regla: los componentes **nunca** usan valores crudos. Si algo necesita un
 * color, un espacio o un tamaño de texto, sale de aquí. Es lo que hace posible
 * que el modo oscuro sea real y no un filtro aplicado por encima.
 *
 * Estética objetivo (A19): editorial, sobria, sin género. Sin gradientes
 * decorativos, sin emojis como iconografía, sin rosa por defecto, sin aspecto
 * de panel de control empresarial.
 */

export const spacing = {
  none: 0,
  xxs: 2,
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
  xxxl: 48,
  huge: 64,
} as const;

export type SpacingToken = keyof typeof spacing;

export const radius = {
  none: 0,
  sm: 4,
  md: 8,
  lg: 14,
  xl: 20,
  pill: 999,
} as const;

/**
 * Escala tipográfica editorial. Los tamaños siguen una progresión ~1.22, que
 * da suficiente contraste entre niveles sin saltos bruscos.
 *
 * `display` usa una serif por defecto: es lo que separa visualmente un
 * producto editorial de un panel de datos.
 */
export const typography = {
  display: { fontSize: 34, lineHeight: 40, letterSpacing: -0.6, fontWeight: '400' },
  title: { fontSize: 26, lineHeight: 32, letterSpacing: -0.4, fontWeight: '500' },
  heading: { fontSize: 20, lineHeight: 26, letterSpacing: -0.2, fontWeight: '600' },
  subheading: { fontSize: 17, lineHeight: 23, letterSpacing: -0.1, fontWeight: '600' },
  body: { fontSize: 16, lineHeight: 24, letterSpacing: 0, fontWeight: '400' },
  bodyStrong: { fontSize: 16, lineHeight: 24, letterSpacing: 0, fontWeight: '600' },
  callout: { fontSize: 15, lineHeight: 21, letterSpacing: 0, fontWeight: '400' },
  caption: { fontSize: 13, lineHeight: 18, letterSpacing: 0.1, fontWeight: '400' },
  overline: { fontSize: 11, lineHeight: 15, letterSpacing: 1.1, fontWeight: '600' },
  mono: { fontSize: 14, lineHeight: 20, letterSpacing: 0, fontWeight: '400' },
} as const;

export type TypographyToken = keyof typeof typography;

/**
 * Paleta base. Neutros cálidos en vez de grises puros: leen como papel, no como
 * interfaz de sistema. El acento es un verde apagado, deliberadamente neutro en
 * cuanto a género y poco saturado para no competir con el contenido.
 */
const palette = {
  ink900: '#16150F',
  ink800: '#26241C',
  ink700: '#3A362B',
  ink500: '#6B6558',
  ink400: '#8C8577',
  ink300: '#B3AC9E',
  paper000: '#FFFFFF',
  paper050: '#FAF8F5',
  paper100: '#F2EFE9',
  paper200: '#E6E2D9',
  paper300: '#D6D1C5',
  night900: '#111110',
  night800: '#1A1A18',
  night700: '#232320',
  night600: '#2E2E2A',
  night500: '#3C3B36',
  accent600: '#3F6B54',
  accent500: '#4E8468',
  accent400: '#6FA187',
  accent200: '#B9D2C4',
  warn600: '#8A5A22',
  warn400: '#C08A46',
  warn200: '#EFD9B8',
  alert600: '#8C3B31',
  alert400: '#BE6255',
  positive600: '#3F6B54',
} as const;

/** Tokens semánticos: lo que los componentes consumen. */
export interface ThemeColors {
  background: string;
  surface: string;
  surfaceRaised: string;
  surfaceSunken: string;
  ink: string;
  inkStrong: string;
  inkMuted: string;
  inkFaint: string;
  line: string;
  lineStrong: string;
  accent: string;
  accentInk: string;
  accentSoft: string;
  warn: string;
  warnSoft: string;
  warnInk: string;
  alert: string;
  alertInk: string;
  positive: string;
  overlay: string;
}

export const lightColors: ThemeColors = {
  background: palette.paper050,
  surface: palette.paper000,
  surfaceRaised: palette.paper000,
  surfaceSunken: palette.paper100,
  ink: palette.ink800,
  inkStrong: palette.ink900,
  inkMuted: palette.ink500,
  inkFaint: palette.ink400,
  line: palette.paper200,
  lineStrong: palette.paper300,
  accent: palette.accent600,
  accentInk: palette.paper000,
  accentSoft: palette.accent200,
  warn: palette.warn600,
  warnSoft: palette.warn200,
  warnInk: palette.paper000,
  alert: palette.alert600,
  alertInk: palette.paper000,
  positive: palette.positive600,
  overlay: 'rgba(22, 21, 15, 0.45)',
};

export const darkColors: ThemeColors = {
  background: palette.night900,
  surface: palette.night800,
  surfaceRaised: palette.night700,
  surfaceSunken: palette.night900,
  ink: palette.paper100,
  inkStrong: palette.paper000,
  inkMuted: palette.ink300,
  inkFaint: palette.ink400,
  line: palette.night600,
  lineStrong: palette.night500,
  accent: palette.accent400,
  accentInk: palette.night900,
  accentSoft: palette.accent600,
  warn: palette.warn400,
  warnSoft: palette.warn600,
  warnInk: palette.night900,
  alert: palette.alert400,
  alertInk: palette.night900,
  positive: palette.accent400,
  overlay: 'rgba(0, 0, 0, 0.6)',
};

/**
 * Objetivos de accesibilidad (A18). No son decorativos: hay un test que
 * comprueba el contraste real de los pares que se usan como texto.
 */
export const contrastTargets = {
  bodyTextMinimum: 4.5,
  largeTextMinimum: 3.0,
  nonTextMinimum: 3.0,
} as const;

/** Tamaños mínimos de área táctil, según las guías de ambas plataformas. */
export const touchTarget = {
  minimum: 44,
  comfortable: 48,
} as const;

export const durations = {
  instant: 0,
  fast: 120,
  normal: 200,
  slow: 320,
} as const;
