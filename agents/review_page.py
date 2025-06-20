import re
import json
from typing import Dict, List
from config import Config
from logger import Logger
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from agents.prompts import LAYOUT_REVIEW_PROMPT, DEVELOP_PAGE_REVIEW_PROMPT

logger = Logger(log_file=Config.LOG_FILE)

class ReviewResult(BaseModel):
    score: int
    feedback: str
    passed: bool

# 共通JSONパースユーティリティ
def robust_json_parser(content: str, required_fields: list = None, specific_patterns: list = None, extract_multiple: bool = False):
    """
    堅牢なJSONパース共通関数
    """
    json_candidates = []
    
    # 戦略1: コードブロック内のJSONを抽出（```json または ``` のパターン）
    code_blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)```", content)
    for block in code_blocks:
        block = block.strip()
        if block.startswith('{') and block.endswith('}'):
            json_candidates.append(block)
        else:
            # コードブロック内で{}パターンを探す
            json_matches = re.findall(r'\{[\s\S]*?\}', block)
            json_candidates.extend(json_matches)
    
    # 戦略2: 生のレスポンステキストから{}パターンを抽出
    raw_matches = re.findall(r'\{[\s\S]*?\}', content)
    json_candidates.extend(raw_matches)
    
    # 戦略3: より厳密な複雑JSONパターンマッチング（長いfeedbackフィールド対応）
    complex_json_pattern = r'\{\s*"score"\s*:\s*\d+\s*,\s*"feedback"\s*:\s*".*?"\s*,\s*"passed"\s*:\s*(?:true|false)\s*\}'
    complex_matches = re.findall(complex_json_pattern, content, re.DOTALL)
    json_candidates.extend(complex_matches)
    
    # 戦略4: 特化パターンマッチング
    if specific_patterns:
        for pattern in specific_patterns:
            pattern_matches = re.findall(pattern, content, re.DOTALL)
            json_candidates.extend(pattern_matches)
    
    # パース結果格納
    parsed_objects = []
    
    # 各候補を試してパース
    for candidate in json_candidates:
        candidate = candidate.strip()
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                # 必須フィールドチェック
                if required_fields:
                    if all(field in parsed for field in required_fields):
                        if extract_multiple:
                            parsed_objects.append(parsed)
                        else:
                            return parsed
                else:
                    if extract_multiple:
                        parsed_objects.append(parsed)
                    else:
                        return parsed
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"[robust_json_parser] JSON parse failed: {e}, candidate length: {len(candidate)}")
            continue
    
    # 結果を返す
    if extract_multiple:
        return parsed_objects
    elif parsed_objects:
        return parsed_objects[0]
    else:
        return None

# review_index_page関数は廃止されました。homeページもreview_develop_pageで統一処理します。

def review_layout_files(layout_code: str, globals_css_code: str, prompt_context: dict) -> dict:
    """
    layout.tsx + globals.css 専用レビュー関数
    - layout構造の正確性をチェック
    - globals.cssのTailwindCSS準拠性を重視
    - 共有ヘッダー/フッターの実装確認
    """
    
    # プロンプトテンプレートに動的な値を埋め込み
    review_prompt = LAYOUT_REVIEW_PROMPT.format(
        overall_design=prompt_context.get('overall_design', ''),
        sitemap=prompt_context.get('sitemap', []),
        required_navigation_targets=[p.get('slug', p.get('name', '')) for p in prompt_context.get('sitemap', [])],
        layout_code=layout_code,
        globals_css_code=globals_css_code
    )
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2, 
        google_api_key=Config.GOOGLE_API_KEY,
        timeout=180 
    )

    # 最大3回リトライ
    for attempt in range(3):
        try:
            response = llm.invoke(review_prompt)
            
            patterns = [r'\{\s*"score"\s*:\s*\d+\s*,[\s\S]*?"passed"\s*:\s*(?:true|false)\s*\}']
            parsed_json = robust_json_parser(response.content, required_fields=['score', 'feedback', 'passed'], specific_patterns=patterns)
            
            if parsed_json:
                review_result = ReviewResult(**parsed_json).dict()
                # スコアとpassedの整合性を自動補正
                if review_result['score'] >= 80 and not review_result['passed']:
                    review_result['passed'] = True
                elif review_result['score'] < 80 and review_result['passed']:
                    review_result['passed'] = False
                return review_result
        except Exception as e:
            logger.debug(f"[review_layout_files] Attempt {attempt + 1} failed: {e}")
            if attempt == 2:  # 最後の試行
                break
    
    return {"score": 0, "feedback": "layout files レビュー実行に失敗しました", "passed": False}

def review_develop_page(page_code: str, module_css_code: str, prompt_context: dict) -> dict:
    """
    個別ページ (app/[slug]/page.tsx + module.css) 専用レビュー関数
    - ページ固有コンテンツの実装をチェック  
    - module.cssの正確性を重視
    - 共有ヘッダーとの重複チェック
    """
    
    # プロンプトテンプレートに動的な値を埋め込み
    review_prompt = DEVELOP_PAGE_REVIEW_PROMPT.format(
        overall_design=prompt_context.get('overall_design', ''),
        page_spec=prompt_context.get('page_spec', {}),
        sitemap=prompt_context.get('sitemap', []),
        globals_css=prompt_context.get('globals_css', ''),
        slug=prompt_context.get('page_spec', {}).get('slug', ''),
        is_home_page=prompt_context.get('is_home_page', False),
        page_code=page_code,
        module_css_code=module_css_code
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2, 
        google_api_key=Config.GOOGLE_API_KEY,
        timeout=180 
    )
    
    # 最大3回リトライ
    for attempt in range(3):
        try:
            response = llm.invoke(review_prompt)
            
            patterns = [r'\{\s*"score"\s*:\s*\d+\s*,[\s\S]*?"passed"\s*:\s*(?:true|false)\s*\}']
            parsed_json = robust_json_parser(response.content, required_fields=['score', 'feedback', 'passed'], specific_patterns=patterns)
            
            if parsed_json:
                review_result = ReviewResult(**parsed_json).dict()
                # スコアとpassedの整合性を自動補正
                if review_result['score'] >= 80 and not review_result['passed']:
                    review_result['passed'] = True
                elif review_result['score'] < 80 and review_result['passed']:
                    review_result['passed'] = False
                return review_result
        except Exception as e:
            logger.debug(f"[review_develop_page] Attempt {attempt + 1} failed: {e}")
            if attempt == 2:  # 最後の試行
                break
    
    return {"score": 0, "feedback": "develop page レビュー実行に失敗しました", "passed": False} 