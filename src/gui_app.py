from __future__ import annotations

import sys
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox, ttk

from src.prompt_templates import BUG_FIX_TEMPLATE, PromptTemplate, TEMPLATES


TextInputWidget = tk.Text


# OS ごとに、日本語表示が比較的安定しやすいフォント候補を優先順で定義する。
FONT_CANDIDATES_BY_PLATFORM = {
    "win32": ["Yu Gothic UI", "Meiryo", "BIZ UDPGothic", "MS UI Gothic"],
    "linux": ["Noto Sans CJK JP", "Noto Sans JP", "IPAexGothic", "TakaoGothic"],
    "darwin": ["Hiragino Sans", "Yu Gothic", "Osaka"],
}


class PromptGeneratorApp(tk.Tk):
    """入力フォームと生成結果表示をまとめて管理するメインウィンドウ。"""

    # アプリ全体のウィンドウ設定と、画面生成に必要な状態を初期化する。
    def __init__(self) -> None:
        super().__init__()
        self.title("AI相談プロンプト生成ツール")
        self.geometry("1280x920")
        self.minsize(1080, 760)

        self.ui_font_family = self._resolve_japanese_font_family()
        self.template_names = list(TEMPLATES.keys())
        self.template_var = tk.StringVar(value=BUG_FIX_TEMPLATE.work_type)
        self.status_var = tk.StringVar(value="入力内容をもとにプロンプトを生成します。")
        self.input_widgets: dict[str, TextInputWidget | ttk.Combobox] = {}
        self.output_box: TextInputWidget | None = None

        self.configure(background="#f3f4f6")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_ui()

    # 実行環境で利用可能なフォント一覧から、日本語表示に適したフォント名を選定する。
    def _resolve_japanese_font_family(self) -> str:
        available_fonts = {font.lower(): font for font in tkfont.families(self)}
        platform_candidates = FONT_CANDIDATES_BY_PLATFORM.get(sys.platform, [])

        for candidate in platform_candidates:
            resolved = available_fonts.get(candidate.lower())
            if resolved:
                return resolved

        return "TkDefaultFont"

    # 画面全体で共通利用するフォント設定を返し、日本語表示の文字化けを避けやすくする。
    def _ui_font(self, size: int, weight: str = "normal") -> tuple[str, int, str]:
        return (self.ui_font_family, size, weight)

    # 標準 tkinter の入力欄へ渡すフォント指定を返し、日本語 IME の変換中表示を安定させる。
    def _tk_text_font(self, size: int, weight: str = "normal") -> tuple[str, int, str]:
        return (self.ui_font_family, size, weight)

    # customtkinter の独自 Textbox は環境によって日本語 IME と相性が出るため、
    # 実際に文字を入力する欄は標準 tkinter の Text を使って構築する。
    def _create_text_input(self, parent: tk.Widget, height: int) -> TextInputWidget:
        line_count = max(3, height // 24)
        text_widget = tk.Text(
            parent,
            height=line_count,
            wrap="word",
            font=self._tk_text_font(size=13),
            background="#ffffff",
            foreground="#111827",
            insertbackground="#111827",
            selectbackground="#bfdbfe",
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=8,
            undo=True,
            highlightthickness=1,
            highlightbackground="#d1d5db",
            highlightcolor="#2563eb",
        )
        # 環境や Tk のバージョンによって Shift+Enter が通常 Enter と別イベントとして
        # 扱われることがあるため、複数行入力で使う改行キーを明示的に登録する。
        text_widget.bind("<Return>", self._insert_newline)
        text_widget.bind("<KP_Enter>", self._insert_newline)
        text_widget.bind("<Shift-Return>", self._insert_newline)
        text_widget.bind("<Shift-KP_Enter>", self._insert_newline)
        return text_widget

    # Text ウィジェット上の Enter はフォーム送信ではなく、複数行入力の改行として扱う。
    def _insert_newline(self, event: tk.Event) -> str:
        event.widget.insert("insert", "\n")
        return "break"

    # 現在選択されている作業種別に対応するテンプレート定義を返す。
    @property
    def active_template(self) -> PromptTemplate:
        return TEMPLATES[self.template_var.get()]

    # メイン画面の大枠を作り、入力パネルと出力パネルを配置する。
    def _build_ui(self) -> None:
        self._configure_style()

        container = ttk.Frame(self, padding=16)
        container.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(1, weight=1)

        header = ttk.Frame(container)
        header.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 12), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ttk.Label(
            header,
            text="AI相談プロンプト生成ツール",
            font=self._ui_font(size=24, weight="bold"),
            style="Title.TLabel",
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = ttk.Label(
            header,
            text="バグ修正・不具合調査の相談内容を整理し、AIへ貼り付けやすいプロンプトを生成します。",
            font=self._ui_font(size=13),
            style="Body.TLabel",
        )
        subtitle.grid(row=1, column=0, pady=(6, 0), sticky="ew")

        input_panel = self._create_scrollable_panel(container)
        input_panel["outer"].grid(row=1, column=0, padx=(20, 10), pady=(0, 20), sticky="nsew")
        input_panel["outer"].grid_columnconfigure(0, weight=1)
        input_panel["outer"].grid_rowconfigure(0, weight=1)
        input_panel["content"].grid_columnconfigure(0, weight=1)

        output_panel = ttk.Frame(container, padding=16, style="Panel.TFrame")
        output_panel.grid(row=1, column=1, padx=(10, 20), pady=(0, 20), sticky="nsew")
        output_panel.grid_columnconfigure(0, weight=1)
        output_panel.grid_rowconfigure(1, weight=1)

        self._build_input_fields(input_panel["content"])
        self._build_output_area(output_panel)

    # 標準 tkinter / ttk の見た目をまとめて設定し、customtkinter 依存を避ける。
    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f3f4f6")
        style.configure("Panel.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        style.configure("Title.TLabel", background="#f3f4f6", foreground="#111827")
        style.configure("Body.TLabel", background="#f3f4f6", foreground="#374151")
        style.configure("Field.TLabel", background="#ffffff", foreground="#111827")
        style.configure("Status.TLabel", background="#ffffff", foreground="#374151")
        style.configure("TButton", font=self._ui_font(size=13, weight="bold"), padding=(10, 8))
        style.configure("TCombobox", font=self._ui_font(size=13), padding=6)

    # 入力欄が多いため、Canvas と Scrollbar で標準 tkinter のスクロール領域を構築する。
    def _create_scrollable_panel(self, parent: tk.Widget) -> dict[str, tk.Widget]:
        outer = ttk.Frame(parent, padding=16, style="Panel.TFrame")
        canvas = tk.Canvas(outer, background="#ffffff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        content = ttk.Frame(canvas, style="Panel.TFrame")
        window_id = canvas.create_window((0, 0), window=content, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        def resize_scroll_region(_: tk.Event) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def resize_content_width(event: tk.Event) -> None:
            canvas.itemconfigure(window_id, width=event.width)

        content.bind("<Configure>", resize_scroll_region)
        canvas.bind("<Configure>", resize_content_width)
        return {"outer": outer, "content": content}

    # テンプレート定義に基づいて入力欄と操作ボタンを動的に構築する。
    def _build_input_fields(self, parent: tk.Widget) -> None:
        for row_index, field in enumerate(self.active_template.fields):
            label = ttk.Label(
                parent,
                text=field.label,
                font=self._ui_font(size=14, weight="bold"),
                style="Field.TLabel",
            )
            label.grid(row=row_index * 2, column=0, padx=12, pady=(12, 6), sticky="w")

            if field.kind == "option":
                widget = ttk.Combobox(
                    parent,
                    values=self.template_names,
                    font=self._ui_font(size=13),
                    textvariable=self.template_var,
                    state="readonly",
                )
                widget.bind("<<ComboboxSelected>>", self._on_template_change)
            else:
                widget = self._create_text_input(parent, field.height)
                if field.default:
                    widget.insert("1.0", field.default)

            widget.grid(row=row_index * 2 + 1, column=0, padx=12, pady=(0, 4), sticky="ew")
            self.input_widgets[field.key] = widget

        button_frame = ttk.Frame(parent, style="Panel.TFrame")
        button_frame.grid(
            row=len(self.active_template.fields) * 2,
            column=0,
            padx=12,
            pady=(16, 12),
            sticky="ew",
        )
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)

        generate_button = ttk.Button(
            button_frame,
            text="プロンプト生成",
            command=self.generate_prompt,
        )
        generate_button.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        copy_button = ttk.Button(
            button_frame,
            text="コピー",
            command=self.copy_prompt,
        )
        copy_button.grid(row=0, column=1, padx=8, sticky="ew")

        clear_button = ttk.Button(
            button_frame,
            text="クリア",
            command=self.clear_all,
        )
        clear_button.grid(row=0, column=2, padx=(8, 0), sticky="ew")

    # 生成結果表示欄と、操作結果を伝えるステータス表示を構築する。
    def _build_output_area(self, parent: ttk.Frame) -> None:
        output_label = ttk.Label(
            parent,
            text="生成結果",
            font=self._ui_font(size=16, weight="bold"),
            style="Field.TLabel",
        )
        output_label.grid(row=0, column=0, pady=(0, 8), sticky="w")

        self.output_box = self._create_text_input(parent, 420)
        self.output_box.grid(row=1, column=0, pady=(0, 8), sticky="nsew")
        self.output_box.insert("1.0", self._default_output_preview())

        status_label = ttk.Label(
            parent,
            textvariable=self.status_var,
            font=self._ui_font(size=12),
            style="Status.TLabel",
        )
        status_label.grid(row=2, column=0, sticky="ew")

    # 出力欄が空のときに表示する案内文を返す。
    def _default_output_preview(self) -> str:
        return "ここに生成されたプロンプトが表示されます。"

    # 作業種別の切り替え時に現在値を同期し、状態表示を更新する。
    def _on_template_change(self, _: tk.Event) -> None:
        work_type_widget = self.input_widgets.get("work_type")
        if isinstance(work_type_widget, ttk.Combobox):
            self.template_var.set(work_type_widget.get())
        self.status_var.set(f"作業種別: {self.template_var.get()}")

    # 指定された入力欄から現在の値を取り出し、生成処理に渡せる文字列へ統一する。
    def _get_widget_value(self, key: str) -> str:
        widget = self.input_widgets[key]
        if isinstance(widget, ttk.Combobox):
            return widget.get()
        return widget.get("1.0", "end").strip()

    # 指定された入力欄へ値を設定し、クリアや初期化の共通処理として利用する。
    def _set_widget_value(self, key: str, value: str) -> None:
        widget = self.input_widgets[key]
        if isinstance(widget, ttk.Combobox):
            self.template_var.set(value)
            widget.set(value)
            return
        widget.delete("1.0", "end")
        if value:
            widget.insert("1.0", value)

    # テンプレートが必要とする全入力値を辞書化し、レンダリング処理へ引き渡す。
    def collect_input_values(self) -> dict[str, str]:
        values: dict[str, str] = {}
        for field in self.active_template.fields:
            values[field.key] = self._get_widget_value(field.key)
        return values

    # 現在の入力内容からプロンプト本文を生成し、右側の出力欄へ反映する。
    def generate_prompt(self) -> None:
        prompt = self.active_template.render(self.collect_input_values())
        if self.output_box is None:
            return

        self.output_box.delete("1.0", "end")
        self.output_box.insert("1.0", prompt)
        self.status_var.set("プロンプトを生成しました。")

    # 生成済みプロンプトをクリップボードへコピーし、未生成時は警告で案内する。
    def copy_prompt(self) -> None:
        if self.output_box is None:
            return

        prompt = self.output_box.get("1.0", "end").strip()
        if not prompt or prompt == self._default_output_preview():
            messagebox.showwarning("コピー不可", "先にプロンプトを生成してください。")
            return

        self.clipboard_clear()
        self.clipboard_append(prompt)
        self.status_var.set("生成結果をクリップボードにコピーしました。")

    # 入力欄と出力欄を初期状態へ戻し、次の相談内容をそのまま入力できる状態にする。
    def clear_all(self) -> None:
        for field in self.active_template.fields:
            self._set_widget_value(field.key, field.default)

        if self.output_box is not None:
            self.output_box.delete("1.0", "end")
            self.output_box.insert("1.0", self._default_output_preview())

        self.status_var.set("入力欄と出力欄をクリアしました。")


# GUI アプリケーションを起動し、イベントループへ制御を渡す。
def main() -> None:
    app = PromptGeneratorApp()
    app.mainloop()
