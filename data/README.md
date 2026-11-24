# Data

| Folder | Contents | In git? |
|---|---|---|
| `raw/` | Original files exactly as downloaded | No (too large) |
| `interim/` | Files produced by the scripts from `raw/` | No (can be rebuilt) |
| `processed/` | Final tables used for modelling | Yes, if small |

## How to get the raw data

### BD-Embalses (MITECO reservoir bulletin)

1. Open the MITECO *Boletín Hidrológico* page:
   https://www.miteco.gob.es/es/agua/temas/evaluacion-de-los-recursos-hidricos/boletin-hidrologico.html
2. Download the *Base de datos del Boletín Hidrológico* (Microsoft Access file).
3. Save it as `data/raw/BD-Embalses.mdb`. The version used here is 213 MB, with table `T_Datos Embalses 1988-2026` (724,217 weekly rows, 6 Oct 1987 to 27 Oct 2026).
4. Run `python src/01_convert_to_csv.py` to create `data/interim/reservoirs_spain_weekly.csv`.
