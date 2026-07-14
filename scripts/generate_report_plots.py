import os
import numpy as np
import matplotlib.pyplot as plt

# Set modern scientific style
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['xtick.color'] = '#333333'
plt.rcParams['ytick.color'] = '#333333'
plt.rcParams['grid.color'] = '#eeeeee'
plt.rcParams['grid.linewidth'] = 0.5

# Define target figures directory
FIGURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "doc", "latex", "figures"))
os.makedirs(FIGURES_DIR, exist_ok=True)

# 1. Stage A Accuracy Comparison
def plot_stagea_acc():
    fig, ax = plt.subplots(figsize=(6, 4))
    experiments = ['EXP-001\nScratch CNN', 'EXP-002\nFrozen MobileNet', 'EXP-003\nFine-Tuned', 'EXP-004\nINT8 TFLite']
    accuracies = [61.00, 84.28, 87.42, 87.35]
    colors = ['#d95f02', '#7570b3', '#1b9e77', '#2ca02c']
    
    bars = ax.bar(experiments, accuracies, color=colors, width=0.5, edgecolor='#333333', linewidth=0.7)
    ax.set_ylabel('Validierungsgenauigkeit (%)', fontsize=10, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.grid(axis='y', linestyle='--')
    
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
                    
    plt.title('Stage A: Modellvergleich der Klassifikation', fontsize=11, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, 'stagea-acc-comparison.png'), dpi=300)
    plt.close()
    print("Generated stagea-acc-comparison.png")

# 2. Stage B mAP50 Comparison
def plot_det_map():
    fig, ax = plt.subplots(figsize=(10, 5))
    experiments = [
        'EXP-005\n(v8n Tabletop)',
        'EXP-006\n(v8n Wild-Fus.)',
        'EXP-008\n(v8n Table-Clean)',
        'EXP-009\n(v8n Pristine)',
        'EXP-011\n(v8n Wild-only)',
        'EXP-013\n(11n Baseline)',
        'EXP-014\n(11n +Roboflow)',
        'EXP-015\n(11n +WaRP)',
        'EXP-016\n(11n WaRP-only)'
    ]
    map50 = [82.3, 39.4, 39.6, 72.8, 35.0, 55.1, 60.7, 56.0, 58.8]
    colors = ['#ff7f0e', '#1f77b4', '#aec7e8', '#2ca02c', '#ffbb78', '#9467bd', '#d62728', '#bcbd22', '#17becf']
    
    bars = ax.bar(experiments, map50, color=colors, width=0.6, edgecolor='#333333', linewidth=0.7)
    ax.set_ylabel('mAP50 (%)', fontsize=10, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.grid(axis='y', linestyle='--')
    
    # Add annotations for labels
    for bar, val in zip(bars, map50):
        height = bar.get_height()
        ax.annotate(f'{height:.1f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
                    
    plt.title('Stage B: mAP50 Vergleich der Detektionsmodelle', fontsize=12, fontweight='bold', pad=15)
    plt.xticks(rotation=15, ha='right', fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, 'det-map-comparison.png'), dpi=300)
    plt.close()
    print("Generated det-map-comparison.png")

# 3. Heatmap of Per-Class mAP50 for YOLO11n Experiments
def plot_heatmap():
    # Data structure
    classes = ['Glass', 'Metal', 'Paper', 'Plastic', 'Trash']
    experiments = [
        'EXP-013 (TACO+TrashNet)',
        'EXP-014 (+Roboflow)',
        'EXP-015 (+WaRP)',
        'EXP-016 (WaRP-only)'
    ]
    
    # mAP50 values
    data = np.array([
        [56.5, 67.9, 79.3, 55.6, 15.6],  # EXP-013
        [50.2, 71.3, 82.9, 72.1, 26.9],  # EXP-014
        [75.0, 57.0, 62.6, 71.2, 14.3],  # EXP-015
        [77.7, 42.1, 42.2, 73.1, 0.0]    # EXP-016 (Trash is N/A, represent as 0 for plot)
    ])
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Standard heatmap using Matplotlib imshow
    im = ax.imshow(data, cmap='YlGnBu', aspect='auto', vmin=0, vmax=100)
    
    # Create colorbar
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel('mAP50 (%)', rotation=-90, va="bottom", fontweight='bold')
    
    # Tick labels
    ax.set_xticks(np.arange(len(classes)))
    ax.set_yticks(np.arange(len(experiments)))
    ax.set_xticklabels(classes, fontsize=10, fontweight='bold')
    ax.set_yticklabels(experiments, fontsize=10)
    
    # Rotate tick labels
    plt.setp(ax.get_xticklabels(), rotation=0, ha="center")
    
    # Add values text inside heatmap
    for i in range(len(experiments)):
        for j in range(len(classes)):
            val = data[i, j]
            if val == 0.0 and j == 4 and i == 3:
                text_val = "N/A"
            else:
                text_val = f"{val:.1f}%"
            text = ax.text(j, i, text_val,
                           ha="center", va="center", 
                           color="white" if val > 55 else "black",
                           fontweight='bold', fontsize=10)
                           
    plt.title('Klassenspezifische mAP50 im Modellvergleich (YOLO11n)', fontsize=12, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, 'heatmap-4datasets.png'), dpi=300)
    plt.close()
    print("Generated heatmap-4datasets.png")

# 4. Class Distribution comparison (Stage A vs Stage B)
def plot_class_distribution():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    
    # Stage A Data
    stage_a_classes = ['Glass', 'Metal', 'Paper', 'Plastic']
    stage_a_counts = [163, 156, 160, 125]
    colors_a = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    ax1.bar(stage_a_classes, stage_a_counts, color=colors_a, edgecolor='#333333', width=0.5, alpha=0.85)
    ax1.set_ylabel('Anzahl Bilder', fontsize=10, fontweight='bold')
    ax1.set_title('Stage A: Bildverteilung (Gesamt: 604)', fontsize=11, fontweight='bold')
    ax1.grid(axis='y', linestyle='--')
    ax1.set_ylim(0, 200)
    
    for i, count in enumerate(stage_a_counts):
        ax1.annotate(str(count), xy=(i, count), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontweight='bold')
        
    # Stage B Validation Data (mira_tnr)
    stage_b_classes = ['Glass', 'Metal', 'Paper', 'Plastic', 'Trash']
    stage_b_counts = [336, 439, 474, 1316, 561]
    colors_b = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    ax2.bar(stage_b_classes, stage_b_counts, color=colors_b, edgecolor='#333333', width=0.5, alpha=0.85)
    ax2.set_ylabel('Anzahl Instanzen (Validierungsset)', fontsize=10, fontweight='bold')
    ax2.set_title('Stage B (mira_tnr): Instanzverteilung (Gesamt: 3126)', fontsize=11, fontweight='bold')
    ax2.grid(axis='y', linestyle='--')
    ax2.set_ylim(0, 1500)
    
    for i, count in enumerate(stage_b_counts):
        ax2.annotate(str(count), xy=(i, count), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontweight='bold')
        
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, 'class-distribution.png'), dpi=300)
    plt.close()
    print("Generated class-distribution.png")

# 5. Field Benchmark comparison (F1 Score)
def plot_field_benchmark():
    fig, ax = plt.subplots(figsize=(9, 5))
    
    models = [
        'mira_exp014.pt (YOLO11n +Roboflow)',
        'mira_exp014_int8.tflite (Quantized)',
        'mira_exp015.pt (YOLO11n +WaRP)',
        'mira_exp015_int8.tflite (Quantized)',
        'mira_exp013.pt (YOLO11n Baseline)',
        'mira_exp013_int8.tflite (Quantized)',
        'mira_exp011.pt (YOLOv8n Wild)',
        'mira_exp009_int8.tflite (Tabletop)',
        'mira_exp006.pt (YOLOv8n Fusion)',
        'mira_exp006_int8.tflite (Quantized)'
    ]
    f1_scores = [85.8, 72.8, 77.3, 78.0, 78.0, 70.7, 80.2, 79.5, 77.8, 52.8]
    
    # Sort models by performance
    indices = np.argsort(f1_scores)
    sorted_models = [models[i] for i in indices]
    sorted_f1 = [f1_scores[i] for i in indices]
    
    # Plot horizontal bar chart
    colors = ['#1f77b4' if 'int8' not in m.lower() else '#aec7e8' for m in sorted_models]
    # Highlight the best model in gold/red
    for idx, model_name in enumerate(sorted_models):
        if 'exp014.pt' in model_name:
            colors[idx] = '#d62728' # Dark red for best model
            
    bars = ax.barh(sorted_models, sorted_f1, color=colors, edgecolor='#333333', height=0.6)
    ax.set_xlabel('Praxistest F1-Score (%)', fontsize=10, fontweight='bold')
    ax.set_xlim(0, 100)
    ax.grid(axis='x', linestyle='--')
    
    for bar in bars:
        width = bar.get_width()
        ax.annotate(f'{width:.1f}%',
                    xy=(width, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0),
                    textcoords="offset points",
                    ha='left', va='center', fontsize=9, fontweight='bold')
                    
    plt.title('Praxistest (Field Benchmark) — F1-Score-Modellvergleich', fontsize=12, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, 'field-benchmark-f1.png'), dpi=300)
    plt.close()
    print("Generated field-benchmark-f1.png")

# 6. EMA Filter Effect Simulation (Hypothesis 4 Proof)
def plot_ema_filter_simulation():
    np.random.seed(42)
    timesteps = 60
    
    # True signal: 0 to 10 step response with some steady states
    true_prob = np.zeros(timesteps)
    true_prob[15:45] = 0.85
    true_prob[45:] = 0.10
    
    # Add random high frequency noise/jitter to simulate raw prediction jitter
    noise = np.random.normal(0, 0.08, timesteps)
    raw_signal = true_prob + noise
    # Constrain raw_signal within 0 and 1
    raw_signal = np.clip(raw_signal, 0.0, 1.0)
    
    # Inject occasional spiky false positives/negatives (misfires)
    raw_signal[8] = 0.65  # False positive spike
    raw_signal[28] = 0.20 # False negative drop
    raw_signal[52] = 0.70 # False positive spike
    
    # Apply EMA filter with alpha = 0.15
    alpha = 0.15
    ema_signal = np.zeros(timesteps)
    ema_signal[0] = raw_signal[0]
    for t in range(1, timesteps):
        ema_signal[t] = alpha * raw_signal[t] + (1 - alpha) * ema_signal[t-1]
        
    fig, ax = plt.subplots(figsize=(8, 4.5))
    
    ax.plot(raw_signal, label='Rohdaten (Modellvorhersage mit Jitter)', color='#e31a1c', alpha=0.6, linewidth=1.5, linestyle=':')
    ax.plot(ema_signal, label=r'Gedämpftes Signal (EMA $\alpha=0.15$)', color='#1f78b4', linewidth=2.5)
    ax.step(np.arange(timesteps), true_prob, label='Realer Objektzustand', color='#333333', alpha=0.8, linewidth=1.5, linestyle='--')
    
    # Annotate key features
    ax.annotate('Dämpfung von\nFehltriggern', xy=(8, 0.2), xytext=(2, 0.4),
                arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                fontsize=9, ha='center')
                
    ax.annotate('Ausgleich stochastischen\nKamerarauschens', xy=(35, 0.85), xytext=(35, 0.5),
                arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=HeadWidth_Placeholder),
                fontsize=9, ha='center')
                
    ax.annotate('Geringer Latenzverzug\n(~5 Frames)', xy=(18, 0.5), xytext=(25, 0.25),
                arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=HeadWidth_Placeholder),
                fontsize=9, ha='center')
                
    ax.set_xlabel('Zeitschritte (Frames)', fontsize=10, fontweight='bold')
    ax.set_ylabel('Klassenwahrscheinlichkeit', fontsize=10, fontweight='bold')
    ax.set_ylim(-0.05, 1.1)
    ax.grid(True, linestyle=':')
    ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
    
    plt.title(r'Wirkung des EMA-Filters ($\alpha=0.15$) auf das Steuersignal', fontsize=11, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, 'ema-filter-effect.png'), dpi=300)
    plt.close()
    print("Generated ema-filter-effect.png")

if __name__ == '__main__':
    # Fix the HeadWidth placeholder
    HeadWidth_Placeholder = 6
    plot_stagea_acc()
    plot_det_map()
    plot_heatmap()
    plot_class_distribution()
    plot_field_benchmark()
    plot_ema_filter_simulation()
    print("All plots generated successfully!")
