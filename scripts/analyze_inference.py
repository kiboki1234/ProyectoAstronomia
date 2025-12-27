# Author: Andres Espin
# Email: aaespin3@espe.edu.ec
# Role: Junior Developer
# Purpose: Independent Research Study


import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def generate_plots():
    csv_path = "inference_results.csv"
    output_dir = "docs/figures"
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(csv_path):
        print("CSV not found!")
        return

    # Load Data
    df = pd.read_csv(csv_path)
    
    # Text Report (Keep existing logic mostly)
    # ... (omitted for brevity, we focus on plots here)
    
    # Set Style
    sns.set_theme(style="whitegrid")
    
    # PLOT 1: Streak Distribution Histogram
    plt.figure(figsize=(10, 6))
    ax = sns.histplot(data=df, x="detected_streaks", discrete=True, color="#3498db", kde=False)
    
    # Calculate stats
    mean_val = df['detected_streaks'].mean()
    median_val = df['detected_streaks'].median()
    
    # Add vertical line for mean
    plt.axvline(mean_val, color='r', linestyle='--', linewidth=2, label=f'Promedio: {mean_val:.2f}')
    
    # Add text box
    textstr = '\n'.join((
        f'N = {len(df)}',
        f'Promedio = {mean_val:.2f}',
        f'Máximo = {df["detected_streaks"].max()}'
    ))
    props = dict(boxstyle='round', facecolor='white', alpha=0.9)
    ax.text(0.95, 0.95, textstr, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', horizontalalignment='right', bbox=props)

    plt.title("Distribución de Estelas de Satélite por Imagen", fontsize=16)
    plt.xlabel("Número de Estelas Detectadas", fontsize=12)
    plt.ylabel("Frecuencia (Imágenes)", fontsize=12)
    plt.legend()
    plt.xticks(range(0, int(df['detected_streaks'].max()) + 2, 2))
    plt.grid(axis='y', alpha=0.3)
    plt.savefig(os.path.join(output_dir, "streak_distribution.png"), dpi=300, bbox_inches='tight')
    plt.close()
    
    # PLOT 2: Processing Time Distribution
    plt.figure(figsize=(10, 6))
    ax2 = sns.histplot(data=df, x="proc_time_ms", bins=30, color="#2ecc71", kde=True)
    
    mean_time = df['proc_time_ms'].mean()
    plt.axvline(mean_time, color='b', linestyle='--', linewidth=2, label=f'Promedio: {mean_time:.1f}ms')
    
    plt.title("Distribución de Tiempo de Procesamiento", fontsize=16)
    plt.xlabel("Tiempo (ms)", fontsize=12)
    plt.ylabel("Frecuencia", fontsize=12)
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    plt.savefig(os.path.join(output_dir, "processing_time_dist.png"), dpi=300, bbox_inches='tight')
    plt.close()
    
    # PLOT 3: Streaks vs Time (Performance Check)
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x="detected_streaks", y="proc_time_ms", alpha=0.5, color="#e74c3c")
    plt.title("Escalabilidad: Estelas vs Tiempo", fontsize=16)
    plt.xlabel("Estelas Detectadas", fontsize=12)
    plt.ylabel("Tiempo de Proceso (ms)", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(output_dir, "perf_time_vs_streaks.png"), dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Plots saved to {output_dir}")

if __name__ == "__main__":
    generate_plots()
