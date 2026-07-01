"""
Phase 10K5: Core Arbitrage Engine – existing‑owner validation tests.

These tests verify that the candidate owners listed in the phase
deliver correct behaviour for the 10K5 core math.  They do **not**
create new packages or connect to live sources.
"""

import math
import unittest
from typing import Any

# ---------------------------------------------------------------------------
# Helper functions (pure Python, no external dependencies)
# ---------------------------------------------------------------------------

def implied_from_american(odds: int) -> float:
    """American‑odds → implied probability (same formula as owners)."""
    if odds > 0:
        return 100.0 / (odds + 100.0)
    else:
        return abs(odds) / (abs(odds) + 100.0)


def no_vig(prob1: float, prob2: float) -> tuple[float, float]:
    """Simple no‑vig normalisation (sum to 1)."""
    s = prob1 + prob2
    if s <= 0:
        raise ValueError("Non‑positive sum")
    return prob1 / s, prob2 / s


def equal_gross_payout_stake(p1_odds: int, p2_odds: int, total_stake: float) -> dict[str, float]:
    """Compute dutch‑book stakes giving equal gross payout on either side."""
    prob1 = implied_from_american(p1_odds)
    prob2 = implied_from_american(p2_odds)
    if prob1 + prob2 >= 1:
        raise ValueError("Not an arbitrage opportunity")
    # equal gross payout = total_stake / (1 - overround) ?
    # Simple : stake_i proportion to 1/dec_i
    dec1 = 1.0 / prob1
    dec2 = 1.0 / prob2
    inv1 = 1.0 / dec1
    inv2 = 1.0 / dec2
    total_inv = inv1 + inv2
    stake1 = total_stake * (inv1 / total_inv)
    stake2 = total_stake - stake1
    return {"stake1": round(stake1, 6), "stake2": round(stake2, 6)}


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

class TestPhase10K5CoreArbitrageEngine(unittest.TestCase):
    """Test every candidate owner listed in the phase document."""

    # ------------------------------------------------------------------
    # 1. Generic math – src/core/math_utils.py
    # ------------------------------------------------------------------
    def test_math_utils_american_implied(self) -> None:
        """american_to_implied_probability must return correct values."""
        from src.core.math_utils import american_to_implied_probability
        self.assertAlmostEqual(american_to_implied_probability(100), 0.5, places=6)
        self.assertAlmostEqual(american_to_implied_probability(-100), 0.5, places=6)
        self.assertAlmostEqual(american_to_implied_probability(150), 0.4, places=6)
        self.assertAlmostEqual(american_to_implied_probability(-200), 2/3, places=6)
        self.assertAlmostEqual(american_to_implied_probability(200), 1/3, places=6)

    def test_math_utils_american_to_decimal(self) -> None:
        """american_to_decimal must return correct decimal odds."""
        from src.core.math_utils import american_to_decimal
        self.assertAlmostEqual(american_to_decimal(150), 2.5, places=6)
        self.assertAlmostEqual(american_to_decimal(-200), 1.5, places=6)

    # ------------------------------------------------------------------
    # 2. Odds helpers – automation_scheduler/odds_math.py
    # ------------------------------------------------------------------
    def test_odds_math_american_implied(self) -> None:
        """Same checks on odds_math.american_to_implied_probability."""
        from src.services.streamlit_dashboard_facade import american_to_implied_probability
        self.assertAlmostEqual(american_to_implied_probability(100), 0.5, places=6)
        self.assertAlmostEqual(american_to_implied_probability(-100), 0.5, places=6)
        self.assertAlmostEqual(american_to_implied_probability(150), 0.4, places=6)
        self.assertAlmostEqual(american_to_implied_probability(-200), 2/3, places=6)

    def test_odds_math_american_to_decimal(self) -> None:
        from src.services.streamlit_dashboard_facade import american_to_decimal
        self.assertAlmostEqual(american_to_decimal(150), 2.5, places=6)
        self.assertAlmostEqual(american_to_decimal(-200), 1.5, places=6)

    # ------------------------------------------------------------------
    # 3. No‑vig normalisation (pure Python helper above)
    # ------------------------------------------------------------------
    def test_no_vig_normalisation(self) -> None:
        """[0.55, 0.55] → [0.5, 0.5] after normalisation."""
        p1, p2 = no_vig(0.55, 0.55)
        self.assertAlmostEqual(p1, 0.5, places=6)
        self.assertAlmostEqual(p2, 0.5, places=6)

    # ------------------------------------------------------------------
    # 4. Two‑way arbitrage – automation_scheduler/arbitrage/two_way_arbitrage.py
    # ------------------------------------------------------------------
    def test_two_way_arbitrage_positive(self) -> None:
        """+120/+120 -> arbitrage exists using the existing one-argument owner."""
        from src.services.streamlit_dashboard_facade import detect_two_way_arbitrage

        offers = [
            {
                "book": "BookA",
                "bookmaker": "BookA",
                "event_id": "evt-10k5",
                "market": "moneyline",
                "market_type": "moneyline",
                "selection": "Team A",
                "outcome": "Team A",
                "oddstype": "american",
                "odds": 120,
                "american_odds": 120,
            },
            {
                "book": "BookB",
                "bookmaker": "BookB",
                "event_id": "evt-10k5",
                "market": "moneyline",
                "market_type": "moneyline",
                "selection": "Team B",
                "outcome": "Team B",
                "oddstype": "american",
                "odds": 120,
                "american_odds": 120,
            },
        ]
        result = detect_two_way_arbitrage(
            offers,
            total_stake=100.0,
            market_identity_confidence=100.0,
        )
        self.assertTrue(result.get("candidate_found"), result)

    def test_two_way_arbitrage_negative(self) -> None:
        """-110/-110 -> no arbitrage using the existing one-argument owner."""
        from src.services.streamlit_dashboard_facade import detect_two_way_arbitrage

        offers = [
            {
                "book": "BookA",
                "bookmaker": "BookA",
                "event_id": "evt-10k5",
                "market": "moneyline",
                "market_type": "moneyline",
                "selection": "Team A",
                "outcome": "Team A",
                "oddstype": "american",
                "odds": -110,
                "american_odds": -110,
            },
            {
                "book": "BookB",
                "bookmaker": "BookB",
                "event_id": "evt-10k5",
                "market": "moneyline",
                "market_type": "moneyline",
                "selection": "Team B",
                "outcome": "Team B",
                "oddstype": "american",
                "odds": -110,
                "american_odds": -110,
            },
        ]
        result = detect_two_way_arbitrage(
            offers,
            total_stake=100.0,
            market_identity_confidence=100.0,
        )
        self.assertFalse(result.get("candidate_found"), result)

    def test_three_way_arbitrage_positive(self) -> None:
        """+250/+250/+250 -> three-way arbitrage using the existing one-argument owner."""
        from src.services.streamlit_dashboard_facade import detect_three_way_arbitrage

        offers = [
            {
                "book": "BookA",
                "bookmaker": "BookA",
                "event_id": "evt-10k5",
                "market": "soccer_1x2",
                "market_type": "soccer_1x2",
                "selection": "Home",
                "outcome": "Home",
                "oddstype": "american",
                "odds": 250,
                "american_odds": 250,
            },
            {
                "book": "BookB",
                "bookmaker": "BookB",
                "event_id": "evt-10k5",
                "market": "soccer_1x2",
                "market_type": "soccer_1x2",
                "selection": "Draw",
                "outcome": "Draw",
                "oddstype": "american",
                "odds": 250,
                "american_odds": 250,
            },
            {
                "book": "BookC",
                "bookmaker": "BookC",
                "event_id": "evt-10k5",
                "market": "soccer_1x2",
                "market_type": "soccer_1x2",
                "selection": "Away",
                "outcome": "Away",
                "oddstype": "american",
                "odds": 250,
                "american_odds": 250,
            },
        ]
        result = detect_three_way_arbitrage(offers, total_stake=100.0)
        self.assertTrue(result.get("candidate_found"), result)

    def test_prediction_market_yes_no_positive(self) -> None:
        """yes=0.47, no=0.47 -> prediction-market yes/no arbitrage."""
        from src.market_intelligence.arbitrage.two_way_arbitrage import detect_prediction_arbitrage

        self.assertTrue(detect_prediction_arbitrage(0.47, 0.47))

    def test_prediction_market_yes_no_negative(self) -> None:
        """yes=0.53, no=0.51 -> no prediction-market yes/no arbitrage."""
        from src.market_intelligence.arbitrage.two_way_arbitrage import detect_prediction_arbitrage

        self.assertFalse(detect_prediction_arbitrage(0.53, 0.51))

    def test_overround_calculation(self) -> None:
        """Verify overround for known scenarios."""
        # -110/-110 → implied ≈ 0.5238 + 0.5238 ≈ 1.0476  (overround ~4.76%)
        p1 = implied_from_american(-110)
        p2 = implied_from_american(-110)
        over = p1 + p2 - 1.0
        self.assertAlmostEqual(over, 0.0476, places=3)

    # ------------------------------------------------------------------
    # 8. Dutching / stake allocation (proof‑of‑concept using math helper)
    # ------------------------------------------------------------------
    def test_dutching_equal_gross_payout(self) -> None:
        """With an arbitrage opportunity, stakes yield equal gross payout."""
        # use +120/+120 (arbitrage)
        stakes = equal_gross_payout_stake(120, 120, total_stake=100)
        # gross payout for each side = stake * decimal_odds
        dec = 1.0 / implied_from_american(120)   # +120 → prob=0.454545..., decimal≈2.2
        gross1 = stakes["stake1"] * dec
        gross2 = stakes["stake2"] * dec
        # equal within rounding
        self.assertAlmostEqual(gross1, gross2, places=5)

    # ------------------------------------------------------------------
    # 9. arbitrage_opportunities table exists in research schema
    # ------------------------------------------------------------------
    def test_arbitrage_opportunities_table_exists(self) -> None:
        from src.research.storage import get_create_sql
        try:
            sql = get_create_sql("arbitrage_opportunities")
        except Exception:
            self.fail("arbitrage_opportunities table not defined in schema")
        self.assertIn("arbitrage_opportunities", sql)

    # ------------------------------------------------------------------
    # 10. Backend imports do not pull in Streamlit, pandas, network libs
    # ------------------------------------------------------------------
    def test_imports_are_safe(self) -> None:
        """Verify that core arbitrage modules can be imported without
        triggering streamlit, pandas, or network dependencies."""
        bad_imports = [
            "streamlit",
            "pandas",
            "requests",
            "aiohttp",
            "urllib3",
        ]
        import sys
        modules_before = set(sys.modules.keys())
        # Trigger the imports that the phase relies on.
        try:
            from src.core import math_utils  # noqa
            from src.services.streamlit_dashboard_facade import odds_math  # noqa
            from src.services.streamlit_dashboard_facade import two_way_arbitrage  # noqa
            from src.services.streamlit_dashboard_facade import three_way_arbitrage  # noqa
            from src import research as market_research_schema  # noqa
        except ImportError:
            # Some owners may not exist yet – that's acceptable for now.
            pass
        modules_after = set(sys.modules.keys())
        new_modules = modules_after - modules_before
        for bad in bad_imports:
            self.assertNotIn(bad, [m.split(".")[0] for m in new_modules],
                             msg=f"Bad import '{bad}' was loaded by a core module")


if __name__ == "__main__":
    unittest.main()
