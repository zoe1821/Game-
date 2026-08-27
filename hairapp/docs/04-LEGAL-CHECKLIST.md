# Checklist legal y regulatorio — BORRADOR DE TRABAJO

> **AVISO IMPORTANTE**
> Este documento es un **borrador interno de trabajo generado con asistencia de
> IA**. **NO es asesoría legal** y no debe usarse como tal. Debe ser revisado,
> corregido y aprobado por un profesional legal con competencia en las
> jurisdicciones objetivo (protección de datos, producto sanitario y publicidad
> cosmética) **antes de cualquier lanzamiento público**.
> Cada ítem marcado `[ ]` está pendiente de validación legal real.

Requisito B6 de Fase 1.

---

## 1. Límite fundamental: la app NO es un producto sanitario

La app es **cosmética y educativa**. La línea que no se cruza:

- No diagnostica, no trata, no previene ni monitoriza ninguna enfermedad,
  lesión o discapacidad.
- No emite juicios sobre alopecia, dermatitis seborreica, psoriasis, tiña,
  foliculitis, infecciones, ni causas hormonales o sistémicas.
- No estima "salud del folículo", "densidad folicular clínica" ni nada que
  sugiera medición médica.

**Por qué importa regulatoriamente:** en la UE, software cuya finalidad prevista
sea diagnóstico o monitorización de una condición puede caer bajo el MDR
(Reglamento (UE) 2017/745) — y una app de este tipo caería, como mínimo, en
clase IIa por la regla de software. En EE. UU., la FDA ejerce discreción sobre
software de bienestar general, pero **la finalidad declarada y el lenguaje de
marketing son lo que determina la clasificación**. Es decir: el riesgo se crea
con las palabras, no solo con el código.

Consecuencia de producto, ya implementada en la arquitectura:
- Existe un **glosario de lenguaje controlado** (`09-CONTROLLED-LANGUAGE.md`)
  que bloquea términos con implicación médica en todo texto de usuario.
- Existe un test automático que falla si un término prohibido aparece en los
  catálogos i18n o en los packs de reglas.

`[ ]` Validar con legal la redacción de la finalidad prevista en tienda y web.
`[ ]` Confirmar que ninguna captura de pantalla de la ficha de tienda implica diagnóstico.

## 2. Lenguaje: reemplazos obligatorios

| Prohibido | Usar en su lugar |
|---|---|
| dermatitis, seborrea, psoriasis | irritación visible / descamación visible |
| alopecia, calvicie | densidad reducida observada / pérdida de longitud |
| diagnóstico, diagnosticar | observación, estimación |
| tratar, tratamiento (clínico) | rutina, cuidado, puedes considerar |
| curar, sanar, reparar (la fibra) | mejorar el aspecto, acondicionar, sellar |
| debes, tienes que | puedes considerar, suele funcionar |
| infección, hongos, bacteria | señal que conviene revisar con un profesional |
| clínicamente probado | consenso profesional / evidencia científica (con etiqueta) |

Regla de derivación (A7/A23): ante heridas abiertas, inflamación, pérdida
localizada y repentina, dolor persistente, sangrado o cambios rápidos, la app
**siempre** muestra el mismo bloque: no interpreta, no estima, y deriva a
evaluación profesional presencial.

`[ ]` Revisión legal de la lista completa del glosario.

## 3. Datos personales

### 3.1 Categoría de los datos
- Fotografías del cuero cabelludo y del rostro potencialmente identificables.
- **Punto crítico:** bajo el RGPD (art. 9), una fotografía es dato biométrico de
  categoría especial **solo cuando se procesa por medios técnicos específicos
  para identificar unívocamente a una persona**. Nuestro pipeline **no hace
  reconocimiento facial ni identificación**; extrae métricas de textura capilar.
  Aun así, tratamos las fotos con el estándar más alto por prudencia.

`[ ]` **Confirmar con legal** si el análisis de imagen que hacemos activa el
art. 9 RGPD en alguna jurisdicción objetivo. Es la pregunta legal de mayor
impacto del proyecto: si la respuesta es sí, se requiere consentimiento
explícito reforzado y una base jurídica distinta.

### 3.2 Consentimientos separados (implementados como entidades distintas)
Cada uno es opt-in independiente, versionado, revocable, con timestamp:

1. `TERMS` — términos y condiciones.
2. `PRIVACY` — política de privacidad.
3. `PHOTO_PROCESSING` — procesar mis fotos para generar mi análisis.
4. `MODEL_TRAINING` — usar mis fotos para mejorar los modelos.
   **Por defecto: NO. Rechazarlo no degrada ninguna función de la app.**
5. `STYLIST_SHARING` — compartir un reporte con un profesional (por reporte).
6. `ANONYMOUS_AGGREGATE` — aportar resultados de experimentos anonimizados (B7).

`[ ]` Verificar que ninguno de los 6 esté pre-marcado en la UI.
`[ ]` Verificar que revocar cualquiera de ellos sea reversible en 2 taps.

### 3.3 Derechos de la persona usuaria
- Acceso y **portabilidad**: exportación completa en formato legible por máquina.
- **Supresión real**: borrado de cuenta = hard delete de filas + purga de objetos
  en storage, no un flag. Plazo objetivo: inmediato en DB, ≤30 días en backups.
- Rectificación: ya es una función central del producto (corregir cualquier
  estimación).
- Oposición al tratamiento: revocar `PHOTO_PROCESSING` detiene todo análisis
  de imagen y ofrece borrar las fotos existentes.

`[ ]` Definir y documentar el plazo real de purga en backups.
`[ ]` Redactar el registro de actividades de tratamiento (art. 30 RGPD).
`[ ]` Evaluar si se requiere DPIA (art. 35). **Probable que sí** por tratamiento
a gran escala de imágenes con perfilado. Asumir que sí hasta que legal diga lo contrario.
`[ ]` Determinar si se requiere DPO.
`[ ]` Acuerdos de encargado de tratamiento (art. 28) con proveedores: hosting,
storage, proveedor de clima, proveedor de LLM del asistente.
`[ ]` Transferencias internacionales: si algún proveedor está fuera del EEE,
documentar SCC / decisión de adecuación. **Aplica al proveedor del asistente.**

### 3.4 Por región
- **UE/EEE**: RGPD. Base jurídica = consentimiento para fotos; ejecución de
  contrato para el resto del servicio.
- **Reino Unido**: UK GDPR + DPA 2018.
- **EE. UU.**: CCPA/CPRA (California) — derecho a opt-out de "venta/compartición"
  (no vendemos, pero hay que declararlo); **BIPA (Illinois)** y leyes análogas de
  Texas y Washington son el riesgo alto si las fotos se consideran identificadores
  biométricos. `[ ]` **Consultar específicamente BIPA antes de lanzar en EE. UU.**
- **Brasil**: LGPD. **Canadá**: PIPEDA + Ley 25 de Quebec.
- `[ ]` Decidir la lista de jurisdicciones de lanzamiento v1 y acotar el alcance
  legal a esa lista; no lanzar globalmente por defecto.

## 4. Menores de edad

Decisión de producto v1: **la app se restringe a mayores de 16 años.**

- Puerta de edad en el registro (no un checkbox, una fecha).
- Motivo: el tratamiento de imágenes de menores con consentimiento parental
  verificable (COPPA en EE. UU. para <13, art. 8 RGPD para <16 según país) añade
  una carga de cumplimiento desproporcionada para v1.
- La ficha de tienda debe declarar la clasificación por edad coherente con esto.

`[ ]` Confirmar el umbral por país (el RGPD permite a los estados fijarlo entre 13 y 16).
`[ ]` Definir el flujo si una cuenta existente declara ser menor.

## 5. Contenido y afirmaciones

- Todo contenido educativo lleva etiqueta de nivel de evidencia visible (B4).
- Ninguna afirmación de eficacia sobre un producto de terceros: describimos
  función de ingredientes y ajuste al perfil, no prometemos resultados.
- No se reproducen textos de marca ni imágenes de packaging sin permiso; el
  catálogo almacena datos fácticos (INCI, formato, categoría).
- `[ ]` Revisar el uso de nombres de marca en el catálogo (uso nominativo
  descriptivo; probablemente admisible, requiere confirmación).
- `[ ]` Revisar términos de servicio de cualquier fuente de datos INCI de terceros.

## 6. Tiendas de aplicaciones

- `[ ]` Apple: cuestionario de privacidad (App Privacy) coherente con lo real.
- `[ ]` Apple guideline 1.4.1 / 5.1.1(iii): apps de salud y datos sensibles.
- `[ ]` Google Play: Data safety form; política de Health Apps; declaración de
  permisos sensibles (cámara).
- `[ ]` Declaración de suscripciones y renovación automática en ambas tiendas.
- `[ ]` Derecho de desistimiento UE para la suscripción.

## 7. Seguridad (obligación legal, no solo técnica)

- `[ ]` Procedimiento de notificación de brechas (72 h RGPD) escrito y probado.
- `[ ]` Cifrado en tránsito (TLS) y en reposo; rotación de claves documentada.
- `[ ]` Registro de accesos a fotos por parte de personal interno; principio de
  mínimo privilegio. **Nadie del equipo debe poder navegar fotos de usuarios.**
- `[ ]` Pentest antes del lanzamiento público.

## 8. Bloqueantes duros antes de lanzar

Ninguno de estos es negociable por presión de calendario:

1. `[ ]` Revisión legal completa de este documento por profesional cualificado.
2. `[ ]` Respuesta cerrada a la pregunta del art. 9 RGPD (§3.1).
3. `[ ]` DPIA completada si aplica.
4. `[ ]` Política de privacidad y ToS redactados por legal, no por IA.
5. `[ ]` Borrado de cuenta verificado end-to-end (incluida purga de storage).
6. `[ ]` Auditoría de lenguaje: 0 hallazgos del test de glosario controlado.
