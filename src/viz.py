import matplotlib.pyplot as plt
import os
from typing import List
from agent import Agent

OUTPUT_DIR = "outputs"

def plot_opinions_time_series(timeseries, outpath=None):
    steps = [t["step"] for t in timeseries]
    means = [t["mean_opinion"] for t in timeseries]
    vars_ = [t["var_opinion"] for t in timeseries]
    plt.figure()
    plt.plot(steps, means, label="mean opinion")
    plt.fill_between(steps, [m - v for m,v in zip(means,vars_)], [m + v for m,v in zip(means,vars_)], alpha=0.2)
    plt.xlabel("Step")
    plt.ylabel("Opinion")
    plt.legend()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = outpath or os.path.join(OUTPUT_DIR, "opinion_timeseries.png")
    plt.savefig(out)
    plt.close()
    return out

def scatter_opinion_valence(population: List[Agent], outpath=None):
    opinions = [a.state.opinion for a in population]
    valences = [a.state.valence for a in population]
    plt.figure(figsize=(6,6))
    plt.scatter(opinions, valences, c=opinions, cmap="coolwarm", vmin=-1, vmax=1)
    plt.xlabel("Opinion")
    plt.ylabel("Emotion valence")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = outpath or os.path.join(OUTPUT_DIR, "opinion_valence_scatter.png")
    plt.colorbar(label="opinion")
    plt.savefig(out)
    plt.close()
    return out