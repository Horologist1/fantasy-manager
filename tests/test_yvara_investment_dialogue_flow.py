import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
YVARA_SCRIPT = ROOT / "game" / "scripts" / "yvara" / "yvara_complete.rpy"


def label_block(source: str, label: str) -> str:
    start = source.index(f"label {label}:")
    match = re.search(r"(?m)^label [A-Za-z0-9_]+:", source[start + 1 :])
    end = start + 1 + match.start() if match else len(source)
    return source[start:end]


class YvaraInvestmentDialogueFlowTests(unittest.TestCase):
    def test_visit_menu_has_input_guard_after_investment_dialogue(self):
        source = YVARA_SCRIPT.read_text(encoding="utf-8")
        block = label_block(source, "yvara_visit_menu")

        menu_index = block.index("    menu:")
        guard_match = re.search(
            r"renpy\.pause\(\s*0\.\d+\s*,\s*hard\s*=\s*True\s*\)",
            block[:menu_index],
        )

        self.assertIsNotNone(
            guard_match,
            "Yvara's visit menu is exposed immediately after the final investment "
            "line, allowing the dismissing click/tap to select the next option.",
        )


if __name__ == "__main__":
    unittest.main()
