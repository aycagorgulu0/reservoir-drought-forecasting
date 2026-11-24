"""Study area definition, shared by every step: basins, key reservoirs and combined systems."""

# Basin name in BD-Embalses -> role in the study.
STUDY_BASINS = ["Tajo", "Guadiana", "Júcar"]
REFERENCE_BASINS = ["Duero"]  # basin used by Baron et al. (2026); comparison only
ALL_BASINS = STUDY_BASINS + REFERENCE_BASINS

KEY_RESERVOIRS = ["Entrepeñas", "Buendía", "Alarcón", "Contreras"]

# Reservoir pairs managed as one system. The Tajo-Segura transfer rules use the
# combined Entrepeñas + Buendía storage; Alarcón + Contreras regulate the Júcar.
# Time-based split (Deliverable 1). Anything fitted on the data (climatologies,
# State Index reference values, seasonal share) uses only the training years.
TRAIN_END = "2016-12-01"   # train: Jan 1988 - Dec 2016
VALID_END = "2020-12-01"   # validation: 2017 - 2020; test: 2021 onwards

SYSTEMS = {
    "Entrepeñas + Buendía": {"basin": "Tajo", "members": ["Entrepeñas", "Buendía"]},
    "Alarcón + Contreras": {"basin": "Júcar", "members": ["Alarcón", "Contreras"]},
}
