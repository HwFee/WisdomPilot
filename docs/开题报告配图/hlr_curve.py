# -*- coding: utf-8 -*-
"""HLR 遗忘曲线：p = 2^(-Δ/h)，精确数学绘制。"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(10.5, 6.0), dpi=200)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

# 三条曲线：半衰期 h = 1 / 3.24 / 5.83 天（初始→答对1次→答对2次）
half_lives = [(1.0, "#94a3b8", "h = 1 天（初学）"),
              (3.24, "#f59e0b", "h = 3.24 天（复习 1 次）"),
              (5.83, "#0ea5e9", "h = 5.83 天（复习 2 次）")]
delta = np.linspace(0, 30, 800)
for h, c, label in half_lives:
    p = 2 ** (-delta / h)
    ax.plot(delta, p, color=c, linewidth=2.6, label=label, zorder=3)
    # 标注 Δ=h 处 p=0.5
    x_at = h
    ax.plot([x_at], [0.5], "o", color=c, markersize=5, zorder=4)
    ax.annotate(f"Δ={h} → p=0.5", xy=(x_at, 0.5), xytext=(x_at - 1.2, 0.56),
                fontsize=9, color=c)

# 水平参考线 p=0.5
ax.axhline(0.5, color="#64748b", ls="--", lw=1.0, alpha=0.6)

# 掌握等级阈值带（右侧）
bands = [(0.8, 1.0, "#0ea5e9", "精通 ≥ 0.8"),
         (0.6, 0.8, "#22c55e", "熟练 ≥ 0.6"),
         (0.3, 0.6, "#f59e0b", "熟悉 ≥ 0.3"),
         (0.0, 0.3, "#e2e8f0", "初识 < 0.3")]
for lo, hi, c, label in bands:
    ax.axhspan(lo, hi, color=c, alpha=0.10, zorder=1)
    ax.text(30.6, (lo + hi) / 2, label, fontsize=8.5, va="center", color="#334155")

# 公式标注
ax.text(0.03, 0.93, r"$p = 2^{-\Delta / h}$", fontsize=20, color="#0f172a",
        transform=ax.transAxes, va="top",
        bbox=dict(boxstyle="round,pad=0.4", fc="#f1f5f9", ec="#94a3b8", lw=1))
ax.text(0.03, 0.86, "Δ = 距上次答对的天数，h = 当前半衰期", fontsize=9,
        transform=ax.transAxes, va="top", color="#475569")

# 坐标轴
ax.set_xlabel("距上次复习的天数 Δ（天）", fontsize=12)
ax.set_ylabel("回忆概率 p", fontsize=12)
ax.set_xlim(0, 31.6)
ax.set_ylim(0, 1.02)
ax.set_xticks(range(0, 31, 5))
ax.set_yticks(np.arange(0, 1.01, 0.1))
ax.grid(axis="y", color="#e2e8f0", lw=0.6)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(loc="center right", fontsize=10, frameon=True, edgecolor="#cbd5e1")

plt.title("HLR 半衰期回归记忆模型 · 遗忘曲线", fontsize=14, pad=12)
plt.tight_layout()
plt.savefig("04_hlr_curve_exact.png", dpi=200, facecolor="white")
print("saved 04_hlr_curve_exact.png")
