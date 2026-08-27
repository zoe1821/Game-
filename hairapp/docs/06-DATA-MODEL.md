# Modelo de datos

## 1. El patrón que gobierna todo: `Measured`

Cualquier propiedad estimada (patrón, porosidad, densidad, daño...) se guarda
como un valor con procedencia:

```
value        el valor en sí
confidence   0.0 - 1.0
source       AI_VISION | USER | INFERRED | REFERENCE_PROFILE | DEFAULT
observed_at  fecha
notes        texto opcional
```

Reglas invariantes:
- `source = USER` **siempre gana** sobre cualquier otra (A1.4). El motor nunca
  sobrescribe una corrección manual; la marca como el valor vigente y conserva
  la estimación previa como histórico.
- `source = REFERENCE_PROFILE` solo aparece en cold start y se etiqueta en UI
  como "basado en perfiles similares, no en tu historial" (B2).
- `confidence` nunca es 1.0 salvo `source = USER`.

## 2. Las 14 zonas (A4)

`FRONTAL_HAIRLINE, BANGS, FRONT_LEFT, FRONT_RIGHT, LEFT_TEMPLE, RIGHT_TEMPLE,
SIDE_UPPER_LEFT, SIDE_UPPER_RIGHT, SIDE_LOWER_LEFT, SIDE_LOWER_RIGHT, CROWN,
BACK_CROWN, OCCIPITAL, NAPE` más `ENDS` como zona transversal de puntas.

Cada zona almacena `Measured` de: patrón, diámetro de rizo, frecuencia de curva,
diámetro de hebra, densidad, frizz, definición, daño visible, color/procesamiento,
longitud, encogimiento, más observaciones libres. Todo editable manualmente.

## 3. Tablas principales

```
users(id, email, password_hash, birth_date, locale, created_at, deleted_at)
consents(id, user_id, purpose, granted, version, granted_at, revoked_at)
hair_profiles(id, user_id, depth_level, completeness, wash_frequency_days, ...)
hair_zones(id, profile_id, zone, measurements JSONB, updated_at)
chemical_events(id, profile_id, kind, date, zones[], details JSONB)
mechanical_events(id, profile_id, kind, date, zones[], details JSONB)
scans(id, profile_id, status, created_at, quality_report JSONB)
scan_photos(id, scan_id, angle, storage_key, quality JSONB, state)
scan_interpretations(id, scan_id, payload JSONB, confidence_report JSONB)
goals(id, profile_id, kind, priority, created_at)
products(id, brand, name, category, size_ml, inci_raw, attributes JSONB, ...)
ingredients(id, inci_name, functions[], notes_key)
product_ingredients(product_id, ingredient_id, position)
inventory_items(id, profile_id, product_id?, custom_name?, opened_at, pao_months, amount_left)
routines(id, profile_id, kind, active, generated_at, rationale JSONB)
routine_steps(id, routine_id, order, zone?, action, product_ref?, amount, technique_key, params JSONB, explanation JSONB)
journal_entries(id, profile_id, date, weather JSONB, products[], techniques[], notes)
journal_results(id, entry_id, day_offset, ratings JSONB, photo_key?)
experiments(id, profile_id, question, controlled_vars JSONB, status)
experiment_arms(id, experiment_id, label, config JSONB)
experiment_observations(id, arm_id, journal_entry_id, ratings JSONB)
twin_snapshots(id, profile_id, created_at, state JSONB, evidence JSONB)
```

**Campos que deliberadamente NO existen en `products`:** `sponsored`,
`partner_id`, `commission_rate`, `affiliate_url`. Ver `02-MONETIZATION.md` §4.

## 4. Fotos

Nunca en la base de datos. `storage_key` apunta a un bucket privado. El borrado
de cuenta purga los objetos, no solo las filas.
