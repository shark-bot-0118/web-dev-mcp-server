from typing import Dict, List
from config import Config
from logger import Logger
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import re, json
from agents.review_page import review_layout_files, review_develop_page
from agents.prompts import LAYOUT_PROMPT, DEVELOP_PAGE_PROMPT, DEVELOP_PAGE_REVISION_PROMPT, LAYOUT_REVISION_PROMPT
import time
import random
from google.api_core.exceptions import ResourceExhausted, TooManyRequests

logger = Logger(log_file=Config.LOG_FILE)

class FileContent(BaseModel):
    name: str
    dir: str
    file_type: str
    code: str
    meta: Dict
    required_libs: list = []

class ReviewResult(BaseModel):
    score: int
    feedback: str
    passed: bool

# 共通JSONパースユーティリティ
def robust_json_parser(content: str, required_fields: list = None, specific_patterns: list = None, extract_multiple: bool = False):
    """
    堅牢なJSONパース共通関数
    
    Args:
        content: パースするテキストコンテンツ
        required_fields: 必須フィールドリスト（例: ['score', 'feedback', 'passed']）
        specific_patterns: 特化パターンリスト
        extract_multiple: 複数のJSONオブジェクト抽出フラグ
        
    Returns:
        dict or list: パースされたJSONオブジェクト（extract_multiple=Trueの場合はリスト）
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
    # マルチラインのfeedbackを含むJSONを正確に抽出
    complex_json_pattern = r'\{\s*"score"\s*:\s*\d+\s*,\s*"feedback"\s*:\s*".*?"\s*,\s*"passed"\s*:\s*(?:true|false)\s*\}'
    complex_matches = re.findall(complex_json_pattern, content, re.DOTALL)
    json_candidates.extend(complex_matches)
    
    # 戦略4: より柔軟なバランス括弧マッチング（ネストした構造に対応）
    def extract_balanced_json(text, start_pos=0):
        """括弧バランスを考慮した正確なJSON抽出"""
        candidates = []
        i = start_pos
        while i < len(text):
            if text[i] == '{':
                bracket_count = 1
                start = i
                i += 1
                in_string = False
                escape_next = False
                
                while i < len(text) and bracket_count > 0:
                    char = text[i]
                    
                    if escape_next:
                        escape_next = False
                    elif char == '\\':
                        escape_next = True
                    elif char == '"' and not escape_next:
                        in_string = not in_string
                    elif not in_string:
                        if char == '{':
                            bracket_count += 1
                        elif char == '}':
                            bracket_count -= 1
                    
                    i += 1
                
                if bracket_count == 0:
                    candidates.append(text[start:i])
            else:
                i += 1
        return candidates
    
    balanced_candidates = extract_balanced_json(content)
    json_candidates.extend(balanced_candidates)
    
    # 戦略5: 特化パターンマッチング
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
            continue
    
    # 結果を返す
    if extract_multiple:
        return parsed_objects
    elif parsed_objects:
        return parsed_objects[0]
    else:
        return None


# layout.tsxの内容をキャッシュするクラス
class LayoutCache:
    _layout_code = None
    @classmethod
    def set(cls, code: str):
        cls._layout_code = code
    @classmethod
    def get(cls):
        return cls._layout_code


def generate_layout(overall_design: str, sitemap: list = None, project_name: str = "nextjs_site") -> Dict:
    """
    サイト全体のデザイン方針とサイトマップを受けて、app/layout.tsxとapp/globals.cssを同時生成し、キャッシュ＆物理ファイル作成。
    Returns: dict (layout, globals_css, review)
    """
    if sitemap is None:
        sitemap = []
    review_feedback = ""
    # 1回だけ生成
    if not review_feedback:
        prompt = LAYOUT_PROMPT.format(
            overall_design=overall_design,
            sitemap=sitemap
        )
    else:
        prompt = LAYOUT_REVISION_PROMPT.format(
            review_feedback=review_feedback,
            overall_design=overall_design,
            sitemap=sitemap
        )
    logger.info(f"[PageDev] Generating layout")
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro", 
        temperature=0.2, 
        google_api_key=Config.GOOGLE_API_KEY,
        timeout=180  # 3分タイムアウト
    )
    response = llm.invoke(prompt)
    
    # JSON抽出の改善
    patterns = [
        r'\{\s*"name"\s*:\s*"layout\\.tsx"[\s\S]*?"file_type"\s*:\s*"layout"[\s\S]*?\}',
        r'\{\s*"name"\s*:\s*"globals\\.css"[\s\S]*?"file_type"\s*:\s*"css"[\s\S]*?\}'
    ]
    parsed_objects = robust_json_parser(response.content, required_fields=['name', 'file_type', 'code'], specific_patterns=patterns, extract_multiple=True)
    layout_obj, css_obj = None, None
    for obj in parsed_objects:
        if obj.get('file_type') == 'layout' and obj.get('name') == 'layout.tsx':
            layout_obj = obj
        elif obj.get('file_type') == 'css' and obj.get('name') == 'globals.css':
            css_obj = obj
    # フォールバック: レガシー方式（共通化関数でカバーできない場合）
    if not layout_obj or not css_obj:
        logger.debug(f"[generate_layout] Primary parsing failed, trying fallback")
        matches = re.findall(r'\{.*?\}(?=\s*\{|$)', response.content, re.DOTALL)
        for i, match in enumerate(matches):
            try:
                obj = json.loads(match)
                if obj.get('file_type') == 'layout' and layout_obj is None:
                    layout_obj = obj
                elif obj.get('file_type') == 'css' and obj.get('name') == 'globals.css' and css_obj is None:
                    css_obj = obj
            except Exception as e:
                logger.debug(f"[generate_layout] JSON parse failed: {e}")
    if layout_obj and css_obj:
        logger.info("[generate_layout] Layout generation completed")
        return {"layout": layout_obj, "globals_css": css_obj}
    else:
        logger.error(f"[generate_layout] Failed to extract layout objects")
        return {"layout": layout_obj, "globals_css": css_obj, "error": "layout or css generation failed"}


def extract_json_objects(text):
    """JSONを様々なパターンから抽出する堅牢な関数（develop_page用）"""
    patterns = [
        r'\{\s*"name"\s*:\s*"page\.tsx"[\s\S]*?"file_type"\s*:\s*"page"[\s\S]*?\}',
        r'\{\s*"name"\s*:\s*"[^"]*\.module\.css"[\s\S]*?"file_type"\s*:\s*"css"[\s\S]*?\}'
    ]
    
    # 共通パーサーを使用
    json_objs = robust_json_parser(text, required_fields=['name', 'file_type'], specific_patterns=patterns, extract_multiple=True)
    
    # フォールバック: レガシー方式（raw_decode）
    if not json_objs:
        idx = 0
        while idx < len(text):
            try:
                obj, end = json.JSONDecoder().raw_decode(text[idx:])
                if isinstance(obj, dict):
                    json_objs.append(obj)
                idx += end
            except Exception:
                idx += 1
    
    return json_objs

def develop_page(overall_design: str, page_spec: dict, sitemap: list, globals_css: str = "", project_name: str = "nextjs_site") -> Dict:
    """
    サイト全体デザイン・ページ仕様・サイトマップ・グローバルCSSを受けて、page.tsxとmodule.cssを生成する。
    homeページの場合はルートディレクトリ（app/page.tsx）に配置し、他のページは app/[slug]/page.tsx に配置する。
    Returns: dict (page, module_css, review, is_home_page)
    """
    page_name = page_spec.get("name", "")
    slug = page_spec.get("slug", "")
    path = page_spec.get("path", "")
    nav = page_spec.get("nav", [])
    contents = page_spec.get("contents", [])
    review_feedback = page_spec.get("review_feedback", "")

    # homeページ判定ロジック
    is_home_page = (page_name.lower() in ['home', 'index', 'top'] or 
                   slug.lower() in ['', 'home', 'index'] or 
                   path == '/')

    logger.info(f"[develop_page] Generating page '{page_name}'")
    layout_code = LayoutCache.get() or ""

    if not review_feedback:
        prompt = DEVELOP_PAGE_PROMPT.format(
            overall_design=overall_design,
            layout_code=layout_code,
            globals_css=globals_css,
            page_name=page_name,
            slug=slug,
            path=path,
            nav=nav,
            contents=contents,
            sitemap=sitemap,
            is_home_page=is_home_page
        )
    else:
        prompt = DEVELOP_PAGE_REVISION_PROMPT.format(
            review_feedback=review_feedback,
            overall_design=overall_design,
            layout_code=layout_code,
            globals_css=globals_css,
            page_spec=page_spec,
            slug=slug,
            sitemap=sitemap,
            is_home_page=is_home_page
        )

    # 1回だけAPIコール
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro", 
            temperature=0.2, 
            google_api_key=Config.GOOGLE_API_KEY,
            timeout=180  # 3分タイムアウト
        )
        response = llm.invoke(prompt)
    except (ResourceExhausted, TooManyRequests) as e:
        logger.warning(f"[develop_page] Rate limit hit for {page_name}: {e}")
        return {"error": f"Gemini API rate limit exceeded: {str(e)}", "page": None, "module_css": None, "is_home_page": is_home_page}
    except Exception as e:
        logger.warning(f"[develop_page] API call failed for {page_name}: {e}")
        return {"error": f"Gemini API call failed: {str(e)}", "page": None, "module_css": None, "is_home_page": is_home_page}
    
    try:
        # JSON抽出・パース
        json_objs = extract_json_objects(response.content)
        page_obj, css_obj = None, None
        
        # homeページの場合とそれ以外でCSSファイル名を調整
        expected_css_name = "home.module.css" if is_home_page else f'{slug}.module.css'
        
        for obj in json_objs:
            if isinstance(obj, dict) and obj.get('file_type') == 'page' and page_obj is None:
                page_obj = obj
            elif isinstance(obj, dict) and obj.get('file_type') == 'css' and obj.get('name') == expected_css_name and css_obj is None:
                css_obj = obj
            if page_obj and css_obj:
                break
                
        if page_obj and css_obj:
            # レビュー実行
            review_result = review_develop_page(
                page_obj['code'], 
                css_obj['code'], 
                {
                    'overall_design': overall_design,
                    'page_spec': page_spec,
                    'sitemap': sitemap,
                    'is_home_page': is_home_page
                }
            )
            logger.info(f"[develop_page] Page '{page_name}' completed (score: {review_result.get('score', 0)})")
            
            return {
                "page": page_obj, 
                "module_css": css_obj, 
                "review": review_result,
                "is_home_page": is_home_page
            }
            
        logger.error(f"[develop_page] JSON parsing failed for {page_name}")
        return {
            "error": "Failed to generate both page.tsx and module.css", 
            "page": page_obj, 
            "module_css": css_obj, 
            "raw_response": response.content,
            "is_home_page": is_home_page
        }
    except Exception as e:
        logger.error(f"[develop_page] JSON parsing exception for {page_name}: {e}")
        return {
            "error": f"JSON抽出・パースで例外発生: {e}", 
            "page": None, 
            "module_css": None, 
            "raw_response": getattr(response, 'content', ''),
            "is_home_page": is_home_page
        }

# 複数ページをまとめて生成する関数
def generate_pages(pages: List[Dict], overall_design: str) -> List[Dict]:
    """
    layout.tsxを参照しつつ、各ページをまとめて生成する。
    Returns: 各ページの生成結果リスト
    """
    results = []
    for page in pages:
        result = develop_page(overall_design, page, [], "")
        results.append(result)
    return results

def generate_tailwind_css(project_name: str = "nextjs_site"):
    """
    app/styles/tailwind.css を生成するユーティリティ
    """
    css_code = """
@tailwind base;
@tailwind components;
@tailwind utilities;
@import './globals.css';
"""
    # プロジェクトルートからの絶対パスを構築
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir_path = os.path.join(project_root, Config.OUTPUT_DIR)
    out_dir = os.path.join(output_dir_path, project_name, "app", "styles")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "tailwind.css"), "w", encoding="utf-8") as f:
        f.write(css_code)
 
