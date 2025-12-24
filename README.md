# Proyecto Astronomía - OrbitalSkyShield

Este repositorio contiene el desarrollo del proyecto **OrbitalSkyShield**, una herramienta para la detección y mitigación de trazas de satélites en imágenes astronómicas (FITS).

## Estructura del Proyecto

- `orbitalskyshield/`: Código fuente del paquete Python (MVP).
- `MULTIAGENT_DEV_SPEC_v0.1.md`: Especificación técnica y roadmap.
- `visualize_results.py`: Script de utilidad para visualizar resultados rápidamente.

## Instalación y Uso

Para instrucciones detalladas de instalación y uso del paquete, consulta el [README del paquete](./orbitalskyshield/README.md).

### Comandos Rápidos

1. **Instalar dependencias:**
   ```bash
   pip install -e .
   ```

2. **Ejecutar Pipeline:**
   ```bash
   python -m orbitalskyshield.cli.main run --input-dir <INPUT_DIR> --output-dir <OUTPUT_DIR>
   ```

## Autores
- Antigravity AI
- Kiboki
