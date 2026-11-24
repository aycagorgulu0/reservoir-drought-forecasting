# Notebooks

Notebooks are for **exploration and presenting results**. The data pipeline itself lives in `src/`.

## Rules

1. Notebooks only **read** files from `data/processed/` (or `data/interim/`). They never write data that a pipeline step depends on.
2. Reusable code (formulas, feature functions) belongs in a module in `src/`, imported here:
   ```python
   import sys; sys.path.insert(0, "../src")
   from paths import PROCESSED, FIGURES
   ```
3. Each notebook has **one owner**, which avoids merge conflicts. Notebooks are long JSON files and hard to merge.
4. Before committing, run **Kernel → Restart & Run All**, so the saved outputs match the code.
5. Name notebooks `<number>-<topic>.ipynb`: `1.x` for Deliverable 2 (exploration), `2.x` for Deliverable 3 (modelling).

## Planned

| Notebook | Deliverable | Content |
|---|---|---|
| `1.0-eda-storage-and-rainfall.ipynb` | 2 | Lag correlations between rainfall and storage, seasonal vs. hyperannual behaviour, class balance |
| `1.1-reservoir-clustering.ipynb` | 2/3 | First k-means / hierarchical grouping of reservoirs (H4) |
| `2.0-model-results.ipynb` | 3 | Model comparison, errors per reservoir group (H1-H3) |
