from pathlib import Path
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
RES = ROOT / 'resultados'
FIG = ROOT / 'figuras'

def localizar_csv(nome):
    # Prefer the CSV just generated in the project root; otherwise use the archived result.
    candidatos = (ROOT / nome, RES / nome)
    for caminho in candidatos:
        if caminho.is_file():
            return caminho
    raise FileNotFoundError(f'CSV não encontrado: {nome}. Procurado em {ROOT} e {RES}.')
FIG.mkdir(exist_ok=True)

# Read CSVs produced by the experiments; UTF-8 BOM is handled by utf-8-sig.
wide = pd.read_csv(localizar_csv('abrangente_resumo.csv'), encoding='utf-8-sig', sep=';')
wide.columns = [c.lstrip('\ufeff') for c in wide.columns]
samples = pd.read_csv(localizar_csv('abrangente_amostras.csv'), encoding='utf-8-sig', sep=';')
samples.columns = [c.lstrip('\ufeff') for c in samples.columns]
scalable = pd.read_csv(localizar_csv('experimento_resumo.csv'), encoding='utf-8-sig')
scalable.columns = [c.lstrip('\ufeff') for c in scalable.columns]
bench = pd.read_csv(localizar_csv('benchmark_complexidade.csv'), encoding='utf-8-sig')

ops = ['ADD', 'SUB', 'MUL', 'DIV']
styles = ['-', '--', '-.', ':']

# Figure 5: empirical vs theoretical RMSE for the scalable experiment.
n = scalable['tamanho_entradas'].to_numpy(dtype=float)
d = scalable['intensidade'].to_numpy(dtype=float)
emp = scalable['rmse'].to_numpy(dtype=float)
theory = d**2 * np.sqrt(n / 2) / 3
fig, ax = plt.subplots(figsize=(7.4, 5.2))
ax.scatter(theory, emp, s=48, alpha=0.85, label='Configurações observadas')
lo = min(theory.min(), emp.min()) * 0.8
hi = max(theory.max(), emp.max()) * 1.2
ax.plot([lo, hi], [lo, hi], '--', label='Correspondência ideal')
ax.set_xscale('log'); ax.set_yscale('log')
ax.set_xlabel('RMSE teórico'); ax.set_ylabel('RMSE empírico')
ax.set_title('RMSE empírico versus teórico')
ax.grid(True, which='both', alpha=0.25); ax.legend()
fig.tight_layout(); fig.savefig(FIG / 'rmse_empirico_teorico.png', dpi=220); plt.close(fig)

# Figure 6: median RMSE by operation, size and relative intensity, log vertical axis.
fig, axes = plt.subplots(2, 2, figsize=(11.4, 8.0), sharex=True)
for ax, op in zip(axes.flat, ops):
    sub = wide[wide['operacao'] == op]
    for j, intensity in enumerate(sorted(sub['intensidade'].unique())):
        vals = (sub[sub['intensidade'] == intensity]
                .groupby('entradas', as_index=False)['RMSE'].median())
        vals = vals.sort_values('entradas')
        y = vals['RMSE'].to_numpy(dtype=float)
        y = np.maximum(y, 1e-18)  # visible floating-point residual floor
        ax.plot(vals['entradas'], y, marker='o', linestyle=styles[j], label=f'{intensity*100:g}%')
    ax.set_yscale('log')
    ax.set_title(op)
    ax.grid(True, which='both', alpha=0.25)
    ax.set_xlabel('Quantidade de entradas')
    ax.set_ylabel('RMSE mediano')
    ax.legend(title='Perturbação')
fig.suptitle('RMSE mediano por operação, tamanho e intensidade', y=1.01)
fig.tight_layout(); fig.savefig(FIG / 'abrangente_rmse_operacao_tamanho.png', dpi=220, bbox_inches='tight'); plt.close(fig)

# Figure 7: sign/pattern effect by operation. Each point is median across sizes and structures.
fig, axes = plt.subplots(2, 2, figsize=(11.4, 8.0), sharex=True)
for ax, op in zip(axes.flat, ops):
    sub = wide[wide['operacao'] == op]
    for j, pattern in enumerate(['positiva', 'negativa', 'combinada']):
        vals = (sub[sub['tipo_perturbacao'] == pattern]
                .groupby('intensidade', as_index=False)['RMSE'].median()
                .sort_values('intensidade'))
        y = np.maximum(vals['RMSE'].to_numpy(dtype=float), 1e-18)
        ax.plot(vals['intensidade']*100, y, marker='o', linestyle=styles[j], label=pattern)
    ax.set_yscale('log'); ax.set_title(op)
    ax.grid(True, which='both', alpha=0.25)
    ax.set_xlabel('Intensidade relativa (%)'); ax.set_ylabel('RMSE mediano')
    ax.legend(title='Padrão')
fig.suptitle('Influência do padrão de perturbação por operação', y=1.01)
fig.tight_layout(); fig.savefig(FIG / 'abrangente_sentido_por_operacao.png', dpi=220, bbox_inches='tight'); plt.close(fig)

# Figure 8: chain vs branched median RMSE; median over intensity and sign.
fig, axes = plt.subplots(2, 2, figsize=(11.4, 8.0), sharex=True)
for ax, op in zip(axes.flat, ops):
    sub = wide[wide['operacao'] == op]
    for j, structure in enumerate(['cadeia', 'ramificada']):
        vals = (sub[sub['estrutura'] == structure]
                .groupby('entradas', as_index=False)['RMSE'].median()
                .sort_values('entradas'))
        y = np.maximum(vals['RMSE'].to_numpy(dtype=float), 1e-18)
        ax.plot(vals['entradas'], y, marker='o', linestyle=styles[j], label=structure)
    ax.set_yscale('log'); ax.set_title(op)
    ax.grid(True, which='both', alpha=0.25)
    ax.set_xlabel('Quantidade de entradas'); ax.set_ylabel('RMSE mediano')
    ax.legend(title='Estrutura')
fig.suptitle('Comparação entre estruturas por operação', y=1.01)
fig.tight_layout(); fig.savefig(FIG / 'abrangente_estrutura_por_operacao.png', dpi=220, bbox_inches='tight'); plt.close(fig)

# Figure 9: stratified sample - exactly eight rows per 384 configurations.
rng = np.random.default_rng(20261110)
keys = ['operacao', 'estrutura', 'entradas', 'intensidade', 'tipo_perturbacao']
parts = []
for _, group in samples.groupby(keys, sort=True):
    take = min(8, len(group))
    idx = rng.choice(group.index.to_numpy(), size=take, replace=False)
    parts.append(group.loc[idx])
strat = pd.concat(parts, ignore_index=True)
assert len(strat) == 384 * 8, len(strat)
fig, axes = plt.subplots(2, 2, figsize=(11.4, 8.6))
for ax, op in zip(axes.flat, ops):
    sub = strat[strat['operacao'] == op]
    x = sub['variacao_real'].to_numpy(dtype=float)
    y = sub['variacao_linear'].to_numpy(dtype=float)
    ax.scatter(x, y, s=9, alpha=0.35)
    lo = min(x.min(), y.min()); hi = max(x.max(), y.max())
    pad = (hi-lo)*0.04 if hi > lo else max(abs(hi)*0.04, 1e-18)
    ax.plot([lo-pad, hi+pad], [lo-pad, hi+pad], '--', linewidth=1.1, label='Correspondência ideal')
    ax.set_title(op); ax.set_xlabel('Variação real'); ax.set_ylabel('Variação linear estimada')
    ax.grid(True, alpha=0.25); ax.legend(loc='best')
fig.suptitle('Variação real versus estimativa linear: amostra estratificada', y=1.01)
fig.tight_layout(); fig.savefig(FIG / 'abrangente_real_vs_linear_estratificado.png', dpi=220, bbox_inches='tight'); plt.close(fig)

# Save the stratified sample used in the figure for transparent reproducibility.
strat.to_csv(RES / 'abrangente_amostra_grafico.csv', index=False, encoding='utf-8-sig')

# Figure: benchmark runtime in log-log scale with least-squares fit.
fig, ax = plt.subplots(figsize=(7.4, 5.2))
x = bench['nos'].to_numpy(dtype=float)
y = bench['mediana_ms'].to_numpy(dtype=float)
lo = y - bench['p25_ms'].to_numpy(dtype=float)
hi = bench['p75_ms'].to_numpy(dtype=float) - y

# Fit ln(t) = alpha + beta * ln(|V|) by ordinary least squares
# on the seven measured medians (one point per graph size).
beta, alpha = np.polyfit(np.log(x), np.log(y), 1)
log_prediction = alpha + beta * np.log(x)
ss_res = np.sum((np.log(y) - log_prediction) ** 2)
ss_tot = np.sum((np.log(y) - np.mean(np.log(y))) ** 2)
r_squared = 1.0 - ss_res / ss_tot
x_fit = np.geomspace(x.min(), x.max(), 200)
y_fit = np.exp(alpha) * x_fit ** beta

ax.errorbar(x, y, yerr=np.vstack([lo, hi]), marker='o', linestyle='none',
            capsize=4, linewidth=1.5, label='Mediana (barras: P25--P75)')
ax.plot(x_fit, y_fit, linestyle='--', linewidth=1.5,
        label=f'Ajuste: expoente={beta:.4f}; R²={r_squared:.4f}')
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlabel('Quantidade de nós (|V|) - escala logarítmica')
ax.set_ylabel('Tempo mediano (ms) - escala logarítmica')
ax.set_title('Tempo de execução da análise completa: ajuste log-log')
ax.grid(True, which='both', alpha=0.25)
ax.legend(loc='best')
fig.tight_layout(); fig.savefig(FIG / 'benchmark_tempo.png', dpi=220); plt.close(fig)

print('Figuras geradas:')
for p in sorted(FIG.glob('*.png')):
    print(p.name, p.stat().st_size)
print('Amostra estratificada:', len(strat))
