import pandas as pd
import matplotlib.pyplot as plt
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Diretórios de resultados
fixed_dir = "resultados_tempo_fixo"
rl_dir = "resultados_qlearning"

# Arquivos de resultado
fixed_files = {
    'carros_parados': os.path.join(fixed_dir, "resultado_tempo_fixo.csv"),
    'total_paradas': os.path.join(fixed_dir, "paradas_tempo_fixo.csv"),
    'tempo_espera': os.path.join(fixed_dir, "espera_tempo_fixo.csv"),
    'velocidade_media': os.path.join(fixed_dir, "velocidade_tempo_fixo.csv"),
    'densidade_media': os.path.join(fixed_dir, "densidade_tempo_fixo.csv"),
    'tempo_espera_emergency': os.path.join(fixed_dir, "emergency_tempo_fixo.csv"),
    'tempo_espera_authority': os.path.join(fixed_dir, "authority_tempo_fixo.csv"),
    'densidade_media_prioritarios': os.path.join(fixed_dir, "densidade_prioritarios_tempo_fixo.csv"),
    'carros_parados_prioritarios': os.path.join(fixed_dir, "carros_parados_prioritarios_tempo_fixo.csv"),
    'total_paradas_prioritarios': os.path.join(fixed_dir, "paradas_prioritarios_tempo_fixo.csv"),
    'tempo_espera_prioritarios': os.path.join(fixed_dir, "espera_prioritarios_tempo_fixo.csv"),
    'velocidade_media_prioritarios': os.path.join(fixed_dir, "velocidade_prioritarios_tempo_fixo.csv")
}
rl_files = {
    'carros_parados': os.path.join(rl_dir, "resultado_qlearning.csv"),
    'total_paradas': os.path.join(rl_dir, "paradas_qlearning.csv"),
    'tempo_espera': os.path.join(rl_dir, "espera_qlearning.csv"),
    'velocidade_media': os.path.join(rl_dir, "velocidade_qlearning.csv"),
    'densidade_media': os.path.join(rl_dir, "densidade_qlearning.csv"),
    'tempo_espera_emergency': os.path.join(rl_dir, "emergency_qlearning.csv"),
    'tempo_espera_authority': os.path.join(rl_dir, "authority_qlearning.csv"),
    'densidade_media_prioritarios': os.path.join(rl_dir, "densidade_prioritarios_qlearning.csv"),
    'carros_parados_prioritarios': os.path.join(rl_dir, "carros_parados_prioritarios_qlearning.csv"),
    'total_paradas_prioritarios': os.path.join(rl_dir, "paradas_prioritarios_qlearning.csv"),
    'tempo_espera_prioritarios': os.path.join(rl_dir, "espera_prioritarios_qlearning.csv"),
    'velocidade_media_prioritarios': os.path.join(rl_dir, "velocidade_prioritarios_qlearning.csv")
}

# Diretório de saída
output_dir = "relatorio"
os.makedirs(output_dir, exist_ok=True)

# Leitura dos dados
dfs_fixed = {}
dfs_rl = {}
for key, file in fixed_files.items():
    try:
        dfs_fixed[key] = pd.read_csv(file)
    except FileNotFoundError:
        print(f"Arquivo {file} não encontrado.")
        dfs_fixed[key] = pd.DataFrame()

for key, file in rl_files.items():
    try:
        dfs_rl[key] = pd.read_csv(file)
    except FileNotFoundError:
        print(f"Arquivo {file} não encontrado.")
        dfs_rl[key] = pd.DataFrame()

# Padding dos dados para igualar os tempos
for metric in ['carros_parados', 'total_paradas', 'tempo_espera', 'velocidade_media', 'carros_parados_prioritarios', 'total_paradas_prioritarios', 'tempo_espera_prioritarios', 'velocidade_media_prioritarios', 'densidade_media_prioritarios']:
    if metric not in dfs_fixed or metric not in dfs_rl:
        continue
    df_fixed = dfs_fixed[metric]
    df_rl = dfs_rl[metric]
    if not df_fixed.empty and not df_rl.empty:
        max_time = int(max(df_fixed['tempo'].max(), df_rl['tempo'].max()))
        min_fixed = df_fixed[metric].min()
        min_rl = df_rl[metric].min()
        # Pad fixed if shorter
        if df_fixed['tempo'].max() < max_time:
            last_time = int(df_fixed['tempo'].max())
            for t in range(last_time + 1, max_time + 1):
                new_row = {'tempo': t, metric: min_fixed}
                df_fixed = pd.concat([df_fixed, pd.DataFrame([new_row])], ignore_index=True)
        # Pad rl if shorter
        if df_rl['tempo'].max() < max_time:
            last_time = int(df_rl['tempo'].max())
            for t in range(last_time + 1, max_time + 1):
                new_row = {'tempo': t, metric: min_rl}
                df_rl = pd.concat([df_rl, pd.DataFrame([new_row])], ignore_index=True)
        dfs_fixed[metric] = df_fixed
        dfs_rl[metric] = df_rl

def get_column(metric):
    column_map = {
        'tempo_espera_emergency': 'media_espera_emergency',
        'tempo_espera_authority': 'media_espera_authority',
        'carros_parados': 'carros_parados',
        'total_paradas': 'total_paradas',
        'tempo_espera': 'tempo_espera',
        'velocidade_media': 'velocidade_media',
        'densidade_media': 'densidade_media',
        'carros_parados_prioritarios': 'carros_parados_prioritarios',
        'total_paradas_prioritarios': 'total_paradas_prioritarios',
        'tempo_espera_prioritarios': 'tempo_espera_prioritarios',
        'velocidade_media_prioritarios': 'velocidade_media_prioritarios',
        'densidade_media_prioritarios': 'densidade_media_prioritarios'
    }
    return column_map.get(metric, metric)

# Cálculo de métricas agregadas
def compute_metrics(df, metric):
    if df.empty:
        return {'media': 0, 'desvio_padrao': 0, 'maximo': 0, 'minimo': 0}
    column = get_column(metric)
    return {
        'media': df[column].mean(),
        'desvio_padrao': df[column].std(),
        'maximo': df[column].max(),
        'minimo': df[column].min()
    }

metrics_fixed = {key: compute_metrics(df, key) for key, df in dfs_fixed.items()}
metrics_rl = {key: compute_metrics(df, key) for key, df in dfs_rl.items()}

# Plot comparativo para cada métrica
metric_labels = {
    'carros_parados': 'Número de Carros Parados',
    'total_paradas': 'Total de Paradas (Estimativa)',
    'tempo_espera': 'Tempo Médio de Espera (s)',
    'velocidade_media': 'Velocidade Média (m/s)',
    'densidade_media': 'Densidade (veículos/km/faixa)',
    'tempo_espera_emergency': 'Tempo de Espera Médio - Emergência (s)',
    'tempo_espera_authority': 'Tempo de Espera Médio - Autoridade (s)',
    'carros_parados_prioritarios': 'Número de Carros Parados - Prioritários',
    'total_paradas_prioritarios': 'Total de Paradas - Prioritários (Estimativa)',
    'tempo_espera_prioritarios': 'Tempo Médio de Espera - Prioritários (s)',
    'velocidade_media_prioritarios': 'Velocidade Média - Prioritários (m/s)',
    'densidade_media_prioritarios': 'Densidade - Prioritários (veículos/km/faixa)'
}
for metric in ['carros_parados', 'total_paradas', 'tempo_espera', 'velocidade_media', 'densidade_media', 'tempo_espera_emergency', 'tempo_espera_authority', 'carros_parados_prioritarios', 'total_paradas_prioritarios', 'tempo_espera_prioritarios', 'velocidade_media_prioritarios', 'densidade_media_prioritarios']:
    if metric not in dfs_fixed or metric not in dfs_rl:
        continue
    plt.figure(figsize=(12, 6))
    if not dfs_fixed[metric].empty:
        plt.plot(dfs_fixed[metric]['tempo'], dfs_fixed[metric][get_column(metric)], label='Tempo Fixo (Controle Tradicional)', color='blue', linewidth=2)
    if not dfs_rl[metric].empty:
        plt.plot(dfs_rl[metric]['tempo'], dfs_rl[metric][get_column(metric)], label='Q-Learning (Aprendizado por Reforço)', color='red', linewidth=2)
    plt.title(f'Comparação de {metric_labels[metric]} ao Longo do Tempo', fontsize=16, fontweight='bold')
    plt.xlabel('Tempo de Simulação (segundos)', fontsize=14)
    plt.ylabel(metric_labels[metric], fontsize=14)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plot_path = os.path.join(output_dir, f'comparacao_{metric}.png')
    plt.savefig(plot_path, dpi=300)
    plt.close()

# Geração de relatório em HTML
def gerar_html(metrics_fixed, metrics_rl, output_file):
    html = """
    <html>
      <head><title>Relatório de Comparação</title></head>
      <body>
        <h1>Relatório de Comparação: Tempo Fixo vs Q-Learning</h1>
        <p><strong>Interpretação:</strong> Este relatório compara o controle de semáforos tradicional (tempo fixo) com o aprendizado por reforço (Q-Learning). Valores menores em "Carros Parados", "Total de Paradas" e "Tempo de Espera" indicam melhor desempenho. Valores maiores em "Velocidade Média" são melhores.</p>
    """
    for metric in ['carros_parados', 'total_paradas', 'tempo_espera', 'velocidade_media', 'densidade_media', 'tempo_espera_emergency', 'tempo_espera_authority', 'carros_parados_prioritarios', 'total_paradas_prioritarios', 'tempo_espera_prioritarios', 'velocidade_media_prioritarios', 'densidade_media_prioritarios']:
        if metric not in metrics_fixed or metric not in metrics_rl:
            continue
        html += """
        <h2>Métricas para {}</h2>
        <table border='1' cellpadding='5'>
          <tr><th>Algoritmo</th><th>Média</th><th>Desvio Padrão</th><th>Máximo</th><th>Mínimo</th></tr>
          <tr><td>Tempo Fixo</td><td>{:.2f}</td><td>{:.2f}</td><td>{}</td><td>{}</td></tr>
          <tr><td>Q-Learning</td><td>{:.2f}</td><td>{:.2f}</td><td>{}</td><td>{}</td></tr>
        </table>
        <p><em>Gráfico mostra a evolução ao longo do tempo. Linha azul: Tempo Fixo. Linha vermelha: Q-Learning.</em></p>
        <img src='comparacao_{}.png' alt='Comparação de {}'>
        """.format(
            metric_labels[metric],
            metrics_fixed[metric]['media'], metrics_fixed[metric]['desvio_padrao'], metrics_fixed[metric]['maximo'], metrics_fixed[metric]['minimo'],
            metrics_rl[metric]['media'], metrics_rl[metric]['desvio_padrao'], metrics_rl[metric]['maximo'], metrics_rl[metric]['minimo'],
            metric, metric_labels[metric]
        )
    html += """
      </body>
    </html>
    """
    with open(output_file, 'w') as f:
        f.write(html)

html_path = os.path.join(output_dir, 'relatorio_comparativo.html')
print(f"Gerando HTML em: {html_path}")
gerar_html(metrics_fixed, metrics_rl, html_path)

print(f"Relatórios gerados em: {output_dir}")