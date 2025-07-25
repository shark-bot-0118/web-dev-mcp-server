# Web Development Agent

自然言語指示から静的Webサイトを自動生成するMCPサーバーです。Next.jsベースのWebサイトを生成し、S3への自動デプロイ&WEBサイト公開も可能です。
本MPCサーバーはCursor、Windsurf、Cline、RooをはじめとしたAIエディタからの実行を想定しています。

## 🚀 概要

このシステムは、ユーザーの自然言語による指示を受け取り、以下の処理を自動実行します：

1. **指示解析**: 自然言語指示をWebサイト構造に変換
2. **Next.jsプロジェクト生成**: 自動的にプロジェクトをセットアップ
3. **ページ開発**: 各ページのコンポーネントとスタイルを生成
4. **品質管理**: 生成されたコードの品質をレビュー
5. **自動デプロイ**: S3静的ホスティングへの自動デプロイ

**重要**: 本システムはWebページの全体構成・レイアウト・機能を自動設計・構築しますが、**実際にWebページに掲載する文言や画像等はユーザーが直接設定する必要があります**。生成されたプロジェクトを確認・修正した後、デプロイツールを使用してWebサイトを公開できます。

## ✨ 主要機能

### MCPツール
- **create_website**: 自然言語指示からWebサイトを自動生成
- **deploy_to_s3**: Next.jsプロジェクトをS3に静的サイトとしてデプロイ
- **check_s3_deployment**: S3デプロイメントの状態確認

### 自動生成される要素
- Next.jsプロジェクト構造
- レスポンシブレイアウト（layout.tsx）
- 各ページコンポーネント（page.tsx）
- CSSモジュール（*.module.css）
- グローバルスタイル（globals.css）
- Tailwind CSS設定

### 技術スタック
- **Framework**: Next.js 13+ App Directory
- **Styling**: TailwindCSS + CSS Modules
- **Server**: FastMCP (Model Context Protocol)
- **AI/ML**: Google Gemini API, LangChain
- **Cloud**: AWS S3 (静的ホスティング)
- **Architecture**: Multi-agent system

## 🏗️ アーキテクチャ

### マルチエージェントシステム
本プロジェクトは各開発フェーズに特化したエージェントを使用：

- **指示解析エージェント** (`agents/instruction_analysis.py`)
  - ユーザー要求の解析と理解
  - デザイン方針と機能要件の抽出

- **ステップ生成エージェント** (`agents/step_generation.py`)
  - 品質管理付き開発ワークフローの計画
  - 重要な失敗に対する3回リトライ制限の実装
  - ライブラリ依存関係の管理

- **ページ開発エージェント** (`agents/page_development.py`)
  - 個別ページとコンポーネントの開発
  - 適切なNext.jsパターンと規約の保証

- **レビューエージェント** (`agents/review_page.py`)
  - 多層コード検証
  - 品質基準の強制（80点以上のスコア要求）

- **実行エージェント** (`agents/execution.py`)
  - プロジェクトセットアップとサーバー管理
  - Next.js開発サーバーのライフサイクル管理

- **ビルドエージェント** (`agents/build_agent.py`)
  - Next.jsプロジェクトのビルド処理

- **S3デプロイエージェント** (`agents/s3_deploy_agent.py`)
  - AWS S3への静的サイトデプロイメント

### 品質管理システム
`agents/prompts.py`の特化プロンプトによる高度な検証：

#### インデックスページ検証 (`INDEX_REVIEW_PROMPT`)
- メタデータエクスポートの検証
- ナビゲーションリンクの確認
- TailwindCSSクラスの検証
- サーバーコンポーネントの準拠

#### レイアウト検証 (`LAYOUT_REVIEW_PROMPT`)
- Next.js 13+レイアウト構造
- 共有ヘッダー/ナビゲーション要件
- CSS @applyディレクティブの検証
- カスタムクラス定義チェック

#### 個別ページ検証 (`DEVELOP_PAGE_REVIEW_PROMPT`)
- ヘッダー継承の検証
- Module.css統合
- 外部リソース制限
- JSX構文検証

### ワークフロー
```mermaid
graph TD
    A[自然言語指示] --> B[指示解析]
    B --> C[Next.jsセットアップ]
    C --> D[ステップ生成]
    D --> E[依存関係インストール]
    E --> F[ページ開発]
    F --> G[品質チェック]
    G --> H[サーバー起動]
    H --> I[S3デプロイ]
```

## 🛠️ インストール

### 前提条件
- Node.js 18+ 
- Python 3.8+
- Google API key (Gemini)

### セットアップ
1. **リポジトリのクローン**
   ```bash
   git clone https://github.com/shark-bot-0118/web-dev-mcp-server
   cd web-dev-mcp-server
   ```

2. **Python依存関係のインストール**
   ```bash
   pip install -r requirements.txt
   ```

3. **Node.js依存関係のインストール**
   ```bash
   npm install
   ```

4. **環境設定**
   `.env`ファイルを作成：
   ```bash
   GOOGLE_API_KEY=your_google_api_key
   
   # AWS設定（S3デプロイ用）
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   AWS_DEFAULT_REGION=ap-northeast-1
   
   # オプション設定
   OUTPUT_DIR=static_site_output
   MAX_CONCURRENCY=3
   LOG_FILE=app.log
   ```

## 🚀 使用方法

### MCPサーバーとしての利用

本プロジェクトは**Model Context Protocol (MCP) サーバー**として実装されており、主にAIエディタ（Cursor、Windsurf等）やAIエージェントからツールとして呼び出されることを前提としています。

#### MCPサーバーの起動
```bash
python main.py
```

#### AIエディタでの利用

MCPサーバーを起動後、以下のツールがAIエディタから利用可能になります：

- `create_website`: 自然言語指示からWebサイトを自動生成
- `deploy_to_s3`: Next.jsプロジェクトをS3にデプロイ
- `check_s3_deployment`: S3デプロイメント状態確認

⚠️ **実行時間について**: ツール実行完了まで**10〜20分程度**かかります（生成ページ数に依存）

⚠️ **タイムアウト注意**: Claude for Desktopでは内部タイムアウトが設定されており長時間の処理でタイムアウトが発生する可能性があります。タイムアウトが発生した場合もバックグラウンドで処理は継続されます。そのほかタイムアウト時間を設定できるエディタの場合はタイムアウトを設定することでこの問題を回避できます。

### Webサイトの生成

#### AIエディタからの実行
AIエディタで以下のように指示することで、MCPツールが実行されます：

```
技術系企業のコーポレートサイトを作成してください。ホーム、企業概要、サービス、お問い合わせページが必要です。モダンなブルー系のカラースキームでプロフェッショナルなタイポグラフィを使用してください。
```

#### スタンドアロン実行（テスト用）
```python
# 例：企業サイトの指示
user_instruction = "技術系企業のコーポレートサイトを作成してください。ホーム、企業概要、サービス、お問い合わせページが必要です。モダンなブルー系のカラースキームでプロフェッショナルなタイポグラフィを使用してください。"
```

### ワークフロープロセス
1. **指示解析** - 要件とデザイン設定の理解
2. **プロジェクトセットアップ** - 適切な構造でNext.jsプロジェクトを作成
3. **ステップ生成** - 品質検証付きの開発ステップ計画
4. **ライブラリインストール** - 必要なnpmパッケージのインストール（Next.jsデフォルト除く）
5. **開発** - 継続的な品質チェック付きページ生成
6. **サーバー起動** - `http://localhost:3000`で開発サーバーを起動

### Webサイトの修正とデプロイ

#### コンテンツの修正
生成されたWebサイトは`static_site_output/nextjs_site_[random_id]/`に保存されます(デフォルト)。  
以下の作業が必要です：

1. **テキストコンテンツ**: 各ページの文言をビジネス要件に合わせて修正
2. **画像・メディア**: プレースホルダー画像を実際の画像に差し替え
3. **連絡先情報**: 実際の住所・電話番号・メールアドレスに更新
4. **ブランディング**: ロゴやカラーテーマの調整
5. **イベント実装**: ボタンクリックやフォーム送信などのユーザーイベント処理を実装（必要に応じてAPIエンドポイントも実装）
6. **商品詳細ページ**: ECサイトなど商品を掲載する場合は、商品詳細ページや関連機能を実装

#### S3デプロイ
修正完了後、AIエディタから以下のツールを実行しWebサイトを公開：

```python
# プロジェクトをS3にデプロイ
deploy_result = deploy_to_s3("nextjs_site_123456", "my-website-bucket")

# デプロイ状態確認
status = check_s3_deployment("my-website-bucket")
```

⚠️ **デプロイ制限事項**: 
- `deploy_to_s3`は簡易的に構築されており、Webサーバーの公開に特化
- 試験的・開発用途での使用を想定
- **本格運用では後述の推奨構成をご利用ください**

## 📁 プロジェクト構造

```
web_development_agent/
├── agents/                    # マルチエージェントシステム
│   ├── instruction_analysis.py  # 指示解析
│   ├── step_generation.py       # ステップ生成
│   ├── page_development.py      # ページ開発
│   ├── review_page.py           # レビュー・品質管理
│   ├── execution.py             # 実行管理
│   ├── build_agent.py           # ビルド処理
│   ├── s3_deploy_agent.py       # S3デプロイ
│   └── prompts.py               # 品質管理プロンプト
├── graph/
│   ├── workflow.py              # メインワークフロー
│   └── s3_deploy_workflow.py    # S3デプロイワークフロー
├── tools/
│   └── setup_nextjs_project.py # Next.jsプロジェクトセットアップ
├── templates/                   # HTMLテンプレート
├── static_site_output/          # 生成されたプロジェクト
├── config.py                    # 設定管理
├── logger.py                    # ロギングシステム
└── main.py                      # MCPサーバーエントリーポイント
```

### 生成される出力
```
static_site_output/
└── nextjs_site_[random_id]/
    ├── app/
    │   ├── layout.tsx           # メインレイアウト
    │   ├── globals.css          # グローバルスタイル
    │   ├── page.tsx             # ホームページ
    │   ├── home.module.css      # ホームページスタイル
    │   ├── about/
    │   │   ├── page.tsx
    │   │   └── about.module.css
    │   └── contact/
    │       ├── page.tsx
    │       └── contact.module.css
    ├── package.json
    ├── tailwind.config.ts
    └── next.config.mjs
```

## 🎯 品質基準

### CSS/TailwindCSS検証
システムが検出・防止する一般的なビルドエラー：

- **禁止カスタムクラス**: `text-primary`, `bg-light-gray`, `selection:bg-accent-teal`
- **無効な@apply使用**: @applyディレクティブでのCSS変数
- **未定義色名**: 非標準TailwindCSSカラークラス
- **構文エラー**: ビルドを破壊する不正なCSS

### スコアリングシステム
- **80点以上**: コンポーネント承認に必要
- **自動失敗**: 未定義カスタムクラス、ナビゲーションエラー、構文問題
- **3回リトライ制限**: 重要コンポーネントは最大3回の試行後ワークフロー終了

### Next.jsベストプラクティス
- **App Directory構造**: Next.js 13+パターン
- **サーバーコンポーネント**: デフォルトでサーバーサイドレンダリング
- **適切なインポート**: 正しいNext.jsモジュール使用
- **SEO最適化**: メタデータエクスポートとセマンティックHTML

## 🔧 設定

### 環境変数
| 変数 | 説明 | デフォルト |
|-----|------|-----------|
| `GOOGLE_API_KEY` | Google Gemini API キー | 必須 |
| `AWS_ACCESS_KEY_ID` | AWS アクセスキー（S3デプロイ用） | オプション |
| `AWS_SECRET_ACCESS_KEY` | AWS シークレットキー（S3デプロイ用） | オプション |
| `AWS_DEFAULT_REGION` | AWS リージョン | `ap-northeast-1` |
| `OUTPUT_DIR` | 生成プロジェクトディレクトリ | `static_site_output` |
| `MAX_CONCURRENCY` | ページ生成処理並列実行数 | `3` |
| `LOG_FILE` | ログファイル名 | `app.log` |

⚠️ **重要な制限事項**:
- MAX_CONCURRENCYの値が大きすぎるとGeminiのレート制限にかかる可能性があります
- マルチエージェント構築のため、LLM呼び出しに実行回数制限が設けられています
- そのため、場合によってはツールの実行に失敗する可能性があります
- 失敗時は再実行することを推奨します

### ロギング
設定可能レベルの包括的ロギングシステム：
- **INFO**: ワークフロー進行と主要操作
- **DEBUG**: 詳細実行情報
- **ERROR**: エラー追跡とデバッグ

## 🧪 テスト

### テストスクリプトの説明

#### test_generate.py - Webアプリケーション生成テスト
ページ生成ワークフローの実行とテストを行うスクリプトです。

**機能:**
- ユーザー指示に基づいてWebサイトを自動生成
- 各種ビジネス要件の実装例を提供
- サンプル指示文が複数用意されており、そのままテスト実行可能

**使用方法:**
```bash
python test/test_generate.py
```

**サンプル用途例:**
- 個人経営の蕎麦屋サイト
- コーヒー屋のメニュー表示サイト  
- グローバル企業のコーポレートサイト
- 個人作家のポートフォリオサイト
- 眼科病院の医療情報サイト

#### test_s3_workflow.py - S3デプロイメントテスト
生成されたWebアプリケーションをAWS S3に公開するテストスクリプトです。

**機能:**
- 事前に生成されたNext.jsプロジェクトをS3にアップロード
- 静的サイトホスティングの設定とテスト
- 対話形式でプロジェクトIDとバケット名を指定

**使用方法:**
```bash
python test/test_s3_workflow.py
```

**実行手順:**
1. `test_generate.py`でWebサイトを生成
2. 生成されたプロジェクトID（例：`next_site_xxxxxxxx`）をメモ
3. `test_s3_workflow.py`を実行
4. プロンプトに従ってプロジェクトIDとS3バケット名を入力

**注意事項:**
- 事前に`test_generate.py`でサイト生成が必要
- AWS認証情報の設定が必要（`.env`ファイル参照）
- バケット名を空欄にするとデフォルト名が自動設定される

### テスト実行例

```bash
# 1. Webサイト生成テスト
python test/test_generate.py

# 2. 生成完了後、S3デプロイテスト実行
python test/test_s3_workflow.py
# project_id: next_site_12345678
# bucket_name: my-website-bucket (または空欄でデフォルト)
```

## 🐛 トラブルシューティング

### 一般的な問題

**CSSビルドエラー**
- システムが未定義TailwindCSSクラスを自動防止
- 特定の検証失敗は`app.log`を確認
- 現在の検証ルールは`agents/prompts.py`をレビュー

**サーバー起動失敗**
- Node.jsバージョン確認（18+必須）
- ポート3000の可用性確認
- npmパッケージインストールログをレビュー

**品質管理失敗**
- 3回失敗したコンポーネントはワークフロー終了
- ログで検証スコア確認
- 品質基準に対する生成コードレビュー

**Gemini APIレート制限・実行制限**
- 指数バックオフとリトライロジック実装済み
- ログでAPI呼び出し状況確認
- マルチエージェントシステムによるLLM呼び出し回数制限あり
- 制限に達した場合は時間をおいて再実行

**MCPツール実行時のタイムアウト**
- Claude for Desktopなどでは内部タイムアウト設定あり
- ツール実行は10〜20分程度かかるため、タイムアウトが発生する可能性
- タイムアウト後もバックグラウンド処理は継続
- 完了状況は`static_site_output/`ディレクトリで確認可能

**本格運用での推奨構成**
- **CloudFront**: CDN配信とHTTPS対応
- **Route53**: 独自ドメインでの公開
- **証明書**: AWS Certificate Managerでの証明書管理
- **セキュリティ**: WAFとセキュリティヘッダー設定

**注意**: ツールを修正することで半自動的なドメイン取得からCloudFront公開が可能ですが、汎用性と試験的運用を考慮し現在は実装していません。本格運用時はツールの機能を拡張するか手動でのAWSリソース設定を推奨します。

## ステップアップ
現在のプロジェクト構成を変更し以下の修正を加えることで、品質向上や特定のタスクへの最適化が可能です

- **適切なLLMの選択**  
現在はコストパフォーマンスと実行時間の観点からGeminiのAPIを利用しています  
モデルを変更することで品質や性能を大きく変更することが可能です  
(例) claude-opus-4-20250514, o3-2025-04-16, Local LLM-Qwen等

- **システムプロンプトの調整**  
システムプロンプトを調整することで品質の向上や特定のタスクへの最適化が可能です  
実行するLLMを変更した場合はシステムプロンプトの最適化を行うことを推奨します  
※システムプロンプトはLLMが生成する作成物の品質に大きく影響を及ぼすため修正には注意してください

- **Web公開処理の修正**  
現在はWebページの公開にAWSを使用しています  
公開方式を修正することでより本番に近いデプロイフローを作成することが可能です  

## 🤝 貢献

1. **コード品質**: 既存パターンと検証ルールに従う
2. **テスト**: 様々な指示タイプと複雑さレベルでテスト
3. **ドキュメント**: 必要に応じてプロンプトと検証ルールを更新
4. **エラーハンドリング**: 品質管理システムに特定エラーパターンを追加

## 📄 ライセンス

このプロジェクトはMITライセンスです

## 🔗 関連プロジェクト

- [FastMCP](https://github.com/jlowin/fastmcp) - MCPサーバーフレームワーク
- [Next.js](https://nextjs.org/) - 本番用Reactフレームワーク
- [TailwindCSS](https://tailwindcss.com/) - ユーティリティファーストCSSフレームワーク
- [LangGraph](https://langchain-ai.github.io/langgraph/) - ワークフロー管理フレームワーク
