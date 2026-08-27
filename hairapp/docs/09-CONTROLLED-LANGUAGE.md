# Glosario de lenguaje controlado (requisito B6, parte de Fase 2)

Este glosario **se ejecuta**: vive en `backend/app/data/controlled_language.yaml`
y hay un test que falla si un término bloqueado aparece en los catálogos i18n,
en los packs de reglas o en el contenido educativo.

## 1. Términos bloqueados y su reemplazo

| Bloqueado | Reemplazo obligatorio | Motivo |
|---|---|---|
| dermatitis | irritación visible | Nombra una condición médica |
| seborrea / seborreica | exceso de grasa visible | Ídem |
| psoriasis | descamación visible | Ídem |
| alopecia | densidad reducida observada | Ídem |
| calvicie | zona con menor densidad | Ídem |
| foliculitis | irritación visible en el cuero cabelludo | Ídem |
| infección / hongos / bacteriano | señal que conviene revisar con un profesional | Ídem |
| diagnóstico / diagnosticar | observación / estimar | Implica acto médico |
| tratamiento / tratar | rutina / cuidado / puedes considerar | Implica acto médico |
| curar / sanar | mejorar el aspecto | Promesa médica |
| reparar (la fibra) | acondicionar / sellar / mejorar el aspecto | La fibra queratinizada no se repara |
| regenerar | acondicionar | Ídem |
| clínicamente probado | (usar la etiqueta de evidencia) | Afirmación regulada |
| debes / tienes que | puedes considerar / suele funcionar | Imperativo prescriptivo |
| garantizado | (eliminar) | Promesa de resultado |
| detox / desintoxicar | clarificar / retirar acumulación | Pseudociencia |
| células madre capilares | (eliminar) | Marketing sin sustento cosmético |
| nutrir desde dentro (aplicado tópicamente) | acondicionar la superficie | Mecanismo falso |

## 2. Términos permitidos con condición

| Término | Condición |
|---|---|
| proteína | Solo con contexto de exceso/déficit y nunca como "reparación" |
| daño | Permitido para daño **visible** (puntas abiertas, rotura); prohibido afirmar daño interno por foto |
| porosidad | Siempre acompañado de confianza y de que es una estimación |
| crecimiento | Distinguir siempre crecimiento biológico de retención de longitud |
| sensibilidad / alergia | Solo como registro declarado por el usuario, nunca como valoración nuestra |

## 3. Bloque de derivación (texto único, no variable)

Se muestra íntegro, sin interpretación previa, ante: heridas abiertas,
inflamación, pérdida de cabello localizada o repentina, dolor persistente,
sangrado, o cambios rápidos e inexplicados.

> **Esto se sale de lo que esta app puede analizar.**
> No podemos estimar qué es ni recomendarte nada al respecto. Lo que estás
> describiendo conviene que lo vea en persona un profesional de la salud
> (dermatología). No es una urgencia necesariamente, pero sí algo que una app
> de cuidado cosmético no debe interpretar.

## 4. Tono

- Gender-neutral siempre. Sin "chicas", sin "reinas", sin "guapa".
- Segunda persona, directa, sin infantilizar.
- Nunca culpabilizar al usuario por su cabello o sus hábitos.
- Nunca urgencia artificial ni miedo como palanca.
