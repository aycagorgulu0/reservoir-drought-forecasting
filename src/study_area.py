"""Study area definition, shared by every step: basins, key reservoirs and combined systems."""

# Basin name in BD-Embalses -> role in the study.
STUDY_BASINS = ["Tajo", "Guadiana", "Júcar"]
REFERENCE_BASINS = ["Duero"]  # basin used by Baron et al. (2026); comparison only
ALL_BASINS = STUDY_BASINS + REFERENCE_BASINS

KEY_RESERVOIRS = ["Entrepeñas", "Buendía", "Alarcón", "Contreras"]

# Reservoir pairs managed as one system. The Tajo-Segura transfer rules use the
# combined Entrepeñas + Buendía storage; Alarcón + Contreras regulate the Júcar.
SYSTEMS = {
    "Entrepeñas + Buendía": {"basin": "Tajo", "members": ["Entrepeñas", "Buendía"]},
    "Alarcón + Contreras": {"basin": "Júcar", "members": ["Alarcón", "Contreras"]},
}
