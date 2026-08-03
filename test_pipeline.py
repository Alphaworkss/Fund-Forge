import unittest
from news_pipeline import clean_text, detect_pakistan_entities, detect_sectors, classify_event

class TestNewsPipeline(unittest.TestCase):
    
    # ----------------------------------------------------
    # TEST 1: Text Cleaning Function
    # ----------------------------------------------------
    def test_clean_text(self):
        raw_html = "<p>State Bank <b>announces</b> new policy &amp; interest rate.</p>"
        expected_output = "State Bank announces new policy & interest rate."
        self.assertEqual(clean_text(raw_html), expected_output)
        
    # ----------------------------------------------------
    # TEST 2: Pakistan Entity Recognition
    # ----------------------------------------------------
    def test_entity_recognition(self):
        text = "The MPC of the SBP met yesterday to discuss loans with the IMF."
        # The script should detect SBP and IMF
        detected = detect_pakistan_entities(text)
        self.assertIn("State Bank of Pakistan (SBP)", detected)
        self.assertIn("International Monetary Fund (IMF)", detected)

    # ----------------------------------------------------
    # TEST 3: Business Sector Detection
    # ----------------------------------------------------
    def test_sector_detection(self):
        text_banking = "Meezan Bank reports record quarterly profits."
        text_energy = "OGRA raises petrol prices across the country."
        
        self.assertEqual(detect_sectors(text_banking), "Banking & Finance")
        self.assertEqual(detect_sectors(text_energy), "Energy & Power")

    # ----------------------------------------------------
    # TEST 4: Event Classification
    # ----------------------------------------------------
    def test_event_classification(self):
        text_budget = "Government presents annual budget proposals in Parliament."
        text_inflation = "CPI inflation rises by 1.2% in weekly report."
        
        self.assertEqual(classify_event(text_budget), "Budget News")
        self.assertEqual(classify_event(text_inflation), "Inflation")

if __name__ == "__main__":
    print("Running News Pipeline Unit Tests...")
    unittest.main()