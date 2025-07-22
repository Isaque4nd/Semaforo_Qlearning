import pandas as pd
import matplotlib.pyplot as plt
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Arquivos de resultado
fixed_file = "resultado_tempo_fixo.csv"
rl_file    = "resultado_qlearning.csv"

# Diretório de saída
output_dir = "relatorio"
os.makedirs(output_dir, exist_ok=True)

# Leitura dos dados
df_fixed = pd.read_csv(fixed_file)
df_rl    = pd.read_csv(rl_file)

# Cálculo de métricas agregadas
def compute_metrics(df, label):
    metrics = {
        'tempo_medio': df['carros_parados'].mean(),
        'desvio_padrao': df['carros_parados'].std(),
        'maximo': df['carros_parados'].max(),
        'minimo': df['carros_parados'].min()
    }
    return metrics

metrics_fixed = compute_metrics(df_fixed, 'Tempo Fixo')
metrics_rl    = compute_metrics(df_rl,    'Q-Learning')

# Plot comparativo
plt.figure(figsize=(10, 5))
plt.plot(df_fixed['tempo'], df_fixed['carros_parados'], label='Tempo Fixo', color='red')
plt.plot(df_rl['tempo'],    df_rl['carros_parados'],    label='Q-Learning', color='blue')
plt.title('Comparação de Carros Parados')
plt.xlabel('Tempo (s)')
plt.ylabel('Número de Carros Parados')
plt.legend()
plot_path = os.path.join(output_dir, 'comparacao.png')
plt.savefig(plot_path)
plt.close()

# Geração de relatório em HTML
def gerar_html(metrics_fixed, metrics_rl, plot_file, output_file):
    html = f"""
    <html>
      <head><title>Relatório de Comparação</title></head>
      <body>
        <h1>Relatório de Comparação: Tempo Fixo vs Q-Learning</h1>
        <h2>Métricas Agregadas</h2>
        <table border='1' cellpadding='5'>
          <tr><th>Algoritmo</th><th>Média</th><th>Desvio Padrão</th><th>Máximo</th><th>Mínimo</th></tr>
          <tr><td>Tempo Fixo</td><td>{metrics_fixed['tempo_medio']:.2f}</td><td>{metrics_fixed['desvio_padrao']:.2f}</td><td>{metrics_fixed['maximo']}</td><td>{metrics_fixed['minimo']}</td></tr>
          <tr><td>Q-Learning</td><td>{metrics_rl['tempo_medio']:.2f}</td><td>{metrics_rl['desvio_padrao']:.2f}</td><td>{metrics_rl['maximo']}</td><td>{metrics_rl['minimo']}</td></tr>
        </table>
        <h2>Gráfico Comparativo</h2>
        <img src='{os.path.basename(plot_file)}' alt='Comparação de Carros Parados'>
      </body>
    </html>
    """
    with open(output_file, 'w') as f:
        f.write(html)

html_path = os.path.join(output_dir, 'relatorio_comparativo.html')
gerar_html(metrics_fixed, metrics_rl, plot_path, html_path)

# Geração de relatório em PDF
def gerar_pdf(metrics_fixed, metrics_rl, plot_file, output_file):
    c = pdfcanvas.Canvas(output_file, pagesize=letter)
    styles = getSampleStyleSheet()
    width, height = letter

    # Título
    c.setFont('Helvetica-Bold', 16)
    c.drawCentredString(width/2, height - 50, 'Relatório de Comparação: Tempo Fixo vs Q-Learning')

    # Métricas
    text = c.beginText(50, height - 100)
    text.setFont('Helvetica', 12)
    text.textLine('Métricas Agregadas:')
    for alg, metrics in [('Tempo Fixo', metrics_fixed), ('Q-Learning', metrics_rl)]:
        text.textLine(f"{alg} - Média: {metrics['tempo_medio']:.2f}, Desvio Padrão: {metrics['desvio_padrao']:.2f}, Máx: {metrics['maximo']}, Mín: {metrics['minimo']}")
    c.drawText(text)

    # Gráfico
    img = Image(plot_file, width=480, height=240)
    img.drawOn(c, 60, height - 380)

    c.showPage()
    c.save()

pdf_path = os.path.join(output_dir, 'relatorio_comparativo.pdf')
gerar_pdf(metrics_fixed, metrics_rl, plot_path, pdf_path)

print(f"Relatórios gerados em: {output_dir}")

