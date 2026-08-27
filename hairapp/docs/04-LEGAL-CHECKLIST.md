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

### 3.4 Por región — **alcance decidido: LATAM + EE. UU.**

Decisión de producto tomada: el lanzamiento es **LATAM (con México como
mercado principal) y Estados Unidos**. Eso cambia el orden de prioridades
respecto a la versión anterior de este documento, que asumía Europa primero.

**El cambio más importante: EE. UU. pasa de "quizá" a riesgo principal.**

#### 🔴 EE. UU. — leyes de privacidad biométrica (RIESGO MÁS ALTO DEL PROYECTO)

| Ley | Qué exige | Por qué nos afecta |
|---|---|---|
| **BIPA** (Illinois, 740 ILCS 14) | Consentimiento **escrito** previo, política pública de retención y destrucción, prohibición de lucrarse con el dato biométrico | **Tiene derecho privado de acción**: cualquier persona puede demandar, con daños legales tasados por infracción. Es la vía de litigio colectivo más activa de EE. UU. en esta materia. |
| **CUBI** (Texas, Bus. & Com. §503.001) | Consentimiento previo, destrucción en plazo razonable | Sin acción privada, pero el fiscal general de Texas ha abierto casos de gran cuantía |
| **My Health My Data** (Washington) | Consentimiento separado para "datos de salud del consumidor", definidos de forma muy amplia | **También tiene acción privada.** Su definición amplia podría alcanzar datos sobre estado del cuero cabelludo |
| **CCPA/CPRA** (California) | Derechos de acceso, supresión y opt-out; la información biométrica es categoría sensible | Obligaciones de aviso y de gestión de solicitudes |

`[ ]` **BLOQUEANTE. Consultar con un abogado especializado en BIPA antes de
publicar en EE. UU.** La pregunta concreta: nuestro pipeline mide textura
capilar y **no identifica personas**, lo que probablemente lo deja fuera de la
definición de "identificador biométrico" de BIPA — pero "probablemente" no es
suficiente cuando la sanción se cuenta por usuario y hay acción colectiva.

`[ ]` Decidir si se excluyen Illinois, Texas y Washington en la v1 mientras se
resuelve. Es una opción legítima y barata de implementar (geobloqueo por
`billing_country` y estado), y la alternativa puede costar mucho más.

`[ ]` Redactar consentimiento **escrito** específico de fotos si se opera en
Illinois, con política de retención y destrucción publicada.

#### México (mercado principal)

- **LFPDPPP** (Ley Federal de Protección de Datos Personales en Posesión de los
  Particulares) y su Reglamento.
- Requiere **aviso de privacidad** con contenido tasado, disponible antes de
  recoger el dato. No basta con una política genérica traducida.
- Los datos biométricos se consideran **datos personales sensibles** (art. 3
  fr. VI), lo que exige **consentimiento expreso y por escrito** (art. 8).
- Derechos ARCO (acceso, rectificación, cancelación, oposición) con plazos
  propios de respuesta.
- `[ ]` Redactar el aviso de privacidad conforme a la ley mexicana, no como
  traducción del europeo.
- `[ ]` Designar la persona o departamento de datos personales que exige la ley.
- `[ ]` Confirmar si nuestro tratamiento de imagen entra en "biométrico" bajo
  la LFPDPPP. **Misma pregunta que en la UE y en BIPA: es la consulta legal de
  mayor impacto y conviene resolver las tres de una vez.**

#### Resto de LATAM

| País | Norma | Nota |
|---|---|---|
| **Brasil** | LGPD | Muy cercana al RGPD. La ANPD ya sanciona. Mercado grande para este producto, y **origen del cronograma capilar**. Si se lanza en Brasil hace falta portugués, no solo español. |
| **Colombia** | Ley 1581/2012 | Exige **registro de bases de datos** ante la SIC. Trámite administrativo real. |
| **Argentina** | Ley 25.326 | En proceso de reforma; vigilar. |
| **Chile** | Ley 19.628 y la nueva ley de datos | Nueva autoridad de protección de datos en implantación. |
| **Perú** | Ley 29733 | Requiere inscripción de bancos de datos. |
| **Ecuador, Uruguay, Panamá, Costa Rica** | Leyes propias | Uruguay tiene decisión de adecuación de la UE. |

`[ ]` Priorizar: México y EE. UU. primero; Colombia y Brasil en segunda fase
por su carga administrativa (registro de bases y, en Brasil, idioma adicional).
`[ ]` No lanzar en los 20 países a la vez. Cada uno añade obligaciones propias.

#### Europa

Se mantiene el análisis del RGPD en este documento **por si hay expansión
futura**, pero deja de ser el foco. No es trabajo urgente.

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

## 5 bis. Suscripciones

El modelo de ingresos es la suscripción (docs/02-MONETIZATION.md). Obligaciones
concretas derivadas de eso:

- `[ ]` **Verificación de recibo en servidor.** Hoy `/billing/activate` confía
  en lo que le manda el cliente, lo que basta para desarrollo pero **no** para
  producción: un cliente modificado podría concederse el plan de pago. Hay que
  validar contra el servidor de App Store / Google Play antes de cobrar a nadie.
- `[ ]` **México — NOM-151 y PROFECO.** Las condiciones de la suscripción, la
  renovación automática y el procedimiento de cancelación deben estar en
  español, claros y accesibles antes de contratar. PROFECO vigila la renovación
  automática y la facilidad de cancelación.
- `[ ]` **EE. UU. — FTC "Click to Cancel"** y leyes estatales de renovación
  automática (California ARL entre las más estrictas): cancelar debe ser tan
  fácil como suscribirse, y por el mismo medio.
- `[ ]` **Impuestos.** IVA mexicano sobre servicios digitales prestados por
  extranjeros; sales tax en EE. UU. según estado. Las tiendas retienen en
  muchos casos, pero no en todos: confirmar con asesoría fiscal.
- `[ ]` Precio localizado por país. Un precio en dólares aplicado tal cual a
  toda LATAM deja el producto fuera de alcance en varios mercados.
- `[ ]` Confirmar que la app **no** vulnera las reglas de pago de las tiendas.
  Todo cobro digital debe ir por la tienda.

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

1. `[ ]` Revisión legal completa de este documento por profesional cualificado,
   con competencia en **México y EE. UU.**, no solo en la UE.
2. `[ ]` **Respuesta cerrada a la pregunta biométrica, en las tres
   jurisdicciones a la vez**: BIPA (Illinois), LFPDPPP (México) y art. 9 RGPD.
   Es la misma pregunta de fondo — ¿medir textura capilar sin identificar a
   nadie es tratamiento biométrico? — y resolverla desbloquea el resto.
3. `[ ]` Decisión sobre si se excluyen Illinois, Texas y Washington en la v1.
4. `[ ]` Verificación de recibo de suscripción en servidor (§5 bis).
5. `[ ]` Aviso de privacidad mexicano conforme a la LFPDPPP.
6. `[ ]` Política de privacidad y ToS redactados por legal, no por IA.
7. `[x]` Borrado de cuenta verificado end-to-end, incluida la purga del
   almacenamiento de fotos. Cubierto por test.
8. `[x]` Auditoría de lenguaje: 0 hallazgos del glosario controlado, verificado
   en backend y en los catálogos de la app.
