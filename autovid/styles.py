"""Préréglages de style reconstitués à partir des deux vidéos de référence.

Couleurs au format ASS : &HAABBGGRR (AA = transparence, 00 = opaque).
"""

STYLES = {
    # Vidéo 1 « BinCombat » : compilation de techniques, titre pinceau 2 lignes, coupe sur 2 temps.
    "bincombat": {
        "beats_per_shot": 2,
        "landscape_layout": "fit_blur",
        "fit_offset_y": 120,            # la vidéo paysage est descendue sous le bandeau titre
        "grade": "eq=contrast=1.06:saturation=1.12,unsharp=5:5:0.6",
        "title_anim": "cut",            # le titre change sec à chaque technique, sans animation
        "watermark_y": 1700,
        "fonts": {
            "kicker": ("Permanent Marker", 60, "&H0000E6FF"),   # jaune
            "title": ("Permanent Marker", 92, "&H00FFFFFF"),    # blanc
            "subtitle": ("Permanent Marker", 50, "&H00FFFFFF"),
            "step": ("Permanent Marker", 84, "&H00FFFFFF"),
            "cta": ("Permanent Marker", 100, "&H00FFFFFF"),
            "watermark": ("Anton", 46, "&H66DDDDDD"),
        },
        "kicker_y": 150, "title_y": 255,
        "outline": 3, "shadow": 5,
    },
    # Vidéo 2 « Pull counter step-by-step » : hook réaction, étapes numérotées, sur-accentuation, flashs.
    "stepbystep": {
        "beats_per_shot": 2,
        "landscape_layout": "fit_blur",
        "fit_offset_y": 0,
        "grade": "eq=contrast=1.15:saturation=1.25:brightness=0.02,unsharp=7:7:1.3",
        "title_anim": "pop",
        "watermark_y": 1700,
        "fonts": {
            "kicker": ("Anton", 54, "&H0000E6FF"),
            "title": ("Anton", 120, "&H00FFFFFF"),
            "subtitle": ("Permanent Marker", 54, "&H00FFFFFF"),
            "step": ("Anton", 92, "&H00FFFFFF"),
            "cta": ("Anton", 104, "&H00FFFFFF"),
            "watermark": ("Anton", 46, "&H66DDDDDD"),
        },
        "kicker_y": 110, "title_y": 215,
        "outline": 5, "shadow": 6,
    },
}


def get_style(name, overrides=None):
    if name not in STYLES:
        raise ValueError(f"Style inconnu « {name} ». Disponibles : {', '.join(STYLES)}")
    style = {**STYLES[name], "fonts": dict(STYLES[name]["fonts"])}
    style.update(overrides or {})
    return style
