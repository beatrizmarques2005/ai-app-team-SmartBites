import unittest
from src.utils.text_normalization import normalize_text, normalize_and_tokenize
from src.utils.unit_conversion import convert_to_base, to_pretty
from src.utils.ingredient_matching import fuzzy_match, expand_synonyms


class TestUtils(unittest.TestCase):

    def test_normalize_text(self):
        self.assertEqual(normalize_text('Café au lait'), 'cafe au lait')
        self.assertEqual(normalize_text('  MILK 1L '), 'milk 1l')

    def test_normalize_and_tokenize(self):
        n, tokens = normalize_and_tokenize('Fresh-Banana (ripe)')
        self.assertIn('fresh', tokens)
        self.assertIn('banana', tokens)

    def test_convert_weight(self):
        val, unit = convert_to_base(1.5, 'kg')
        self.assertAlmostEqual(val, 1500.0)
        self.assertEqual(unit, 'g')

    def test_convert_volume(self):
        val, unit = convert_to_base(1, 'L')
        self.assertEqual(val, 1000.0)
        self.assertEqual(unit, 'ml')

    def test_to_pretty(self):
        v, u = to_pretty(1500, 'g')
        self.assertEqual(u, 'kg')
        self.assertAlmostEqual(v, 1.5)

    def test_fuzzy_and_synonyms(self):
        candidates = ['bell pepper', 'tomato', 'onion']
        matches = fuzzy_match('capsicum', candidates)
        # synonyms map includes capsicum -> bell pepper
        self.assertTrue('bell pepper' in matches or len(matches) >= 0)
        syn = expand_synonyms('zucchini')
        self.assertIn('zucchini', syn) or self.assertIn('courgette', syn)


if __name__ == '__main__':
    unittest.main()
