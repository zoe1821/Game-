/**
 * Tipos del contrato con la API.
 *
 * Se escriben a mano para poder documentar por qué cada campo existe; en
 * producción se generarían del OpenAPI que ya publica el backend
 * (`/openapi.json`) y este archivo pasaría a ser el punto de comprobación.
 */

/** El bloque «¿por qué esto?». Acompaña a toda recomendación (A21). */
export interface Explanation {
  summary_key: string;
  inputs_used: string[];
  observations: string[];
  evidence_level: EvidenceLevel;
  /** Qué tan sólida es la regla en general. */
  evidence_confidence: number;
  /** Cuántos datos propios la respaldan. Nunca se promedia con la anterior. */
  personal_confidence: number;
  sample_size: number;
  uncertainty_keys: string[];
  alternatives: string[];
  params: Record<string, unknown>;
}

export type EvidenceLevel =
  | 'scientific_evidence'
  | 'professional_consensus'
  | 'extended_anecdote'
  | 'unsupported_trend';

export type MeasurementSource =
  | 'user'
  | 'ai_vision'
  | 'inferred'
  | 'reference_profile'
  | 'default';

export interface Measured {
  value: string | number | boolean;
  confidence: number;
  source: MeasurementSource;
  observed_at: string | null;
  notes: string | null;
}

export interface Zone {
  zone: string;
  label_key: string;
  measurements: Record<string, Measured>;
  damage_signs: string[];
  notes: string | null;
  completeness: number;
}

export interface Profile {
  id: string;
  depth_level: DepthLevel;
  completeness: number;
  onboarding_essential_done: boolean;
  wash_frequency_days: number | null;
  country: string | null;
  water_hardness_ppm: number | null;
  uses_heat: boolean;
  owns_diffuser: boolean;
  protective_style: string;
  goals: string[];
  zones: Zone[];
}

export type DepthLevel = 'basic' | 'intermediate' | 'advanced';

export interface Amount {
  ml: number;
  reference_key: string;
  reference_multiplier: number;
  zone: string | null;
}

export interface RoutineStep {
  order: number;
  stage: string;
  action_key: string;
  zones: string[];
  product_category: string | null;
  product_attributes: Record<string, unknown>;
  amount: Amount | null;
  technique_id: string | null;
  technique_steps: string[];
  follow_up_technique_ids: string[];
  params: Record<string, unknown>;
  duration_seconds: number | null;
  explanation: Explanation;
}

export interface Routine {
  kind: string;
  /** True cuando una señal de derivación detuvo el análisis (A23). */
  halted: boolean;
  halt_block_key: string | null;
  total_minutes: number;
  steps: RoutineStep[];
  warnings: Explanation[];
  education: Explanation[];
  /** Lo que se dejó fuera por tiempo. Nunca se recorta en silencio. */
  skipped_reason_keys: string[];
}

export interface PhotoQuality {
  angle: string;
  score: number;
  must_retake: boolean;
  issues: Array<{ code: string; message_key: string; blocking: boolean }>;
  metrics: Record<string, number>;
}

export interface ScanStage {
  stage: string;
  status: 'ok' | 'skipped' | 'unavailable';
  reason_key: string | null;
  detail: string | null;
}

export interface ScanResult {
  quality: {
    photos: PhotoQuality[];
    angles_to_retake: string[];
    missing_required_angles: string[];
    mean_score: number;
    is_complete: boolean;
  };
  stages: ScanStage[];
  observations: Array<{
    zone: string;
    observed: boolean;
    source_angles: string[];
    quality_score: number;
    not_observed_reason_key: string | null;
  }>;
  /** False mientras no exista un modelo de segmentación real. */
  used_image_analysis: boolean;
  requires_user_confirmation: boolean;
  estimates: Record<string, Record<string, Measured>>;
  explanation: Explanation;
}

export interface JournalEntry {
  id: string;
  date: string;
  product_ids: string[];
  technique_ids: string[];
  amounts_ml: Record<string, number>;
  weather: Record<string, number>;
  ratings: Record<string, number>;
  notes: string | null;
  experiment_arm_id: string | null;
  longevity_days: number;
}

export interface Finding {
  subject: string;
  kind: string;
  with_mean: number;
  without_mean: number;
  with_n: number;
  without_n: number;
  sample_size: number;
  difference: number;
  effect_size: number;
  strength: 'insufficient_data' | 'suggestive' | 'consistent' | 'strong';
  is_actionable: boolean;
  uncontrolled_variables: string[];
  explanation: Explanation;
}

export interface Insights {
  entry_count: number;
  findings: Finding[];
  has_enough_data: boolean;
  message_key: string;
}

export interface Trait {
  key: string;
  value: number;
  confidence: number;
  sample_size: number;
  based_on: string[];
  is_controlled: boolean;
  last_updated: string | null;
}

export interface DigitalTwin {
  profile_id: string;
  entry_count: number;
  completeness: number;
  traits: Trait[];
}

export interface Projection {
  scenario: string;
  direction: 'likely_better' | 'likely_worse' | 'likely_similar' | 'unknown';
  magnitude: number;
  confidence: number;
  sample_size: number;
  /** False cuando no hay base histórica. Entonces `missing_data_keys` dice qué registrar. */
  can_project: boolean;
  missing_data_keys: string[];
  explanation: Explanation;
}

export interface ColdStartGuidance {
  stage: 'no_data' | 'first_steps' | 'early_pattern' | 'learning' | 'established';
  entry_count: number;
  based_on_reference_profiles: boolean;
  reference_profile_id: string | null;
  reference_sample_size: number;
  suggested_technique_ids: string[];
  suggested_product_attributes: string[][];
  milestone_keys: string[];
  message_key: string;
  explanation: Explanation;
}

export interface MatchResult {
  outcome: 'already_owned' | 'owned_partial' | 'needs_product' | 'unverifiable';
  category: string;
  from_inventory: ProductMatch[];
  suggestions: ProductMatch[];
  unmet_attributes: string[];
  explanation: Explanation;
}

export interface ProductMatch {
  product_id: string;
  brand: string;
  name: string;
  category: string;
  from_inventory: boolean;
  inventory_item_id: string | null;
  matched: AttributeCheck[];
  mismatched: AttributeCheck[];
  unknown: AttributeCheck[];
}

export interface AttributeCheck {
  attribute: string;
  wanted: unknown;
  actual: unknown;
  status: 'match' | 'mismatch' | 'unknown';
}

export interface HairForecast {
  band: 'very_dry' | 'dry' | 'comfortable' | 'humid' | 'very_humid';
  dew_point_c: number;
  frizz_risk: number;
  dryness_risk: number;
  uv_risk: number;
  advice_keys: string[];
  explanation: Explanation;
}

export interface Technique {
  id: string;
  stage: string;
  name_key: string;
  description_key: string;
  evidence_level: EvidenceLevel;
  evidence_label_key: string;
  difficulty: 'easy' | 'moderate' | 'advanced';
  minutes: number;
  goal_keys: string[];
  step_keys: string[];
  timer_steps: number[];
  caution_keys: string[];
  not_for_keys: string[];
}

export interface Myth {
  id: string;
  myth: string;
  message_key: string;
  correction_key: string;
  related_concept: string;
  mechanism: string;
  evidence_level: EvidenceLevel;
  evidence_label_key: string;
  tags: string[];
}

export interface Consent {
  purpose: ConsentPurpose;
  granted: boolean;
  version: number;
  granted_at: string | null;
  revoked_at: string | null;
}

export type ConsentPurpose =
  | 'terms'
  | 'privacy'
  | 'photo_processing'
  | 'model_training'
  | 'stylist_sharing'
  | 'anonymous_aggregate';

export interface Me {
  id: string;
  email: string;
  locale: string;
  depth_level: DepthLevel;
  profile_completeness: number;
  consents: Consent[];
}

export interface Tokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/** Error de la API. Trae clave, no texto: el idioma lo decide el cliente. */
export interface ApiErrorBody {
  code: string;
  message_key: string;
  details: Record<string, unknown>;
}
