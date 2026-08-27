# Posicionamiento y diferenciación — Trichon (requisito B5)

> Entregable de Fase 1, previo a implementación. Alimenta el copy del home
> screen y del onboarding.

## 1. El estado del arte (qué existe hoy y qué hace)

| Categoría | Qué hace | Límite estructural |
|---|---|---|
| **Apps de análisis de rizos** (foto → tipo de rizo + productos) | Clasifican la cabeza entera en un tipo (3a/3b/3c) y recomiendan un set de productos. | Asumen **un solo patrón por cabeza**. El curl type es el eje principal, cuando es el eje menos accionable. No modelan porosidad, densidad ni daño por zona. |
| **Quizzes de marca** (cuestionario → set propio) | 8-12 preguntas, salida = productos de esa marca. | El resultado está determinado por el catálogo, no por el cabello. Cero explicabilidad honesta. |
| **Funciones de red social / comunidad de rizos** | Contenido, rutinas de creadores, comparación entre usuarios. | Optimizan enganche, no salud capilar. Amplifican métodos únicos (p. ej. Curly Girl) como verdad universal y mitos sin respaldo. |
| **Apps de escaneo de ingredientes (INCI)** | Semáforo bueno/malo por ingrediente. | Juzgan ingredientes **aislados**, ignorando función, concentración, formulación y a quién le sirve. "Silicona = malo" es el ejemplo canónico del error. |
| **Trackers de crecimiento / recordatorios** | Fotos periódicas y recordatorios. | No interpretan nada; confunden crecimiento con retención de longitud. |
| **Herramientas de tricología clínica** (tricoscopios, software de clínica) | Medición real, uso profesional. | No son de consumo, requieren hardware y consulta; y son diagnóstico médico, terreno que nosotros explícitamente no pisamos. |

Ninguna de estas categorías responde la pregunta que la gente hace de verdad:
*"¿por qué mi pelo quedó así hoy y qué cambio concreto lo mejora?"*

## 2. Los cuatro pilares que constituyen categoría nueva

No son mejoras incrementales sobre "quiz de rizos". Cada uno rompe una asunción
estructural de la categoría existente.

### Pilar 1 — Mapa capilar por zonas (rompe "una cabeza = un tipo")
Una misma cabeza tiene patrones, densidades, diámetros y niveles de daño
distintos por zona: coronilla más seca, nuca más rizada, frontal más fina por
tensión, puntas procesadas y raíz virgen. **Las 14 zonas son la unidad de
análisis y también la unidad de instrucción**: la rutina dice qué hacer *en la
coronilla* y qué hacer *en la nuca*, con producto y cantidad distintos si
corresponde. Ninguna app de consumo hace esto hoy.

### Pilar 2 — Hair Digital Twin (rompe "el análisis es una foto puntual")
No es una simulación física de hebras. Es una **representación estructurada y
actualizable del comportamiento observado** del cabello de esa persona:
qué le pasa con humedad alta, cuánta proteína tolera, cuántos días aguanta la
definición, qué técnica le da mejor resultado con qué producto. Se construye de
scans + historial + productos + clima + técnicas + resultados reales, y permite
proyectar "qué probablemente ocurrirá si..." **siempre con incertidumbre y base
histórica a la vista**. Es un modelo longitudinal, no una clasificación.

### Pilar 3 — Motor experimental personal (rompe "confía en la recomendación")
La app no pretende saber la respuesta: la ayuda a **averiguarla**. El usuario
define un experimento controlado (crema+gel vs. solo gel, resto de variables
igual), la app estructura las repeticiones, controla las variables observables
(clima, cantidad, técnica) y lee el resultado **con honestidad estadística**:
tamaño de muestra, si la diferencia es distinguible del ruido, y qué variables
quedaron sin controlar. Esto convierte la app en un instrumento, no en un oráculo.

### Pilar 4 — Anti-consumismo estructural (rompe "recomendar = vender")
El primer paso de cualquier recomendación es el inventario del usuario. El motor
de producto **no puede** acceder a datos comerciales (ver `02-MONETIZATION.md` §4).
La consecuencia de producto es concreta: la respuesta más frecuente a "¿qué
compro?" será "nada, usa el que ya tienes así".

## 3. El eje transversal: incertidumbre explícita

Cada uno de los pilares descansa en algo que la categoría entera evita:
**decir lo que no sabemos**. Separamos:

- **evidence confidence** — qué tan sólida es la regla general (evidencia
  científica / consenso profesional / experiencia anecdótica extendida / mito).
- **personal confidence** — cuántos datos *tuyos* la respaldan, con tamaño de
  muestra siempre visible.

Una recomendación puede ser "regla sólida, pero solo 2 wash days tuyos" o
"apenas anecdótico, pero en tus 14 registros funciona". Son cosas distintas y el
usuario ve la diferencia. Ninguna app de la categoría distingue esto.

## 4. Para quién es (y para quién no)

**Es para**: cualquier persona, de cualquier género y presentación, con cabello
liso, ondulado, rizado, afro o texturizado, que ya intentó cuidarse el pelo y se
topó con consejos contradictorios; personas con cabello procesado o en
transición; personas cuyo cabello no encaja en un solo tipo.

**No es para**: quien quiere una respuesta rápida sin invertir nada; quien busca
diagnóstico médico (explícitamente fuera de alcance, ver `04-LEGAL-CHECKLIST.md`);
quien quiere una comunidad social.

## 5. Traducción a copy de producto

El primer texto que ve el usuario **no puede** sonar a "descubre tu tipo de rizo".

**Home / primera pantalla (es):**
> **Tu cabello no es un tipo. Es un mapa.**
> Analizamos zona por zona, aprendemos de tus resultados reales y te decimos
> exactamente qué hacer — y qué no hace falta comprar.

**Home / primera pantalla (en):**
> **Your hair isn't a type. It's a map.**
> We analyse it zone by zone, learn from your real results, and tell you exactly
> what to do — and what you don't need to buy.

**Onboarding, pantalla 1 (es):**
> Vas a construir un perfil, no a hacer un test.
> Empezamos con lo mínimo (menos de 3 minutos). Todo lo demás lo añades cuando
> quieras, y puedes corregir cualquier cosa que estimemos mal.

**Frase de honestidad, presente en el primer análisis:**
> Esto es lo que vemos en tus fotos y lo que deducimos de tus respuestas.
> Todavía no conocemos tu cabello: eso lo aprendemos con tus resultados.

## 6. Riesgo de posicionamiento y cómo lo mitigamos

El riesgo real no es que copien las funciones, es que **la profundidad espante**
(ver B3). Mitigación en producto, no en marketing: onboarding mínimo <3 min,
niveles de profundidad básico/intermedio/avanzado, funciones avanzadas ocultas
por defecto, y la prueba de los 10 segundos aplicada a cada pantalla.
