from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FieldDefinition:
    """画面項目の表示名、入力種別、初期値、記載例などを保持する定義。"""

    key: str
    label: str
    kind: str = "textbox"
    height: int = 90
    default: str = ""
    example: str = ""


@dataclass(frozen=True)
class ConditionalOutputFormatItem:
    """特定の入力状態に応じて、出力形式へ追加する項目を保持する定義。"""

    field_key: str
    text: str
    insert_after: str
    include_when_empty: bool = True


@dataclass(frozen=True)
class PromptTemplate:
    """作業種別ごとのプロンプト構造を保持し、最終文面を生成する定義。"""

    work_type: str
    role_text: str
    output_format_items: tuple[str, ...]
    fields: tuple[FieldDefinition, ...]
    conditional_output_format_items: tuple[ConditionalOutputFormatItem, ...] = ()

    # 出力形式は条件付き項目を差し込んだ後に番号を振り直し、AIへの依頼内容を崩さない。
    # 例: 関連ソースが未入力の場合だけ、調査開始点として確認すべき関連ファイルの列挙を依頼する。
    def _render_output_format(self, values: dict[str, str]) -> str:
        output_items = list(self.output_format_items)

        for conditional_item in self.conditional_output_format_items:
            field_value = values.get(conditional_item.field_key, "").strip()
            should_include = not field_value if conditional_item.include_when_empty else bool(field_value)
            if not should_include or conditional_item.text in output_items:
                continue

            try:
                insert_index = output_items.index(conditional_item.insert_after) + 1
            except ValueError:
                insert_index = len(output_items)
            output_items.insert(insert_index, conditional_item.text)

        numbered_items = [f"{index}. {item}" for index, item in enumerate(output_items, start=1)]
        return "以下の形式で回答してください。\n\n" + "\n".join(numbered_items)

    # 入力された各項目をテンプレート順に並べ、AIへ貼り付ける最終プロンプトへ整形する。
    # 未入力の項目はAIへ渡す情報として意味を持たないため、見出しごと出力対象から除外する。
    def render(self, values: dict[str, str]) -> str:
        sections: list[str] = [
            "# 役割",
            self.role_text.strip(),
            "",
        ]

        for field in self.fields:
            content = values.get(field.key, "").strip()
            if not content:
                continue
            sections.extend([f"# {field.label}", content, ""])

        sections.extend(
            [
                "# 出力形式",
                self._render_output_format(values),
            ]
        )
        return "\n".join(sections).strip()


BUG_FIX_TEMPLATE = PromptTemplate(
    work_type="バグ修正",
    role_text=(
        "あなたは既存システムの保守開発を支援するエンジニアです。\n"
        "既存仕様への影響を最小限にしながら、原因調査と修正方針の整理を行ってください。"
    ),
    output_format_items=(
        "原因候補",
        "追加で確認すべきこと",
        "修正方針",
        "修正対象ファイル",
        "影響範囲",
        "テスト観点",
        "注意点",
    ),
    fields=(
        FieldDefinition("work_type", "作業種別", kind="option", default="バグ修正"),
        FieldDefinition(
            "consultation",
            "相談内容",
            height=80,
            example="ログイン画面で特定ユーザーだけログインできない原因を調べたい",
        ),
        FieldDefinition(
            "target",
            "対象",
            height=80,
            example="aaa-bbb-c1234",
        ),
        FieldDefinition(
            "source_location",
            "関連ソース・場所",
            height=80,
            example="src/auth/login.ts",
        ),
        FieldDefinition(
            "issue",
            "発生事象",
            height=100,
            example="正しいIDとパスワードを入力してもエラー画面に遷移する",
        ),
        FieldDefinition(
            "expected_behavior",
            "期待する動作",
            height=90,
            example="認証に成功した場合はトップ画面へ遷移する",
        ),
        FieldDefinition(
            "actual_behavior",
            "実際の動作",
            height=90,
            example="「認証に失敗しました」と表示され、ログインできない",
        ),
        FieldDefinition(
            "error_log",
            "エラー内容・ログ",
            height=120,
            example="Invalid password、401 Unauthorized、該当ログの抜粋",
        ),
        FieldDefinition(
            "known_facts",
            "現状わかっていること",
            height=120,
            example="管理者ユーザーでは再現せず、一般ユーザーのみ発生している",
        ),
        FieldDefinition(
            "constraints",
            "制約・注意点",
            height=100,
            example="DB構造は変更できない。既存APIのレスポンス形式は維持したい",
        ),
        FieldDefinition(
            "request_details",
            "依頼したいこと",
            height=100,
            example="原因候補、確認すべきファイル、修正方針を整理してほしい",
        ),
    ),
    conditional_output_format_items=(
        ConditionalOutputFormatItem(
            field_key="source_location",
            text="確認すべき関連ファイル・処理",
            insert_after="原因候補",
        ),
    ),
)


# 将来の作業種別追加時は、この辞書へテンプレート定義を登録する。
TEMPLATES: dict[str, PromptTemplate] = {
    BUG_FIX_TEMPLATE.work_type: BUG_FIX_TEMPLATE,
}
