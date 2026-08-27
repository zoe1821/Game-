/**
 * Catálogo español. Es el idioma de origen: el inglés se traduce desde aquí.
 *
 * Reglas de redacción, verificadas por `src/i18n/__tests__/language.test.ts`:
 *  - Lenguaje neutro en cuanto a género, siempre.
 *  - Nada de terminología con implicación médica (ver el glosario controlado
 *    del backend, `app/data/controlled_language.yaml`).
 *  - Segunda persona, directa, sin infantilizar y sin culpabilizar.
 *  - Ninguna urgencia artificial ni miedo como palanca.
 */
export const es = {
  common: {
    continue: 'Continuar',
    back: 'Atrás',
    save: 'Guardar',
    cancel: 'Cancelar',
    edit: 'Editar',
    delete: 'Eliminar',
    retry: 'Reintentar',
    skip: 'Ahora no',
    done: 'Listo',
    loading: 'Cargando',
    optional: 'Opcional',
    whyThis: '¿Por qué esto?',
    seeDetail: 'Ver detalle',
    notNow: 'Ahora no',
    of: 'de',
  },

  home: {
    // El primer texto que se ve. No puede sonar a «descubre tu tipo de rizo»
    // (docs/03-POSITIONING.md §5).
    heroTitle: 'Tu cabello no es un tipo. Es un mapa.',
    heroBody:
      'Lo analizamos zona por zona, aprendemos de tus resultados reales y te decimos exactamente qué hacer — y qué no hace falta comprar.',
    startScan: 'Empezar por el mapa',
    continueProfile: 'Seguir con tu perfil',
    todayTitle: 'Hoy',
    routineForToday: 'Tu rutina de hoy',
    profileCompleteness: 'Tu perfil está completo al %{percent}%',
    profileCompletenessHint: 'Puedes añadir el resto cuando quieras. Nada se bloquea.',
  },

  onboarding: {
    welcomeTitle: 'Vas a construir un perfil, no a hacer un test',
    welcomeBody:
      'Empezamos con lo mínimo, menos de tres minutos. Todo lo demás lo añades cuando quieras, y puedes corregir cualquier cosa que estimemos mal.',
    essentialTitle: 'Lo esencial',
    essentialSubtitle: 'Cinco preguntas. Con esto ya podemos empezar.',
    patternQuestion: '¿Cómo describirías tu cabello ahora mismo?',
    patternHint:
      'Una respuesta aproximada basta. El mapa por zonas afinará esto después, y podrás corregirlo.',
    lengthQuestion: '¿Cuánto mide, más o menos?',
    lengthHint: 'De la raíz a las puntas, en centímetros.',
    washQuestion: '¿Cada cuántos días sueles lavarlo?',
    goalQuestion: '¿Qué te gustaría mejorar primero?',
    goalHint: 'Puedes añadir más objetivos luego y cambiar el orden.',
    processedQuestion: '¿Lo tienes teñido, decolorado, alisado o con alguna química?',
    processedHint: 'Cambia bastante lo que conviene hacer, por eso lo preguntamos ya.',
    deepTitle: 'Profundizar',
    deepSubtitle: 'Opcional. Cuanto más nos cuentes, más se afinan las estimaciones.',
    deepSection: {
      hair_now: 'Tu cabello ahora',
      chemical_history: 'Historial químico',
      mechanical_history: 'Calor y peinados',
      products: 'Productos y hábitos',
      sleep: 'Cómo duermes',
      environment: 'Dónde vives',
    },
    sectionDone: 'Completada',
    sectionPending: 'Sin empezar',
  },

  depth: {
    title: 'Cuánto detalle quieres ver',
    body: 'Puedes cambiarlo cuando quieras. Nada desaparece: solo deja de estar a la vista.',
    basic: 'Básico',
    basicHint: 'Lo esencial, sin tecnicismos.',
    intermediate: 'Intermedio',
    intermediateHint: 'Añade técnicas avanzadas y detalle de ingredientes.',
    advanced: 'Avanzado',
    advancedHint: 'Todo: experimentos, INCI completo y las reglas que usamos.',
  },

  zone: {
    frontal_hairline: 'Línea frontal',
    bangs: 'Flequillo',
    front_left: 'Frontal izquierda',
    front_right: 'Frontal derecha',
    left_temple: 'Sien izquierda',
    right_temple: 'Sien derecha',
    side_upper_left: 'Lateral superior izquierdo',
    side_upper_right: 'Lateral superior derecho',
    side_lower_left: 'Lateral inferior izquierdo',
    side_lower_right: 'Lateral inferior derecho',
    crown: 'Coronilla',
    back_crown: 'Coronilla posterior',
    occipital: 'Occipital',
    nape: 'Nuca',
    ends: 'Puntas',
  },

  zoneDetail: {
    title: 'Mapa capilar',
    subtitle: 'Cada zona puede comportarse distinto. Aquí está lo que sabemos de cada una.',
    notObserved: 'Sin datos todavía',
    notPhotographed: 'No aparecía en tus fotos',
    correct: 'Corregir',
    corrected: 'Corregido por ti',
    estimatedBy: 'Estimado a partir de %{source}',
    fields: {
      pattern: 'Patrón',
      curl_diameter_mm: 'Diámetro de rizo',
      curve_frequency_per_cm: 'Frecuencia de curva',
      strand_diameter: 'Grosor de hebra',
      density: 'Densidad',
      porosity: 'Porosidad',
      elasticity: 'Elasticidad',
      frizz_level: 'Frizz',
      definition_level: 'Definición',
      uniformity: 'Uniformidad',
      clumping: 'Agrupamiento',
      shrinkage_ratio: 'Encogimiento',
      length_cm: 'Longitud',
      processing: 'Procesado',
    },
  },

  confidence: {
    evidenceLabel: 'Solidez de la recomendación',
    personalLabel: 'Respaldo de tus datos',
    sampleSize: {
      zero: 'Todavía no tenemos registros tuyos sobre esto',
      one: 'Basado en 1 registro tuyo',
      other: 'Basado en %{count} registros tuyos',
    },
    // La distinción que define el producto (docs/03-POSITIONING.md §3).
    explainer:
      'Son dos cosas distintas: qué tan sólida es la regla en general, y cuánto la respaldan tus propios resultados.',
    contradicts: 'Tus registros apuntan justo en la dirección contraria',
    coldStart: 'Todavía estamos aprendiendo cómo se comporta tu cabello',
  },

  evidence: {
    scientific_evidence: 'Evidencia científica',
    professional_consensus: 'Consenso profesional',
    extended_anecdote: 'Experiencia extendida',
    unsupported_trend: 'Mito frecuente',
  },

  uncertainty: {
    cold_start: 'Todavía no tenemos historial tuyo',
    small_sample: 'Pocos registros: puede cambiar',
    mixed_personal_results: 'Tus resultados están repartidos',
    anecdotal_rule: 'La regla general es anecdótica, no está medida',
    uncontrolled_observations: 'Son observaciones sueltas, no un experimento',
    contradicts_your_history: 'Contradice lo que vemos en tus registros',
    no_image_analysis: 'Esto no lo estimamos con las fotos',
    estimates_need_confirmation: 'Falta que lo confirmes tú',
    some_photos_unusable: 'Alguna foto no se pudo usar',
    missing_angles: 'Faltan ángulos por fotografiar',
    correlation_not_causation: 'Es una coincidencia observada, no una causa demostrada',
    projection_is_not_a_prediction: 'Es una proyección de tu historial, no una predicción',
    no_basis_for_projection: 'No tenemos base para responder a esto todavía',
    water_estimated_not_measured: 'La dureza del agua está estimada, no medida',
    unverified_product_attributes: 'Hay atributos del producto que no pudimos comprobar',
    weather_is_not_your_history: 'Es el clima previsto, no tu historial',
    formulation_details_unknown: 'No conocemos las concentraciones exactas',
    no_catalog_coverage: 'No tenemos productos suficientes de esta categoría',
    no_personal_history: 'Sin historial propio todavía',
    reference_profile_only: 'Basado en perfiles parecidos, no en el tuyo',
    not_your_history: 'No son tus datos',
    experiment_incomplete: 'Al experimento le faltan repeticiones',
    small_sample_experiment: 'Un experimento con pocas repeticiones',
    growth_rate_assumed_not_measured: 'El ritmo de crecimiento está estimado, no medido',
    home_measurement: 'Medición casera: varía según cómo estires el pelo',
    only_two_measurements: 'Solo hay dos mediciones',
    short_period: 'El periodo es corto para sacar conclusiones',
    difference_within_noise: 'La diferencia cabe dentro del margen de variación',
  },

  scan: {
    title: 'Mapa capilar',
    intro:
      'Vamos a fotografiar tu cabello por zonas. Solo se analiza lo que fotografíes: lo que no salga, lo diremos.',
    consentTitle: 'Antes de empezar',
    consentBody:
      'Para analizar las fotos necesitamos tu permiso explícito. Puedes retirarlo cuando quieras y el resto de la app sigue funcionando igual.',
    consentAccept: 'Doy permiso para analizar mis fotos',
    cropFaceOption: 'Recortar el rostro antes de subir',
    cropFaceHint: 'No hace falta el rostro para analizar el cabello.',
    angle: {
      front: 'Frente',
      crown_top: 'Coronilla desde arriba',
      left_side: 'Lateral izquierdo',
      right_side: 'Lateral derecho',
      back: 'Nuca y parte de atrás',
      nape: 'Nuca de cerca',
      ends_closeup: 'Puntas de cerca',
      strand_closeup: 'Una hebra de cerca',
    },
    required: 'Necesaria',
    optionalAngle: 'Opcional',
    covers: 'Cubre %{count} zonas',
    quality: {
      too_blurry: 'Salió movida. Apoya el brazo y vuelve a intentarlo.',
      underexposed: 'Hay poca luz. Acércate a una ventana si puedes.',
      overexposed: 'Hay zonas quemadas por la luz. Prueba sin luz directa.',
      low_resolution: 'La imagen es demasiado pequeña para analizarla.',
      low_contrast: 'Se distingue poco el detalle del cabello.',
      possible_filter: 'Parece llevar un filtro. Sin filtro el análisis es más fiable.',
      subject_too_small: 'El cabello ocupa muy poco de la foto.',
    },
    retakeOnly: 'Solo hay que repetir %{count}',
    allGood: 'Todas las fotos sirven',
    analysing: 'Analizando',
    noVisionModel:
      'Ahora mismo no analizamos la imagen: estas estimaciones vienen de tus respuestas, no de las fotos.',
    confirmTitle: 'Revisa antes de guardar',
    confirmBody:
      'Nada de esto entra en tu perfil hasta que lo confirmes. Si algo no cuadra, corrígelo: tu corrección manda sobre nuestra estimación, siempre.',
  },

  routine: {
    title: 'Tu rutina',
    generate: 'Generar rutina',
    totalMinutes: '%{minutes} min aprox.',
    inZones: 'En %{zones}',
    amount: 'Cantidad',
    technique: 'Técnica',
    thenAlso: 'Y después',
    quickModes: 'Tengo poco tiempo',
    quick5: '5 min',
    quick10: '10 min',
    quick20: '20 min',
    skipped: 'Lo que dejamos fuera por tiempo',
    noSteps: 'Todavía no hay suficiente información para generar una rutina.',
    stepTitle: {
      cleanse: 'Lavar',
      clarify: 'Limpieza profunda',
      chelate: 'Quelar',
      condition: 'Acondicionar',
      deep_condition: 'Mascarilla',
      protein: 'Aporte de proteína',
      detangle: 'Desenredar',
      leave_in: 'Sin aclarado',
      cream: 'Crema',
      gel: 'Gel',
      dry: 'Secar',
      refresh: 'Refrescar',
      night: 'Antes de dormir',
    },
  },

  amount: {
    ref: {
      few_drops: 'unas gotas',
      pea: 'un guisante',
      chickpea: 'un garbanzo',
      almond: 'una almendra',
      coin: 'una moneda',
      teaspoon: 'una cucharadita',
      walnut: 'una nuez',
      tablespoon: 'una cucharada',
      golf_ball: 'una pelota de golf',
      palmful: 'la palma llena',
    },
    times: '%{count} × %{reference}',
  },

  goal: {
    definition: 'Definición',
    volume: 'Volumen',
    frizz_control: 'Menos frizz',
    hydration: 'Hidratación',
    damage_recovery: 'Recuperar cabello dañado',
    length_retention: 'Conservar longitud',
    scalp_comfort: 'Cuero cabelludo cómodo',
    chemical_transition: 'Transición química',
    preserve_style: 'Que dure más',
    low_maintenance: 'Menos mantenimiento',
    shine: 'Brillo',
    clumping: 'Rizos más agrupados',
  },

  inventory: {
    title: 'Lo que ya tienes',
    // La promesa anti-consumista, dicha explícitamente (A15).
    subtitle: 'Antes de recomendarte comprar nada, miramos aquí.',
    empty: 'Añade lo que tengas en casa. No hace falta que sea todo.',
    add: 'Añadir producto',
    alreadyOwned: 'Ya lo tienes',
    alreadyOwnedBody: 'Lo que tienes cumple lo que hace falta para este paso. No necesitas comprar nada.',
    ownedPartial: 'Casi sirve',
    ownedPartialBody: 'Lo que tienes cumple casi todo. Le falta: %{missing}.',
    needsProduct: 'Aquí sí falta algo',
    duplicateWarning: 'Ya tienes %{count} de esta categoría',
    expiresOn: 'Conviene usarlo antes de %{date}',
    expired: 'Pasado de fecha desde %{date}',
    amountLeft: 'Queda %{percent}%',
    disliked: 'No te gustó',
  },

  ingredients: {
    title: 'Analizar ingredientes',
    paste: 'Pega la lista INCI del envase',
    byFunction: 'Por función',
    unrecognised: 'No reconocimos %{count} ingredientes',
    unrecognisedHint: 'No cuentan ni a favor ni en contra: simplemente no los conocemos.',
    sensitivityMatch: 'Coincide con algo que registraste como sensibilidad',
    function: {
      anionic_surfactant: 'Tensioactivo fuerte',
      amphoteric_surfactant: 'Tensioactivo suave',
      nonionic_surfactant: 'Tensioactivo muy suave',
      cationic_conditioner: 'Acondicionador catiónico',
      emollient: 'Emoliente',
      occlusive: 'Oclusivo',
      humectant: 'Humectante',
      film_former: 'Formador de película',
      hydrolysed_protein: 'Proteína hidrolizada',
      silicone_soluble: 'Silicona soluble en agua',
      silicone_insoluble: 'Silicona no soluble',
      chelator: 'Quelante',
      preservative: 'Conservante',
      solvent: 'Disolvente',
      alcohol_drying: 'Alcohol de cadena corta',
      alcohol_fatty: 'Alcohol graso',
      oil_penetrating: 'Aceite que penetra',
      oil_sealing: 'Aceite que sella',
      uv_filter: 'Filtro UV',
      ph_adjuster: 'Ajustador de pH',
      fragrance: 'Fragancia',
      colourant: 'Colorante',
      thickener: 'Espesante',
      other: 'Sin clasificar',
    },
  },

  journal: {
    title: 'Diario',
    subtitle: 'Cada registro hace que las recomendaciones se parezcan más a ti.',
    empty: 'Todavía no has registrado ningún día de lavado.',
    newEntry: 'Registrar un lavado',
    rateDay: 'Día %{day}',
    rating: {
      1: 'Mal',
      2: 'Regular',
      3: 'Bien',
      4: 'Muy bien',
    },
    lastedDays: 'Aguantó %{count} días',
    stillLearning: 'Todavía estamos aprendiendo cómo se comporta tu cabello',
    stillLearningBody:
      'Con unos cuantos registros más podremos empezar a ver patrones tuyos de verdad.',
  },

  learning: {
    title: 'Lo que vemos en tus datos',
    strength: {
      insufficient_data: 'Sin datos suficientes',
      suggestive: 'Indicio',
      consistent: 'Constante',
      strong: 'Claro',
    },
    uncontrolledIntro: 'Ojo con esto: hubo variables que no estaban igualadas.',
    uncontrolled: {
      dew_point: 'El clima no era comparable entre los dos grupos',
      dew_point_missing: 'Faltan datos de clima en algunos registros',
      other_products: 'Cambiaron también otros productos',
      techniques: 'Cambiaron también las técnicas',
    },
    turnIntoExperiment: 'Convertirlo en experimento',
  },

  twin: {
    title: 'Cómo se comporta tu cabello',
    subtitle: 'Lo que hemos aprendido de tus registros. Crece contigo.',
    completeness: 'Conocemos %{percent}% de lo que seguimos',
    trait: {
      humidity_sensitivity: 'Sensibilidad a la humedad',
      protein_tolerance: 'Tolerancia a la proteína',
      style_longevity_days: 'Cuánto le dura el peinado',
      product_load_tolerance: 'Cuánto producto admite',
      drying_speed: 'Velocidad de secado',
      heat_sensitivity: 'Sensibilidad al calor',
      buildup_speed: 'Rapidez de acumulación',
      refresh_response: 'Respuesta al refresh',
    },
    unknownTrait: 'Aún no lo sabemos',
    projectTitle: '¿Qué pasa si...?',
    scenario: {
      higher_humidity: 'Sube la humedad',
      lower_humidity: 'Baja la humedad',
      more_product: 'Uso más producto',
      less_product: 'Uso menos producto',
      add_protein: 'Añado proteína',
      skip_gel: 'Me salto el gel',
      stretch_wash_day: 'Estiro el lavado un día más',
      refresh_instead_of_wash: 'Refresco en vez de lavar',
    },
    direction: {
      likely_better: 'Probablemente mejor',
      likely_worse: 'Probablemente peor',
      likely_similar: 'Probablemente parecido',
      unknown: 'No lo sabemos todavía',
    },
    unlock: {
      log_five_wash_days: 'Registra cinco días de lavado',
      log_across_different_weather: 'Registra en climas distintos',
      log_amounts_used: 'Apunta cuánto producto usas',
      vary_the_amount_deliberately: 'Prueba a variar la cantidad a propósito',
      run_protein_experiment: 'Haz un experimento con proteína',
      rate_days_2_and_3: 'Valora también los días 2 y 3',
      try_a_refresh_and_log_it: 'Prueba un refresh y regístralo',
    },
  },

  experiment: {
    title: 'Experimentos',
    subtitle: 'En vez de creernos, compruébalo con tu propio cabello.',
    create: 'Diseñar un experimento',
    controlledVariables: 'Lo que mantendrás igual',
    repetitions: '%{done} de %{planned} repeticiones',
    reading: {
      not_enough_yet: 'Todavía faltan repeticiones',
      inconclusive: 'No hay diferencia clara',
      conclusive: 'Hay una diferencia clara',
      invalid: 'Este experimento no se puede leer',
    },
    invalidBody: 'Alguna variable que ibas a mantener igual cambió entre los dos grupos.',
    tieBody: 'La diferencia cabe dentro de la variación normal. Con estos datos, empatan.',
  },

  education: {
    title: 'Aprender',
    mythsTitle: 'Mitos frecuentes',
    mythsSubtitle: 'Cosas que circulan mucho y no se sostienen. Con el porqué.',
    rulesTitle: 'En qué nos basamos',
    rulesSubtitle: 'Todas las reglas que usamos, con su nivel de evidencia y su mecanismo.',
    mechanism: 'Por qué ocurre',
  },

  safety: {
    referralBlockTitle: 'Esto se sale de lo que esta app puede analizar',
    referralBlock:
      'No podemos estimar qué es ni recomendarte nada al respecto. Lo que estás describiendo conviene que lo vea en persona un profesional de la salud. No es necesariamente una urgencia, pero sí algo que una app de cuidado cosmético no debe interpretar.',
    cosmeticOnly:
      'Trichon es una app cosmética y educativa. No sustituye la valoración de un profesional de la salud.',
  },

  privacy: {
    title: 'Tus datos',
    photosTitle: 'Tus fotos',
    photosBody:
      'Se guardan cifradas y solo tú accedes a ellas. Puedes borrarlas, y borrar la cuenta entera, cuando quieras.',
    consent: {
      terms: 'Términos de uso',
      privacy: 'Política de privacidad',
      photo_processing: 'Analizar mis fotos para generar mi análisis',
      model_training: 'Usar mis fotos para mejorar los modelos',
      stylist_sharing: 'Compartir un informe con un profesional',
      anonymous_aggregate: 'Aportar resultados anónimos de mis experimentos',
    },
    modelTrainingHint: 'Está desactivado. Dejarlo así no quita ninguna función.',
    deleteAccount: 'Eliminar mi cuenta',
    deleteAccountBody: 'Se borra todo: perfil, fotos, diario e historial. No se puede deshacer.',
  },

  match: {
    already_owned: 'Ya tienes lo que hace falta',
    owned_partial: 'Lo que tienes sirve casi del todo',
    needs_product: 'Para este paso te falta algo',
    no_data: 'No tenemos datos suficientes para decidir',
    matchedAttributes: 'Coincide en',
    mismatchedAttributes: 'No coincide en',
    unknownAttributes: 'No pudimos comprobar',
  },

  coldStart: {
    based_on_similar_profiles: 'Basado en perfiles parecidos al tuyo',
    general_consensus_only: 'Basado en consenso cosmético general',
    referenceHint:
      'No son tus datos: son de %{count} perfiles con características parecidas. Cuando tengas historial propio, esto cambia.',
    stage: {
      no_data: 'Acabas de empezar',
      first_steps: 'Primeros registros',
      early_pattern: 'Empiezan a verse cosas',
      learning: 'Aprendiendo de ti',
      established: 'Con historial sólido',
    },
  },

  milestone: {
    complete_first_scan: 'Haz tu primer mapa capilar',
    log_first_wash_day: 'Registra tu primer lavado',
    add_what_you_already_own: 'Añade lo que ya tienes en casa',
    log_day_2_result: 'Valora también el día 2',
    complete_zone_map: 'Completa el mapa de zonas',
    log_three_more: 'Registra tres lavados más',
    try_one_technique_change: 'Prueba a cambiar una técnica',
    run_first_experiment: 'Haz tu primer experimento',
    compare_photos: 'Compara tus fotos',
    review_your_twin: 'Revisa lo que sabemos de tu cabello',
  },

  weather: {
    title: 'El tiempo y tu pelo',
    dewPoint: 'Punto de rocío %{value}°',
    // El insight que diferencia de las apps que miran humedad relativa.
    dewPointHint:
      'Miramos el punto de rocío, no la humedad relativa: 80% a 5° y 80% a 28° son cantidades de agua muy distintas.',
    band: {
      very_dry: 'Muy seco',
      dry: 'Seco',
      comfortable: 'Templado',
      humid: 'Húmedo',
      very_humid: 'Muy húmedo',
    },
    advice: {
      reduce_humectants: 'Baja los humectantes hoy',
      increase_film_forming: 'Sube la fijación para sellar la forma',
      increase_emollients: 'Sube los emolientes',
      humectants_may_backfire: 'Con este aire, los humectantes pueden secar en vez de hidratar',
      uv_cover_or_filter: 'Si vas a estar al sol, cúbrelo o usa filtro',
      protective_style_for_wind: 'Con este viento, un recogido evita mucho enredo',
      no_adjustment_needed: 'Hoy no hace falta cambiar nada',
    },
  },


  plan: {
    free: 'Gratis',
    studio: 'Trichon Estudio',
    pro: 'Trichon Pro',
    currentPlan: 'Tu plan',
    renews: 'Se renueva el %{date}',
    endsOn: 'Activo hasta el %{date}',
    notRenewing: 'No se renovará. Sigues teniendo todo hasta esa fecha.',
    upgrade: 'Pasar a Estudio',
    cancel: 'Cancelar la renovación',
    // La promesa que más importa dejar visible.
    alwaysIncludedTitle: 'Esto no se limita nunca',
    alwaysIncludedBody:
      'Tus datos son tuyos en cualquier plan. Si cancelas, conservas todo tu historial y puedes exportarlo.',
    remaining: 'Te quedan %{count} de %{limit} este mes',
    unlimited: 'Sin límite',
    notIncluded: 'No está en tu plan',
    periodResets: 'El cupo se renueva el %{date}',
    whatYouGet: 'Qué incluye',
  },

  feature: {
    scan: 'Mapa capilar',
    scalp_scan: 'Análisis de cuero cabelludo',
    ingredient_scan: 'Análisis de ingredientes',
    assistant_query: 'Preguntas al asistente',
    active_experiment: 'Experimentos a la vez',
    active_routine: 'Rutinas guardadas',
    twin_projection: 'Proyecciones "¿qué pasa si...?"',
    stylist_report: 'Informe para tu estilista',
    extended_history: 'Historial más allá de 6 meses',
    product_comparison: 'Comparar productos',
    journal_entry: 'Diario',
    inventory_item: 'Inventario',
    explanation: '"¿Por qué esto?"',
    education: 'Enciclopedia y mitos',
    zone_correction: 'Corregir tus zonas',
    data_export: 'Exportar tus datos',
  },

  entitlement: {
    allowed: 'Disponible',
    quota_exhausted: {
      scan: 'Has usado tus %{limit} mapas de este mes. El cupo se renueva el %{period_end}.',
      ingredient_scan: 'Has usado tus %{limit} análisis de ingredientes este mes.',
      assistant_query: 'Has usado tus %{limit} preguntas de este mes.',
      active_experiment: 'Ya tienes un experimento en marcha. Termínalo o pásate a Estudio.',
      twin_projection: 'Has usado tus %{limit} proyecciones de este mes.',
      product_comparison: 'Has usado tus %{limit} comparaciones de este mes.',
    },
    not_in_plan: {
      scalp_scan: 'El análisis de cuero cabelludo está en Estudio.',
      stylist_report: 'El informe para estilista está en Estudio.',
      extended_history: 'Ver más de 6 meses de historial está en Estudio.',
    },
  },

  cronograma: {
    title: 'Cronograma capilar',
    subtitle: 'Agua, lípidos y proteína son tres carencias distintas.',
    step: {
      hydration: 'Hidratación',
      nutrition: 'Nutrición',
      reconstruction: 'Reconstrucción',
    },
    label_matches: 'La etiqueta y los ingredientes coinciden',
    label_differs_from_inci:
      'La etiqueta dice %{declared}, pero por los ingredientes se parece más a %{inferred}.',
    covers_several_steps: 'Cubre varios pasos a la vez, aunque la etiqueta nombre solo uno',
    no_declared_step: 'El envase no declara paso',
    cannot_verify: 'No podemos deducirlo de la lista de ingredientes',
    // El matiz que evita convertir el cronograma en dogma.
    calendarNote:
      'Lo que se sostiene es la distinción entre las tres carencias. El calendario fijo de días asignados no: cuánta proteína admite tu cabello depende de tu porosidad y tu historial, no del día de la semana.',
  },


  growth: {
    title: 'Crecimiento y retención',
    // La distinción que da sentido a toda la pantalla.
    subtitle:
      'No son lo mismo. El cabello crece en el folículo a un ritmo bastante estable; lo que sí puedes cambiar es cuánto conservas antes de que se rompa.',
    notEnough: 'Todavía no hay mediciones suficientes',
    hint: {
      measure_every_two_months: 'Mide cada dos meses, no cada semana',
      measure_the_same_way: 'Mide siempre igual: mismo punto, mismo estiramiento',
    },
    grewTotal: 'Creció %{cm} cm',
    kept: 'Conservaste %{cm} cm',
    lost: 'Se perdieron %{cm} cm por rotura',
    trimmed: 'Cortaste %{cm} cm a propósito',
    retention: 'Retención %{percent}%',
    perMonth: '%{cm} cm al mes',
    measured: 'Medido en la raíz',
    assumed: 'Estimado, no medido',
    // El matiz que evita que la app afirme más de lo que sabe.
    assumedHint:
      'La longitud de las puntas no puede distinguir "crece poco" de "crece normal y se rompe". Si tienes el pelo teñido, mide desde el cuero cabelludo hasta la línea de color y sabremos cuál de las dos es.',
    retentionProblem: 'Tu cabello crece bien; lo que cuesta es conservarlo',
    retentionProblemBody:
      'Ahí sí se puede hacer algo: bajar tensión, desenredar en húmedo desde las puntas y revisar el calor.',
    healthy: 'Estás conservando casi todo lo que crece',
  },

  error: {
    generic: 'Algo no ha ido bien.',
    internal: 'Ha fallado algo por nuestra parte. Vuelve a intentarlo en un momento.',
    network: 'No hay conexión. Lo que hagas se guarda y se sincroniza luego.',
    unauthorized: 'Tu sesión ha caducado. Vuelve a entrar.',
    missing_token: 'Necesitas iniciar sesión.',
    token_expired: 'Tu sesión ha caducado.',
    invalid_token: 'Tu sesión ya no es válida.',
    token_revoked: 'Esa sesión ya se cerró.',
    account_unavailable: 'No pudimos acceder a tu cuenta.',
    invalid_credentials: 'El correo o la contraseña no coinciden.',
    email_taken: 'Ya hay una cuenta con ese correo.',
    minimum_age: 'Por ahora Trichon es para mayores de %{minimum_age} años.',
    terms_and_privacy_required: 'Necesitamos que aceptes los términos y la política de privacidad.',
    consent_required: 'Para esto necesitamos tu permiso explícito.',
    cannot_revoke_required_consent:
      'Sin esto no se puede usar la app. Si quieres retirarlo, puedes eliminar la cuenta.',
    unknown_consent_purpose: 'No reconocemos ese permiso.',
    unknown_goal: 'No reconocemos ese objetivo.',
    unknown_pattern: 'No reconocemos ese patrón.',
    unknown_section: 'No reconocemos esa sección.',
    unknown_depth_level: 'No reconocemos ese nivel.',
    unknown_zone: 'No reconocemos esa zona.',
    unknown_angle: 'No reconocemos ese ángulo.',
    unknown_category: 'No reconocemos esa categoría.',
    unknown_scenario: 'No reconocemos ese escenario.',
    unknown_routine_kind: 'No reconocemos ese tipo de rutina.',
    unknown_damage_sign: 'No reconocemos alguno de esos signos.',
    unknown_rating_key: 'No reconocemos alguna de esas valoraciones.',
    rating_out_of_range: 'Las valoraciones van del 1 al 4.',
    field_not_measurable: 'Ese campo no se puede corregir.',
    unreadable_image: 'No pudimos leer esa imagen.',
    image_too_large: 'Esa imagen pesa demasiado.',
    scan_has_no_photos: 'Este mapa todavía no tiene fotos.',
    scan_photos_unreadable: 'No pudimos leer las fotos de este mapa.',
    scan_not_ready_for_confirmation: 'Este mapa todavía no está listo para confirmar.',
    empty_inci: 'Pega la lista de ingredientes para poder analizarla.',
    inventory_needs_product_or_name: 'Dinos al menos el nombre y la categoría.',
    experiment_needs_two_arms: 'Un experimento necesita al menos dos cosas que comparar.',
    free_tier_experiment_limit: 'Con el plan gratuito puedes tener %{limit} experimento a la vez.',
    too_many_products_to_compare: 'Puedes comparar hasta %{limit} productos a la vez.',
    not_found: {
      zone: 'No encontramos esa zona.',
      scan: 'No encontramos ese mapa.',
      hair_profile: 'Todavía no tienes perfil.',
      journal_entry: 'No encontramos ese registro.',
      experiment: 'No encontramos ese experimento.',
      inventory_item: 'No encontramos ese producto en tu inventario.',
    },
  },

  meta: {
    cosmetic_educational_only:
      'Trichon es una app cosmética y educativa. No diagnostica ni sustituye la valoración de un profesional de la salud.',
  },
} as const;

/**
 * Ensancha los literales de `as const` a `string`, conservando la estructura
 * de claves. Así `en.ts` está obligado a tener exactamente las mismas claves
 * — un olvido rompe el typecheck — sin exigir que el texto inglés sea
 * literalmente el español.
 */
type WidenLeaves<T> = T extends string
  ? string
  : T extends number
    ? number
    : { [K in keyof T]: WidenLeaves<T[K]> };

export type Catalog = WidenLeaves<typeof es>;
