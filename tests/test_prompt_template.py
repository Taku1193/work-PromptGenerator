import unittest

from src.prompt_templates import BUG_FIX_TEMPLATE


class PromptTemplateTest(unittest.TestCase):
    # 未入力項目がある場合は、AIへ渡す不要な見出しを増やさないよう項目ごと省くことを確認する。
    def test_render_omits_empty_values(self) -> None:
        prompt = BUG_FIX_TEMPLATE.render(
            {
                "work_type": "バグ修正",
                "consultation": "",
                "target": "ログインAPI",
            }
        )

        self.assertIn("# 作業種別\nバグ修正", prompt)
        self.assertIn("# 対象\nログインAPI", prompt)
        self.assertNotIn("# 相談内容", prompt)
        self.assertNotIn("未入力", prompt)

    # 期待する見出し群が崩れず出力されることを確認し、テンプレート改修時の回帰を防ぐ。
    def test_render_keeps_required_sections(self) -> None:
        prompt = BUG_FIX_TEMPLATE.render({"work_type": "バグ修正"})

        self.assertIn("# 役割", prompt)
        self.assertIn("# 作業種別\nバグ修正", prompt)
        self.assertIn("# 出力形式", prompt)


if __name__ == "__main__":
    unittest.main()
