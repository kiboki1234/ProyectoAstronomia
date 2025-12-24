# MULTIAGENT_DEV_SPEC v0.1 — OrbitalSkyShield

## 1) Propósito
Construir una plataforma open-source para:
- **A)** detectar y mitigar rastros/artefactos de satélites en datos astronómicos (FITS),
- **B)** estimar y reportar la contribución difusa al brillo de cielo (“ODC”: Orbital Diffuse Contribution) con incertidumbre.

Este documento define: alcance del MVP, arquitectura modular, contratos de E/S, roles de agentes, “Definition of Done”, y el plan de trabajo.

---

## 2) Alcance del MVP (Release 0.1)
### Entradas mínimas
- Carpeta con imágenes **FITS** (2D), con headers estándar.
- Parámetros del sitio e instrumento (archivo `config.yaml`).

### Salidas mínimas por frame
- `mask.fits`: máscara binaria (1=contaminado, 0=limpio).
- `quality.json`: métricas por frame (área afectada, severidad, flags).

### Salidas mínimas por noche/carpeta
- `night_summary.json`: agregados y métricas globales.
- `odc_report.json`: estimación inicial ODC (modelo simple + incertidumbre básica).

### Lo que NO entra en el MVP
- Limpieza/inpainting “cleaned.fits” (opcional para v0.2).
- Integración con catálogos orbitales externos (v1.0).
- Soporte de espectros (v1.x).

---

## 3) Repositorio y módulos
Estructura recomendada:

```
orbitalskyshield/
  pyproject.toml
  README.md
  LICENSE
  config/
    default_config.yaml
  core/
    io_fits.py
    wcs_utils.py
    logging.py
    types.py
  streak_detection/
    model_interface.py
    baseline_detector.py
    postprocess.py
  mitigation/
    masking.py
  skyglow/
    odc_estimator.py
    background_model.py
  metrics/
    frame_metrics.py
    night_metrics.py
  cli/
    main.py
    commands/
      run_pipeline.py
  api/
    pipeline.py
  datasets/
    synthetic/
      generator.py
      examples/
  benchmarks/
    evaluate.py
    metrics_definitions.md
  tests/
    test_io.py
    test_masks.py
    test_cli.py
  docs/
    architecture.md
    user_guide.md
    developer_guide.md
```

Lenguaje: **Python** (MVP). Enfoque científico reproducible.

---

## 4) Contratos de datos (E/S) — obligatorios

### 4.1 `mask.fits`
- Tipo: FITS 2D, misma forma que la imagen.
- Valores: `uint8` o `bool`.
  - `1` = píxel contaminado por rastro/artefacto
  - `0` = píxel limpio
- Header: copiar header base + añadir:
  - `OSS_MASK= T`
  - `OSS_VER = "0.1"`

### 4.2 `quality.json` (por frame)
Esquema mínimo:

```json
{
  "file": "frame001.fits",
  "timestamp_utc": "2025-12-23T03:10:22Z",
  "streak_area_fraction": 0.0123,
  "num_streaks": 2,
  "severity_score": 0.67,
  "flags": ["SAT_STREAK_DETECTED"],
  "detector": {
    "name": "baseline_detector",
    "version": "0.1",
    "params": { "threshold_sigma": 5.0 }
  }
}
```

### 4.3 `night_summary.json` (por carpeta)
```json
{
  "dataset_id": "2025-12-23_siteX_filterR",
  "n_frames": 120,
  "affected_frames": 38,
  "median_streak_area_fraction": 0.006,
  "p95_streak_area_fraction": 0.021,
  "severity_histogram": { "0-0.2": 40, "0.2-0.4": 50, "0.4-0.6": 20, "0.6-0.8": 10, "0.8-1.0": 0 }
}
```

### 4.4 `odc_report.json` (MVP)
ODC es una estimación inicial del incremento difuso. En MVP será un modelo simple (residuales de fondo, controlando parámetros básicos).

```json
{
  "dataset_id": "2025-12-23_siteX_filterR",
  "odc_percent": 7.8,
  "odc_ci95": [4.1, 11.9],
  "method": "mvp_background_residual",
  "assumptions": [
    "background estimated via robust median filtering",
    "frames with high streak contamination downweighted"
  ],
  "quality": {
    "fit_status": "ok",
    "notes": []
  }
}
```

---

## 5) API interna (contratos de código)
### 5.1 Tipos comunes (`core/types.py`)
- `FrameData`: imagen (numpy), header, path, timestamp.
- `MaskData`: máscara (numpy), metadata.
- `FrameQuality`: dict validado.
- `NightReport`: dict validado.

### 5.2 Pipeline (SDK) (`api/pipeline.py`)
Funciones obligatorias:

- `run_on_folder(input_dir: str, output_dir: str, config_path: str) -> None`
- `process_frame(frame: FrameData, config: dict) -> tuple[MaskData, FrameQuality]`
- `aggregate_night(frame_qualities: list[FrameQuality]) -> dict`
- `estimate_odc(frames: list[FrameData], qualities: list[FrameQuality], config: dict) -> dict`

---

## 6) CLI (obligatorio para MVP)
Comando principal:

```bash
oss run --input ./data/fits --output ./out --config ./config/site.yaml
```

Debe producir:
- `./out/masks/*.fits`
- `./out/quality/*.json`
- `./out/night_summary.json`
- `./out/odc_report.json`
- logs en `./out/run.log`

---

## 7) Métricas y evaluación (MVP)
### 7.1 Evaluación del detector (si hay truth sintético)
- IoU de máscaras
- Precision/Recall de píxel
- Recall de streaks (por trazo)

### 7.2 Calidad operativa
- % de frames afectados
- área afectada mediana y p95
- severidad (0–1) definida como función de:
  - fracción de área,
  - brillo relativo del trazo,
  - cercanía a regiones de interés (opcional v0.2)

### 7.3 Validación de ODC (MVP)
- Consistencia temporal: ODC no debe oscilar sin explicación cuando condiciones son similares.
- Sensibilidad: ODC debe bajar cuando se descartan frames con alto residuo de fondo no relacionado.

---

## 8) Reglas de ingeniería (calidad mínima)
- Formato: `ruff` + `black`.
- Tipado: `mypy` en módulos core/API.
- Tests: `pytest` (mínimo: IO FITS, generación de máscara, CLI smoke test).
- CI: GitHub Actions con:
  - lint + tests,
  - empaquetado básico.

---

## 9) Protocolo de multiagentes (cómo trabajan)
### 9.1 Fuente única de verdad
- Este documento + `docs/architecture.md` + `config/default_config.yaml`.

### 9.2 Handoffs obligatorios
Cada agente entrega:
- PR con código + tests + doc corta.
- Un “handoff note” en el PR:
  - qué hizo,
  - cómo usarlo,
  - contratos que consume/produce,
  - limitaciones.

### 9.3 Política de cambios
- Cambios a contratos JSON/FITS: solo el “Tech Lead Agent” aprueba.
- Todo módulo debe exponer una interfaz estable (funciones en `api/pipeline.py` o su equivalente).

---

## 10) Roles de agentes (multiagentes)

### Agente 0 — Tech Lead / Orchestrator (prioridad máxima)
**Objetivo:** mantener coherencia global, contratos, roadmap.  
**Entregables:**
- scaffolding repo + CI + `pyproject.toml`
- `docs/architecture.md`
- decisiones de interfaces y versionado  
**DoD:**
- proyecto instala (`pip install -e .`)
- CLI existe y ejecuta aunque sea con detector baseline.

---

### Agente 1 — Core I/O FITS + WCS
**Objetivo:** lectura/escritura robusta FITS, manejo de headers, timestamps.  
**Tareas:**
- `core/io_fits.py`: `read_fits(path) -> FrameData`, `write_fits(path, array, header)`
- extracción de timestamp de header (fallback: filename).  
**DoD:**
- tests con FITS de ejemplo
- escritura de `mask.fits` preserva dimensiones y header base.

---

### Agente 2 — Detector baseline (no-ML) + postproceso
**Objetivo:** entregar detección funcional sin entrenamiento.  
**Enfoque MVP:**
- filtro de realce + umbral robusto (sigma-clipping) + detección de segmentos lineales (Hough o morfología).  
**Archivos:**
- `streak_detection/baseline_detector.py`
- `streak_detection/postprocess.py`  
**DoD:**
- produce `MaskData` consistente
- genera `num_streaks` aproximado
- funciona en imágenes sintéticas del agente de datasets.

---

### Agente 3 — Métricas por frame + calidad
**Objetivo:** computar `quality.json`.  
**Tareas:**
- `metrics/frame_metrics.py`: área afectada, severidad, flags.
- define `severity_score` determinista y documentada.  
**DoD:**
- `quality.json` cumple esquema
- tests: valores correctos en casos sintéticos.

---

### Agente 4 — Agregación por noche
**Objetivo:** `night_summary.json`.  
**Tareas:**
- `metrics/night_metrics.py`: medianas, p95, histogramas.  
**DoD:**
- resumen correcto para lista de `FrameQuality`.

---

### Agente 5 — ODC Estimator (MVP)
**Objetivo:** estimación inicial de ODC reproducible.  
**Enfoque MVP (pragmático):**
- estimar fondo por frame (robusto) tras enmascarar streaks,
- modelar “residuo” agregado por noche,
- producir ODC% con bootstrap simple para CI95.  
**Archivos:**
- `skyglow/background_model.py`
- `skyglow/odc_estimator.py`  
**DoD:**
- `odc_report.json` se genera siempre (aunque con warnings)
- CI95 presente.

---

### Agente 6 — Datasets sintéticos + generador de truth
**Objetivo:** dataset mínimo para pruebas.  
**Tareas:**
- `datasets/synthetic/generator.py`: crear imagen base (ruido + estrellas simples) + streaks paramétricos + máscara truth.
- guardar FITS + truth mask.  
**DoD:**
- se puede generar un set de 50 frames reproducible por seed
- truth mask alineada con la imagen.

---

### Agente 7 — CLI + UX
**Objetivo:** comando `oss run`.  
**Tareas:**
- `cli/main.py` con `argparse`/`typer`.
- manejo de directorios, outputs, logs.  
**DoD:**
- `oss run` ejecuta pipeline completo en dataset sintético.

---

### Agente 8 — QA/CI + Release
**Objetivo:** garantizar calidad y automatización.  
**Tareas:**
- GitHub Actions, lint/test, artefactos.
- smoke tests del CLI.  
**DoD:**
- PRs bloqueados si fallan tests.
- build reproducible.

---

### Agente 9 — Documentación y adopción (open-source)
**Objetivo:** documentación mínima para usuarios y contribuidores.  
**Tareas:**
- `README.md` con quickstart.
- `docs/user_guide.md` y `docs/developer_guide.md`.
- ejemplo end-to-end con dataset sintético.  
**DoD:**
- cualquier persona puede correr el MVP en <10 minutos.

---

## 11) Plan de ejecución por sprints (sin bloquearse)

### Sprint 0 (Día 1–2): Arranque
- Agente 0: scaffold + CI + contratos (este spec en repo).
- Agente 1: IO FITS básico.
- Agente 6: dataset sintético.
- Agente 7: CLI skeleton.

**Criterio de salida:** `oss run` corre en dataset sintético aunque sea con máscara trivial.

### Sprint 1 (Día 3–7): MVP funcional
- Agente 2: detector baseline real.
- Agente 3: quality.json.
- Agente 4: night_summary.
- Agente 5: ODC estimator MVP.

**Criterio de salida:** artefactos completos por carpeta + reportes.

### Sprint 2 (v0.2): Calidad científica incremental
- mejorar detector, calibración de severidad, downweighting,
- opción de “cleaned.fits” bajo bandera experimental,
- mejora ODC (control por luna/airmass si hay metadata).

---

## 12) Checklist de “Definition of Done” global (MVP)
- [ ] Instala y ejecuta en limpio.
- [ ] `oss run` genera los 4 outputs principales.
- [ ] Tests pasan (IO + masks + CLI smoke).
- [ ] Documentación de quickstart existe.
- [ ] Contratos de E/S respetados.

---

## 13) Backlog inicial (issues list)
1) Repo scaffold + CI (Agente 0/8)
2) FITS IO + tests (Agente 1)
3) Synthetic dataset + truth (Agente 6)
4) Detector baseline + mask (Agente 2)
5) Frame metrics + quality.json (Agente 3)
6) Night summary (Agente 4)
7) ODC estimator MVP (Agente 5)
8) CLI end-to-end (Agente 7)
9) Docs + ejemplo (Agente 9)
