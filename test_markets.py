import unittest
from market_classifier import classify_market
class MarketTests(unittest.TestCase):
    def test_anytime(self): self.assertEqual(classify_market('Anytime Goalscorer')['threshold'],1)
    def test_double(self): self.assertEqual(classify_market('Player Goals Over 1.5')['threshold'],2)
    def test_triple(self): self.assertEqual(classify_market('Player Goals Over 2.5')['threshold'],3)
    def test_assist(self): self.assertEqual(classify_market('Player Assists 1+')['category'],'assists')
    def test_first_half(self): self.assertEqual(classify_market('First Half Anytime Goalscorer')['period'],'first_half')
    def test_unknown(self): self.assertTrue(classify_market('Shots on Target')['needs_review'])
    def test_ambiguous(self): self.assertTrue(classify_market('Player Goals')['needs_review'])
if __name__=='__main__': unittest.main()
