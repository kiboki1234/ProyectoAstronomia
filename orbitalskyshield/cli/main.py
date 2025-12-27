# Author: Andres Espin
# Email: aaespin3@espe.edu.ec
# Role: Junior Developer
# Purpose: Independent Research Study

import typer
import os
from typing import Optional
from ..core.logging import setup_logging
from ..datasets.synthetic.generator import generate_dataset
from ..api.pipeline import OSSPipeline

app = typer.Typer(help="OrbitalSkyShield CLI")

@app.command()
def run(
    input_dir: str = typer.Option(..., help="Input directory containing FITS files"),
    output_dir: str = typer.Option(..., help="Output directory for masks/reports"),
    config: Optional[str] = typer.Option(None, help="Path to config.yaml"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")
):
    """
    Run the full detection pipeline.
    """
    level = "DEBUG" if verbose else "INFO"
    logger = setup_logging(level=level)
    
    # Load pipeline and execute
    try:
        pipeline = OSSPipeline(config_path=config)
        pipeline.run_on_folder(input_dir, output_dir)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise typer.Exit(code=1)


@app.command()
def generate_synthetic(
    output_dir: str = typer.Option("./data/synthetic", help="Output directory"),
    count: int = typer.Option(10, help="Number of frames to generate")
):
    """
    Generate synthetic dataset for testing.
    """
    setup_logging()
    generate_dataset(output_dir, count)


if __name__ == "__main__":
    app()
