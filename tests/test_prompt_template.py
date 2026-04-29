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

    # 記載例は入力補助のための表示情報であり、未入力項目の本文として出力しないことを確認する。
    def test_render_does_not_include_examples_for_empty_values(self) -> None:
        prompt = BUG_FIX_TEMPLATE.render({"work_type": "バグ修正"})
        target_field = next(field for field in BUG_FIX_TEMPLATE.fields if field.key == "target")

        self.assertEqual("aaa-bbb-c1234", target_field.example)
        self.assertNotIn(target_field.example, prompt)

    # 関連ソースが未入力の場合は、AIに調査開始点を洗い出させるための出力項目を追加する。
    def test_render_adds_related_file_check_when_source_location_is_empty(self) -> None:
        prompt = BUG_FIX_TEMPLATE.render(
            {
                "work_type": "バグ修正",
                "source_location": "",
            }
        )

        self.assertIn("2. 確認すべき関連ファイル・処理", prompt)
        self.assertIn("3. 追加で確認すべきこと", prompt)

    # 関連ソースが入力済みの場合は、その場所を前提に調査するため追加の洗い出し項目を出さない。
    def test_render_omits_related_file_check_when_source_location_exists(self) -> None:
        prompt = BUG_FIX_TEMPLATE.render(
            {
                "work_type": "バグ修正",
                "source_location": "src/auth/login.ts",
            }
        )

        self.assertNotIn("確認すべき関連ファイル・処理", prompt)
        self.assertIn("2. 追加で確認すべきこと", prompt)


if __name__ == "__main__":
    unittest.main()
