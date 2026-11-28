"""Correcteur de narration : nombres en lettres, graphie phonétique, mots étrangers, comparaison avec l'audio."""
import unittest

from autovid import phonetique as ph


class EcrireTest(unittest.TestCase):
    def test_numbers_in_three_languages(self):
        self.assertIn("mille neuf cent dix-neuf", ph.ecrire("En 1919, 10 femmes.", "fr"))
        self.assertIn("dix femmes", ph.ecrire("En 1919, 10 femmes.", "fr"))
        self.assertIn("mil novecentos e dezenove", ph.ecrire("Em 1919.", "pt"))
        self.assertNotIn(",", ph.ecrire("1919", "pt"))
        self.assertIn("nineteen nineteen", ph.ecrire("In 1919.", "en"))
        self.assertIn("vingt-cinq février", ph.ecrire("Le 25/02/1922.", "fr"))
        self.assertIn("quinze por cento", ph.ecrire("15 %", "pt"))
        self.assertIn("cinquenta reais", ph.ecrire("R$ 50", "pt"))

    def test_phonetic_spelling_keeps_word_count(self):
        shown = ph.ecrire("En 1919, il en avait 10 et elle 6. Dix ans.", "fr")
        said = ph.dire(shown, "fr")
        self.assertIn("dize-neuf", said)
        self.assertIn("disse", said)
        self.assertIn("sisse", said)
        self.assertIn("diz ans", said)
        self.assertEqual(len(shown.split()), len(said.split()))

    def test_foreign_words_get_their_country_accent(self):
        self.assertIn("[fr]Versailles[/fr]", ph.marquer("O tribunal de Versailles.", "pt"))
        self.assertIn("[pt]ginga[/pt]", ph.marquer("La ginga reprend.", "fr"))
        self.assertEqual(ph.marquer("Le [pt]aú[/pt] part.", "fr"), "Le [pt]aú[/pt] part.")   # pas de double balise
        self.assertEqual([lg for _, lg in ph.morceaux("Le [pt]aú[/pt] part.", "fr")], ["fr", "pt", "fr"])


class ComparerTest(unittest.TestCase):
    def test_detects_wrong_number_and_tolerates_spelling(self):
        self.assertTrue(ph.comparer("En mille neuf cent dix-neuf.", "en 1999.", "fr"))
        self.assertFalse(ph.comparer("En mille neuf cent dix-neuf.", "En 1919.", "fr"))
        self.assertFalse(ph.comparer("Dez famílias.", "Deis famílias.", "pt"))
        self.assertFalse(ph.comparer("Le [pt]aú[/pt] et la [pt]ginga[/pt].", "Le A'O'Ela Jing.", "fr", ["aú", "ginga"]))


if __name__ == "__main__":
    unittest.main()
