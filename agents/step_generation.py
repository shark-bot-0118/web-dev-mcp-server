import os
import json
import subprocess
import time
import random
from dotenv import load_dotenv
from config import Config
from logger import Logger
from typing import List, Dict
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from agents.page_development import generate_layout, generate_tailwind_css, develop_page, LayoutCache
from agents.review_page import review_develop_page, review_layout_files

load_dotenv()
logger = Logger(log_file=Config.LOG_FILE)

def write_file(file_path: str, content: str) -> None:
    """
    ファイルにコンテンツを書き込む関数
    
    Args:
        file_path (str): 書き込み先のファイルパス
        content (str): 書き込むコンテンツ
    """
    try:
        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # ファイルに書き込み
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"[write_file] Successfully wrote file: {file_path}")
        
    except Exception as e:
        logger.error(f"[write_file] Failed to write file {file_path}: {str(e)}")
        raise e

class QualityControlException(Exception):
    """品質制御で致命的な問題が発生した場合の例外"""
    def __init__(self, message: str, component: str = None, attempts: int = None):
        super().__init__(message)
        self.component = component
        self.attempts = attempts

class CriticalWorkflowError(Exception):
    """ワークフロー全体を停止すべき致命的エラー"""
    def __init__(self, message: str, failed_component: str = None):
        super().__init__(message)
        self.failed_component = failed_component

class Step(BaseModel):
    page: str
    template: str
    content: Dict

class StepsOutput(BaseModel):
    steps: List[Step]

class SetupAgent:
    def setup_project(self, output_dir: str, project_name: str) -> Dict:
        """
        Next.jsプロジェクトのセットアップを/static_site_output上で行う。
        Args:
            output_dir: 出力ディレクトリ
            project_name: プロジェクト名
        Returns:
            dict: セットアップstep情報
        """
        # Next.jsプロジェクト初期化
        project_path = os.path.join(output_dir, project_name)
        os.makedirs(output_dir, exist_ok=True)
        # 既に存在する場合はスキップ
        if not os.path.exists(project_path):
            try:
                cmd = [
                    "npx", "create-next-app@latest", project_name,
                    "--use-npm", "--no-git", "--typescript", "--eslint", "--src-dir", "--app"
                ]
                logger.info(f"[SetupAgent] Running: {' '.join(cmd)} in {output_dir}")
                result = subprocess.run(cmd, cwd=output_dir, capture_output=True, text=True, check=True)
                description = f"Next.js project initialized at {project_path}\nstdout: {result.stdout}\nstderr: {result.stderr}"
            except Exception as e:
                description = f"Failed to initialize Next.js project: {e}"
                logger.debug(description)
        else:
            description = f"Next.js project already exists at {project_path}"
        return {
            "step_type": "setup",
            "output_dir": output_dir,
            "project_path": project_path,
            "description": description
        }

class StepGenerationAgent:
    def generate_steps(self, requirements: dict, project_name: str):
        # instruction_analysis.pyの出力を受け取る
        overall_design = requirements.get("overall_design", "")
        pages = requirements.get("pages", [])
        sitemap = requirements.get("siteMap", [])
        logger.info(f"[StepGeneration] Starting generation for {len(pages)} pages")

        steps = []
        all_required_libs = set()
        globals_css_content = ""
        
        # 2. Layout品質重視フロー  
        def generate_layout_with_quality_control():
            """Layout品質重視フロー：生成 -> レビュー -> リトライ（最大3回）"""
            max_attempts = Config.MAX_ATTEMPTS
            for attempt in range(max_attempts):
                try:
                    if attempt > 0:
                        logger.info(f"[StepGeneration] Layout retry {attempt + 1}/{max_attempts}")
                    
                    # Layout生成
                    layout_result = generate_layout(overall_design, sitemap, project_name)
                    
                    if not isinstance(layout_result, dict) or not layout_result.get('layout') or not layout_result.get('globals_css'):
                        if attempt == max_attempts - 1:
                            raise QualityControlException(
                                f"Layout generation failed after {max_attempts} attempts", 
                                component="layout", 
                                attempts=max_attempts
                            )
                        continue
                    
                    # レビュー実行
                    review_result = review_layout_files(
                        layout_result['layout']['code'],
                        layout_result['globals_css']['code'],
                        {
                            'overall_design': overall_design,
                            'sitemap': sitemap
                        }
                    )
                    
                    review_score = review_result.get('score', 0)
                    
                    if review_score >= 80:
                        # 品質基準クリア
                        logger.info(f"[StepGeneration] Layout approved (score: {review_score})")
                        
                        # ファイル書き込み処理を実行
                        if layout_result.get('layout') and layout_result.get('globals_css'):
                            try:
                                # プロジェクトルートからの絶対パスを構築
                                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                                output_dir_path = os.path.join(project_root, Config.OUTPUT_DIR)
                                project_path = os.path.join(output_dir_path, project_name, "app")
                                layout_path = os.path.join(project_path, "layout.tsx")
                                css_path = os.path.join(project_path, "globals.css")
                                
                                # layout.tsx書き込み
                                write_file(layout_path, layout_result['layout']['code'])
                                
                                # LayoutCacheにセット
                                LayoutCache.set(layout_result['layout']['code'])
                                
                                # globals.css書き込み（既存ファイルがあれば削除）
                                if os.path.exists(css_path):
                                    os.remove(css_path)
                                write_file(css_path, layout_result['globals_css']['code'])
                                
                            except Exception as write_error:
                                logger.error(f"[StepGeneration] Layout file write error: {write_error}")
                        else:
                            logger.error(f"[StepGeneration] Cannot write layout files - missing data")
                        
                        layout_result['review'] = review_result
                        # globals.css内容を後続処理用に保存
                        nonlocal globals_css_content
                        globals_css_content = layout_result['globals_css']['code']
                        return layout_result
                    else:
                        # 品質基準未達
                        if attempt == max_attempts - 1:
                            raise QualityControlException(
                                f"Layout quality check failed after {max_attempts} attempts (final score: {review_score})", 
                                component="layout", 
                                attempts=max_attempts
                            )
                        continue
                        
                except QualityControlException:
                    # QualityControlExceptionは再発生
                    raise
                except Exception as e:
                    logger.error(f"[StepGeneration] Layout generation exception: {e}")
                    if attempt == max_attempts - 1:
                        raise QualityControlException(
                            f"Layout generation exception after {max_attempts} attempts: {str(e)}", 
                            component="layout", 
                            attempts=max_attempts
                        )
                    continue
            
            raise QualityControlException(
                f"Layout generation unexpected termination after {max_attempts} attempts", 
                component="layout", 
                attempts=max_attempts
            )

        # 3. 各ページ品質重視フロー（既存）
        def develop_page_with_quality_control(overall_design, page, sitemap, globals_css_content, project_name):
            """品質重視フロー：develop_page -> review -> retry(最大3回) -> 品質確保後にファイル書き込み"""
            max_attempts = Config.MAX_ATTEMPTS
            page_name = page.get('name', 'unknown')
            slug = page.get('slug', '')
            
            for attempt in range(max_attempts):
                try:
                    if attempt > 0:
                        logger.info(f"[StepGeneration] Page '{page_name}' retry {attempt + 1}/{max_attempts}")
                    
                    # develop_page実行
                    page_result = develop_page(overall_design, page, sitemap, globals_css_content, project_name)
                    
                    if not isinstance(page_result, dict) or not page_result.get("page") or not page_result.get("module_css"):
                        if attempt == max_attempts - 1:  # 最後の試行
                            raise QualityControlException(
                                f"develop_page failed for {page_name} after {max_attempts} attempts", 
                                component=f"page_{page_name}", 
                                attempts=max_attempts
                            )
                        continue

                    # レビュー実行
                    review_result = review_develop_page(
                        page_result["page"]["code"],
                        page_result["module_css"]["code"],
                        {
                            'overall_design': overall_design,
                            'page_spec': page,
                            'sitemap': sitemap,
                            'globals_css': globals_css_content,
                            'is_home_page': page_result.get('is_home_page', False)  # 🚨 CRITICAL FIX: is_home_page情報を正しく渡す
                        }
                    )
                
                    # review_resultが辞書でない場合の対応
                    if not isinstance(review_result, dict):
                        logger.error(f"[StepGeneration] Invalid review_result type for {page_name}")
                        # デフォルト値で対応
                        review_result = {"score": 0, "feedback": f"Review failed - invalid result type: {review_result}", "passed": False}
                    
                    review_score = review_result.get('score', 0)
                    
                    # スコア判定
                    if review_score >= 80:
                        # 品質基準クリア - ファイル書き込みが必要かチェック
                        logger.info(f"[StepGeneration] Page '{page_name}' approved (score: {review_score})")
                        
                        # develop_page内でファイル書き込みが失敗した可能性があるため、ここで確実に書き込む
                        if page_result.get("page") and page_result.get("module_css"):
                            try:
                                # プロジェクトルートからの絶対パスを構築
                                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                                output_dir_path = os.path.join(project_root, Config.OUTPUT_DIR)
                                project_path = os.path.join(output_dir_path, project_name, "app")
                                is_home_page = page_result.get('is_home_page', False)
                                
                                if is_home_page:
                                    # homeページはルートに配置
                                    page_path = os.path.join(project_path, "page.tsx")
                                    css_path = os.path.join(project_path, "home.module.css")
                                else:
                                    # 他のページは slug ディレクトリに配置
                                    slug = page.get('slug', '')
                                    page_dir = os.path.join(project_path, slug)
                                    page_path = os.path.join(page_dir, "page.tsx")
                                    css_path = os.path.join(page_dir, f"{slug}.module.css")
                                
                                # ファイル書き込み実行
                                write_file(page_path, page_result["page"]["code"])
                                write_file(css_path, page_result["module_css"]["code"])
                                
                            except Exception as write_error:
                                logger.error(f"[StepGeneration] File write error for {page_name}: {write_error}")
                        else:
                            logger.error(f"[StepGeneration] Cannot write files for {page_name} - missing data")
                        
                        return page_result
                    else:
                        # 品質基準未達 -> リトライまたはエラー
                        if attempt == max_attempts - 1:  # 最後の試行
                            logger.error(f"[StepGeneration] Quality check failed after {max_attempts} attempts for {page_name}")
                            raise QualityControlException(
                                f"Quality check failed for {page_name} after {max_attempts} attempts (final score: {review_score})",
                                component=f"page_{page_name}",
                                attempts=max_attempts
                            )
                        else:
                            # リトライのためにレビューフィードバックをpage_specに追加
                            page["review_feedback"] = review_result.get('feedback', 'Quality standards not met. Please improve the code.')
                            continue
                    
                except QualityControlException:
                    # QualityControlExceptionは再発生
                    raise
                except Exception as e:
                    logger.error(f"[StepGeneration] Exception for {page_name}: {e}")
                    if attempt == max_attempts - 1:  # 最後の試行
                        raise QualityControlException(
                            f"Exception occurred for {page_name} after {max_attempts} attempts: {str(e)}",
                            component=f"page_{page_name}",
                            attempts=max_attempts
                        )
                    continue
            
            # ここには到達しないはずだが、安全のため
            raise QualityControlException(
                f"Unexpected termination for {page_name} after {max_attempts} attempts",
                component=f"page_{page_name}",
                attempts=max_attempts
            )

        try:
            # 段階的品質重視フロー実行
            logger.info("[StepGeneration] Starting generation")
            
            # 1. Layout品質重視フロー実行
            layout_result = generate_layout_with_quality_control()
            steps.append(layout_result)
            
            # 2. TailwindCSS生成（品質チェック不要）
            tailwind_result = generate_tailwind_css(project_name)
            steps.append(tailwind_result)
            
            # 3. 各ページ（homeページ含む）品質重視フローを並列実行（1つ失敗で即座に停止）
            logger.info(f"[StepGeneration] Processing {len(pages)} pages")
            
            # レート制限回避のため、並列度を制限
            max_workers = min(Config.MAX_CONCURRENCY, len(pages))  # 最大3並列でGemini APIを叩く
            
            # 並列処理で一つでも失敗したら即座に停止する戦略
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {}  # future -> page_name のマッピング
                
                # すべてのページをサブミット
                for i, page in enumerate(pages):
                    # ページ間でAPI呼び出しを少し分散（レート制限回避）
                    if i > 0:
                        time.sleep(random.uniform(0.5, 1.0))
                    
                    future = executor.submit(develop_page_with_quality_control, overall_design, page, sitemap, globals_css_content, project_name)
                    futures[future] = page.get('name', 'unknown')
                
                # as_completedを使って完了順に処理し、エラーが発生したら即座に停止
                completed_pages = []
                for future in as_completed(futures):
                    page_name = futures[future]
                    try:
                        page_result = future.result()
                        steps.append(page_result)
                        if isinstance(page_result, dict) and "required_libs" in page_result and page_result["required_libs"]:
                            all_required_libs.update(page_result["required_libs"])
                        completed_pages.append(page_name)
                        
                    except QualityControlException as qce:
                        # ページ生成で品質制御に失敗した場合 - 即座にワークフロー停止
                        logger.error(f"[StepGeneration] Page '{page_name}' failed quality control")
                        
                        # 残りのタスクをキャンセル
                        for remaining_future in futures:
                            if remaining_future != future and not remaining_future.done():
                                remaining_future.cancel()
                        
                        # 即座にCriticalWorkflowErrorを発生
                        raise CriticalWorkflowError(
                            f"Page generation failed: {page_name} failed quality control after {Config.MAX_ATTEMPTS} attempts. Error: {str(qce)}", 
                            failed_component=f"page_{page_name}"
                        )
                        
                    except Exception as e:
                        # その他の予期しないエラー - 即座にワークフロー停止
                        logger.error(f"[StepGeneration] Page '{page_name}' encountered unexpected error: {str(e)}")
                        
                        # 残りのタスクをキャンセル
                        for remaining_future in futures:
                            if remaining_future != future and not remaining_future.done():
                                remaining_future.cancel()
                        
                        # 即座にCriticalWorkflowErrorを発生
                        raise CriticalWorkflowError(
                            f"Page generation unexpected error: {page_name} failed with exception: {str(e)}", 
                            failed_component=f"page_{page_name}"
                        )
                
                # 全てのページが正常完了した場合
                logger.info(f"[StepGeneration] All pages completed successfully")

        except QualityControlException as qce:
            # Index PageまたはLayoutの品質制御失敗 -> CriticalWorkflowErrorに変換
            logger.error(f"[StepGeneration] Core component generation failed")
            raise CriticalWorkflowError(
                f"Core component generation failed: {str(qce)}", 
                failed_component=qce.component
            )
        except CriticalWorkflowError as cwe:
            # CriticalWorkflowErrorは再発生してワークフロー全体を停止
            logger.error(f"[StepGeneration] Critical workflow error")
            raise
        except Exception as e:
            logger.error(f"[StepGeneration] Unexpected error: {type(e).__name__}")
            raise CriticalWorkflowError(
                f"Unexpected critical error: {str(e)}", 
                failed_component="workflow"
            )
        
        logger.info(f"[StepGeneration] Generation completed successfully")
        return steps, list(all_required_libs)

# 例外クラスをエクスポート（上位ワークフローでキャッチできるように）
__all__ = [
    'StepGenerationAgent',
    'SetupAgent',
    'QualityControlException',
    'CriticalWorkflowError',
    'Step',
    'StepsOutput'
] 
