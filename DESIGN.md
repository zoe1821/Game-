# PSYCHIATRIC HOSPITAL SIMULATOR — Game Design Document (Android)

> Documento de diseño original del proyecto. Sirve como referencia de alcance completo
> (V0.1 → V1.0). La implementación avanza versión por versión; ver `README.md` para el
> estado actual.

## 1. CONCEPTO

Crear un simulador de gestión hospitalaria psiquiátrica para Android inspirado en la
profundidad de Project Hospital.

El jugador administra un hospital psiquiátrico completo: construye habitaciones,
contrata personal, recibe pacientes, realiza evaluaciones clínicas, establece
diagnósticos diferenciales, decide tratamientos, controla la evolución de los pacientes
y gestiona las finanzas.

El juego debe sentirse como un simulador médico, no como un idle/tycoon simplificado.

### Plataforma

- Android
- Orientación horizontal
- Controles táctiles
- Interfaz escalable para teléfonos y tablets
- Guardado automático

### Estilo visual

2D/isométrico o top-down. Sprites simples pero detallados. Interfaz limpia y
profesional. Inspiración visual: Project Hospital.

## 2. BUCLE PRINCIPAL

1. Construir hospital.
2. Contratar personal.
3. Abrir departamentos.
4. Recibir pacientes.
5. Registrar al paciente.
6. Realizar evaluación.
7. Obtener síntomas y antecedentes.
8. Realizar examen del estado mental.
9. Solicitar pruebas cuando corresponda.
10. Crear diagnóstico diferencial.
11. Seleccionar diagnóstico.
12. Elegir tratamiento.
13. Observar respuesta.
14. Modificar tratamiento si es necesario.
15. Dar alta o continuar hospitalización.
16. Recibir pago.
17. Mejorar el hospital.
18. Desbloquear nuevos servicios.

## 3. MAPA DEL HOSPITAL

Recepción, Consulta externa, Hospitalización, Emergencias psiquiátricas, Terapias,
Diagnóstico, Personal. (Ver detalle completo de salas por área en el documento original
entregado por el usuario.)

## 4. PERSONAL

Psiquiatra, Psicólogo, Enfermero, Trabajador social, Terapeuta ocupacional, Personal
auxiliar — cada uno con atributos y funciones específicas.

## 5. PACIENTES

Generados proceduralmente, con información demográfica/clínica y variables
psicológicas internas **no visibles directamente** para el jugador (deben inferirse
mediante entrevistas y evaluaciones).

## 6. SÍNTOMAS

Síntomas depresivos, de ansiedad, psicóticos, maniformes y patrones de personalidad.
Un síntoma nunca revela automáticamente el diagnóstico.

## 7. ENTREVISTA CLÍNICA

Preguntas por categoría (motivo de consulta, ánimo, ansiedad, sueño, psicosis,
seguridad) que modifican la información disponible para el diagnóstico.

## 8. EXAMEN DEL ESTADO MENTAL

Pantalla dedicada con categorías clínicas estándar (apariencia, conducta, actitud,
habla, ánimo, afecto, pensamiento, percepción, cognición, insight, juicio).

## 9. DIAGNÓSTICO DIFERENCIAL

El jugador nunca recibe el diagnóstico directamente. Debe construir un diferencial a
partir de síntomas y antecedentes, y el sistema calcula probabilidades según la
evidencia reunida.

## 10. PRUEBAS

Evaluación cognitiva, escalas clínicas, laboratorio, toxicología, pruebas metabólicas,
evaluación del sueño, evaluaciones psicológicas — para descartar condiciones médicas,
identificar sustancias, evaluar riesgos y obtener información adicional.

## 11. TRATAMIENTO

Psicoterapia (TCC, apoyo, familiar, grupal, específicas) y medicación por clases
reales (ISRS, IRSN, antipsicóticos, estabilizadores, ansiolíticos, hipnóticos), cada
una con dosis, frecuencia, efectos, tiempo de respuesta, interacciones y
contraindicaciones. *La información médica es contenido de simulación y no debe
tratarse como recomendación clínica real.*

## 12. EVOLUCIÓN DEL PACIENTE

Los tratamientos no funcionan inmediatamente; el estado cambia día a día y pueden
ocurrir efectos secundarios, empeoramiento, falta de adherencia, abandono, recaída,
crisis o diagnóstico incorrecto.

## 13. EVENTOS

Eventos aleatorios (crisis, negativa a tratamiento, abandono, efectos adversos,
mejoría inesperada, emergencias, falta de personal, sobrecarga, problemas
financieros) que requieren decisiones del jugador.

## 14. EMERGENCIA PSIQUIÁTRICA

Prioridades NORMAL / URGENTE / CRÍTICO. El foco está en decisiones clínicas y
seguridad, sin contenido gráfico.

## 15. HOSPITALIZACIÓN

Voluntaria, observación, intensiva — representadas de forma abstracta, sin enseñar
procedimientos legales reales como universales.

## 16. ECONOMÍA

Ingresos por consultas/hospitalizaciones/terapias/evaluaciones/tratamientos; gastos
por salarios, medicamentos, equipamiento, electricidad, mantenimiento, limpieza,
expansión.

## 17. REPUTACIÓN

Afectada por calidad diagnóstica, tiempos de espera, satisfacción, seguridad,
resultados, limpieza, personal y errores.

## 18. PROGRESIÓN

Nivel 1 Clínica pequeña → Nivel 2 Centro de salud mental → Nivel 3 Hospital
psiquiátrico → Nivel 4 Centro especializado, cada uno desbloqueando nuevos sistemas.

## 19. MODO SANDBOX

Dinero infinito opcional, todos los departamentos desbloqueados, generación
ilimitada de pacientes, personal y dificultad configurables.

## 20. SISTEMA DE IA DE PACIENTES

Cada paciente tiene un modelo interno oculto (diagnóstico real, síntomas internos,
% de información que conoce/oculta) y puede olvidar, minimizar, exagerar o cambiar
sus respuestas según el contexto.

## 21. SISTEMA DE ERRORES

Los diagnósticos y tratamientos incorrectos son posibles y tienen consecuencias
(empeoramiento), pero el caso siempre puede revisarse y corregirse.

## 22–25. INTERFAZ, BASE DE DATOS, MOTOR, GUARDADO

- Motor: Unity 2D.
- Datos en JSON (no hardcodeados): `patient_cases.json`, `medications.json`,
  `symptoms.json`, `diagnoses.json`, `events.json`, `staff.json`, `rooms.json`.
- Arquitectura: `GameManager`, `HospitalManager`, `PatientManager`, `StaffManager`,
  `DiagnosisSystem`, `TreatmentSystem`, `TimeManager`, `EconomyManager`,
  `SaveManager`, `UIManager`, `EventManager`.
- Guardado automático de dinero, hospital, personal, pacientes, diagnósticos,
  tratamientos, progreso, reputación e investigación.

## 26. HOJA DE RUTA DE VERSIONES

| Versión | Contenido |
|---|---|
| V0.1 | Mapa, cámara, construcción de habitaciones, paciente básico, tiempo |
| V0.2 | Personal, recepción, consultorio, movimiento de pacientes |
| V0.3 | Entrevista, síntomas, historia clínica |
| V0.4 | Diagnóstico diferencial, examen mental |
| V0.5 | Tratamientos, evolución |
| V0.6 | Hospitalización, emergencias |
| V0.7 | Economía, reputación, progresión |
| V0.8 | Eventos, IA de pacientes |
| V0.9 | Guardado, optimización Android |
| V1.0 | Tutorial, campaña, sandbox, pulido, APK/AAB |

## 27. REGLAS DE IMPLEMENTACIÓN

- Ningún sistema debe ser un prototipo visual falso; cada sistema debe ser funcional.
- Diagnósticos nunca aleatorios ni desconectados de los síntomas; nunca mostrados
  automáticamente.
- Separación estricta entre síntomas, observaciones, antecedentes, pruebas,
  diagnóstico, tratamiento y evolución.
- El juego debe poder ejecutarse sin conexión, sin depender de APIs externas.

## 28. OBJETIVO FINAL

*Project Hospital + simulador de psiquiatría + gestión hospitalaria profunda*, nunca
un idle/clicker/tycoon simplificado. Prioridad: profundidad clínica simulada >
gestión hospitalaria > pacientes dinámicos > diagnóstico diferencial > tratamiento y
evolución > construcción > interfaz táctil > gráficos.
