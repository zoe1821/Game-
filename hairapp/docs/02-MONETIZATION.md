# Estrategia de monetización — Trichon (requisito B1)

> Entregable de Fase 1. Documento de producto/negocio, no de marketing.

## 1. El conflicto central que hay que resolver

El producto se posiciona explícitamente como **anti-consumista** (A15: "usa lo
que ya tienes" antes de recomendar comprar). El modelo de ingresos por defecto
de esta categoría — afiliación a marcas y venta de producto — es directamente
incompatible con esa promesa: crea un incentivo para recomendar más compras y
para rankear por comisión.

Por lo tanto: **la app no monetiza la recomendación de productos.** Ni por
afiliación, ni por posicionamiento pagado, ni por "marca destacada".

## 2. Qué es gratis y qué es premium

### Gratis, para siempre (el núcleo útil)

Un usuario gratuito debe poder cuidar bien su cabello. Si el tier gratuito no
sirve, la promesa educativa es falsa.

- Enciclopedia educativa completa, incluido el detector de mitos (A17).
- Hair scan básico: hasta **2 scans al mes**, mapa de zonas completo (las 14
  zonas), análisis de patrón, porosidad estimada y daño visible.
- Perfil capilar completo y edición manual ilimitada de cualquier estimación.
- **Una** rutina activa generada, con instrucciones por zona completas.
- Diario de wash day ilimitado (los datos del usuario nunca se rehenean).
- Inventario personal ilimitado y análisis de "usa lo que ya tienes".
- Ingredient scanner: **10 análisis al mes**.
- Explicabilidad ("¿por qué esto?") en todas las recomendaciones. No es premium:
  cobrar por la transparencia sería exactamente el patrón oscuro que evitamos.
- Modos rápidos, protección nocturna, refresh planner.

### Premium — "Trichon Estudio" (suscripción)

Se cobra por **profundidad analítica y continuidad**, no por acceso básico.

| Función | Por qué es premium |
|---|---|
| Hair Digital Twin avanzado (A24) con proyecciones "qué pasa si..." | Es el trabajo computacional y de datos más caro; su valor crece con el tiempo de uso. |
| Experimentos personales ilimitados (A25) — gratis: 1 activo | Cada experimento requiere seguimiento estructurado y lectura estadística. |
| Histórico extendido: comparación fotográfica, timeline y growth tracker más allá de 6 meses | Coste real de storage; valor real para el usuario de largo plazo. |
| Scans ilimitados y scan de cuero cabelludo con seguimiento longitudinal | Coste de cómputo por scan. |
| Ingredient scanner y comparador de productos ilimitados | Coste de catálogo y de cómputo. |
| Exportación de reporte para estilista (A26) | Ver §3: es también la puerta al canal profesional. |
| Asistente conversacional con contexto completo (gratis: cupo mensual) | Coste directo de inferencia por consulta. |
| Alertas de clima proactivas y planificación semanal | Coste de proveedor de clima + notificaciones. |

**Precio de referencia (a validar):** ~4,99 €/mes o ~34,99 €/año. Anual con
descuento fuerte porque el valor del producto es longitudinal: nos conviene un
usuario que acumule 12 meses de journal, no uno que pruebe un mes.

**Reglas duras del paywall:**
1. Nunca se bloquean los datos que el usuario ya generó. Si cancela, conserva
   lectura y exportación de todo su histórico; solo pierde el análisis nuevo.
2. Nunca se usa el miedo ("tu cabello se está dañando, hazte premium").
3. El paywall se muestra en el punto de valor, no en el onboarding.

## 3. Segundo canal: estilistas y salones (no marcas)

El reporte para estilista (A26) es la bisagra entre el usuario y un profesional.
Modelo propuesto:

- **Trichon Pro**: cuenta para estilistas/salones con suscripción propia
  (~15-25 €/mes por profesional) que permite recibir reportes de clientes,
  anotar la consulta y devolver un plan que se sincroniza en la app del usuario.
- **La comisión, si existe, es por reporte compartido / consulta gestionada —
  nunca por producto vendido.** Un profesional no gana más por vender más
  producto a través nuestro, porque no hay venta de producto a través nuestro.
- Directorio de profesionales: listado por especialidad real (rizo, texturizado,
  color correctivo, locs) y por zona geográfica, **sin ranking pagado**. El
  orden es por relevancia y proximidad; cualquier posición promocionada se
  etiqueta visiblemente como tal o simplemente no existe. Decisión v1: no existe.

Este canal es estratégicamente importante porque su incentivo está alineado:
el profesional gana cuando el usuario llega mejor informado, no cuando compra más.

## 4. Por qué el motor de recomendación NO se acopla a los ingresos

**Requisito arquitectónico, no aspiración.**

1. El módulo `domain/products/matching.py` recibe únicamente: perfil capilar,
   zonas, objetivos, inventario, clima e historial del journal. **No recibe
   identificadores comerciales.** Los campos `sponsored`, `partner_id`,
   `commission_rate`, `affiliate_url` **no existen** en el modelo `Product`.
2. Si en el futuro existiera cualquier relación comercial con una marca, vivirá
   en una tabla separada (`CommercialRelationship`) que **el motor no puede
   importar**; la separación se verifica con un test automático que inspecciona
   las dependencias del módulo de matching y falla si toca capa comercial.
3. El ranking siempre muestra "por qué este producto" con los atributos que lo
   justifican. Un ranking que no se puede explicar en términos del perfil del
   usuario es un ranking corrupto por definición.
4. El primer resultado de cualquier consulta de producto es siempre el chequeo
   de inventario: "ya tienes X, que cumple esta función". Si el inventario
   resuelve la necesidad, no se muestra ninguna recomendación de compra (A15).

## 5. Lo que explícitamente NO haremos

- Publicidad de terceros y SDKs de tracking publicitario.
- Venta o cesión de datos, agregados o no, a marcas.
- Cajas de suscripción de producto propias (nos convertiría en la marca cuyo
  producto rankeamos).
- Gamificación competitiva o social que empuje consumo (ver B7).
- "Análisis gratis, resultado de pago": el análisis se muestra completo o no se hace.

## 6. Coste unitario y sostenibilidad (estimación para dimensionar, no promesa)

Costes variables por usuario activo/mes, orden de magnitud:

- Storage de fotos: un usuario que hace 2 scans/mes con ~8 fotos comprimidas
  (~400 KB) genera ~6,4 MB/mes → ~77 MB/año. A precios S3-compatible típicos,
  céntimos al año. **No es el cuello de botella.**
- Cómputo de scan: el pipeline v1 es CPU (validación + métricas). Con modelo de
  segmentación real, el coste sube; se mitiga corriendo la validación de calidad
  en el dispositivo y solo subiendo fotos que pasan el filtro.
- Asistente conversacional: **el coste dominante y el único que escala mal.** Por
  eso el cupo gratuito es limitado y el contexto se construye de forma acotada
  (resumen estructurado del perfil, no volcado de historial).
- Clima: cacheado por celda geográfica en Redis, no por usuario. Coste ~plano.

Implicación de diseño: la sostenibilidad depende de **acotar el asistente**, no
de acotar el análisis. Está reflejado en la tabla de §2.

## 7. Métricas que decidiremos mirar (y las que no)

Miramos: retención semana 4 y 12, scans completados/usuario, entradas de journal
por usuario activo, ratio de correcciones manuales del análisis (calidad real del
motor), conversión a premium tras 30 días, reportes compartidos con estilista.

**No** miramos ni optimizamos: tiempo en app, sesiones/día, ni ningún proxy de
enganche. Una app de cuidado capilar que maximiza tiempo de pantalla está
fallando: el éxito es que el usuario cuide bien su cabello y vuelva cuando toca
lavar, no que se quede dentro.
