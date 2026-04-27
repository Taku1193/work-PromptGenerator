# AI相談プロンプト生成ツール

Windows上でローカル動作する、AI相談用プロンプト生成ツールです。
入力内容をテンプレートに流し込み、GitHub Copilot や社内AIへ貼り付けやすい文章を生成します。

## ディレクトリ構成

- `app.py`: 起動用エントリポイント
- `src/`: GUI 本体、テンプレート定義、生成処理
- `doc/`: 設計書と要件メモ
- `tests/`: テンプレートの基本テスト
- `requirements.txt`: 依存関係

## 前提

- Python 3.11 以降を推奨
- 外部API通信なし
- ローカル実行専用
- GUI 利用のため `tkinter` が使える Python 環境が必要

## セットアップ

WSL や Linux 環境では、システム Python へ直接 `pip install` できない場合があります。
その場合は仮想環境を作成してからインストールしてください。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

WSL で `python app.py` 実行時に `No module named 'tkinter'` が出る場合は、先に以下を実行してください。

```bash
sudo apt update
sudo apt install python3.12-venv python3-tk
```

## 起動

```bash
source .venv/bin/activate
python app.py
```

Windows で使う前提なら、WSL ではなく Windows 側の Python で起動する方が素直です。
WSL 上の Linux GUI として起動した場合、Windows の日本語 IME が入力欄へ渡らないことがあります。
日本語入力ができない場合は、Windows 側の PowerShell やコマンドプロンプトから `python app.py` を実行してください。

## 確認コマンド

```bash
source .venv/bin/activate
python3 -m py_compile app.py src/*.py tests/*.py
python3 -m unittest discover tests
```

## MVP機能

- 作業種別: 初期値は `バグ修正`
- 相談内容、対象、関連ソース、発生事象などの入力
- プロンプト生成
- 生成結果のコピー
- 入力欄と出力欄のクリア

## 拡張ポイント

`src/prompt_templates.py` 内の `TEMPLATES` に `PromptTemplate` を追加すると、将来的な作業種別拡張に対応できます。
