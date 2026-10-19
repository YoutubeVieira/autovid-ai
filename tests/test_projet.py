"""Projet modifiable : les choix faits dans la plateforme reviennent bien dans le montage."""
import unittest

from autovid import projet as pj
from autovid import sfx


def imp(frame, score, nom):
    return {"frame": frame, "score": score, "track": 0, "eff": 28, "contact": {"cible": "air", "rotation": False},
            "info": {"nom": nom, "kind": "pied", "membre": "JAMBE DROITE", "hook": ("A", "B"),
                     "risque": ("GENOU", "x"), "muscles": []}}


class ProjetTest(unittest.TestCase):
    def test_roundtrip_edits(self):
        impacts = [imp(100, 0.5, "HIGH KICK"), imp(300, 0.9, "LOW KICK")]
        segs = [{"id": "hook", "fr": "A. B."}, {"id": 0, "fr": "Un."}, {"id": 1, "fr": "Deux."},
                {"id": "outro", "fr": "Fin."}]
        data = pj.combat_export("x.mp4", impacts, segs, {"style": "fluide"}, lambda i: "LIGNE")
        data["analyses"][0]["actif"] = False
        a = data["analyses"][1]
        a.update(titre="meia-lua", ligne2="la hanche", voix="Nouvelle voix.", son="sac", risque="")
        a["effets"]["rond"] = False
        data["accroche"].update(l1="regarde ça", voix="Regarde ça.")
        kept, voices, every = pj.combat_apply(data, [imp(100, 0.5, "HIGH KICK"), imp(300, 0.9, "LOW KICK")])
        self.assertEqual([m["frame"] for m in kept], [300])
        info = kept[0]["info"]
        self.assertEqual((info["nom"], info["cle"]), ("MEIA-LUA", "LA HANCHE"))
        self.assertFalse(info["fx"]["rond"])
        self.assertIsNone(info["risque"])
        self.assertEqual(kept[0]["contact"]["cible"], "sac")
        self.assertEqual(info["hook"][0], "REGARDE ÇA")
        self.assertEqual(voices[0], "Nouvelle voix.")
        segs2 = pj.apply_voices([{"id": 0, "fr": "x"}, {"id": "hook", "fr": "y"}], voices)
        self.assertEqual(segs2[0]["fr"], "Nouvelle voix.")
        back = pj.combat_export("x.mp4", kept, segs2, {}, lambda i: "", every)
        self.assertEqual([a["actif"] for a in back["analyses"]], [False, True])   # la désactivée reste visible

    def test_no_sound_option(self):
        self.assertEqual(sfx.contact_fx({"cible": "aucun"}, "pied"), [])
        self.assertEqual(pj.hex_rgb("#22ff66"), (0x22, 0xff, 0x66))
        self.assertIsNone(pj.hex_rgb("vert"))


if __name__ == "__main__":
    unittest.main()
