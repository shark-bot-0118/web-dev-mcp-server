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
        logger.info(f"[StepGenerationAgent] overall_design: {overall_design}")
        logger.info(f"[StepGenerationAgent] pages: {pages}")
        logger.info(f"[StepGenerationAgent] sitemap: {sitemap}")

        steps = []
        all_required_libs = set()
        globals_css_content = ""
        
        # 2. Layout品質重視フロー  
        def generate_layout_with_quality_control():
            """Layout品質重視フロー：生成 -> レビュー -> リトライ（最大3回）"""
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    logger.info(f"[generate_layout_with_quality_control] Attempt {attempt + 1}/{max_attempts} for layout")
                    
                    # Layout生成
                    layout_result = generate_layout(overall_design, sitemap, project_name)
                    
                    if not isinstance(layout_result, dict) or not layout_result.get('layout') or not layout_result.get('globals_css'):
                        logger.error(f"[generate_layout_with_quality_control] Layout generation failed attempt {attempt + 1}: {layout_result}")
                        if attempt == max_attempts - 1:
                            raise QualityControlException(
                                f"Layout generation failed after {max_attempts} attempts", 
                                component="layout", 
                                attempts=max_attempts
                            )
                        continue
                    
                    # レビュー実行
                    logger.info(f"[generate_layout_with_quality_control] Starting layout review attempt {attempt + 1}")
                    review_result = review_layout_files(
                        layout_result['layout']['code'],
                        layout_result['globals_css']['code'],
                        {
                            'overall_design': overall_design,
                            'sitemap': sitemap
                        }
                    )
                    
                    review_score = review_result.get('score', 0)
                    logger.info(f"[generate_layout_with_quality_control] Layout review score attempt {attempt + 1}: {review_score}")
                    
                    if review_score >= 80:
                        # 品質基準クリア
                        logger.info(f"[generate_layout_with_quality_control] Layout quality passed! Score: {review_score}")
                        
                        # ファイル書き込み処理を実行
                        if layout_result.get('layout') and layout_result.get('globals_css'):
                            try:
                                # プロジェクトルートからの絶対パスを構築
                                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                                output_dir_path = os.path.join(project_root, Config.OUTPUT_DIR)
                                project_path = os.path.join(output_dir_path, project_name, "app")
                                layout_path = os.path.join(project_path, "layout.tsx")
                                css_path = os.path.join(project_path, "globals.css")
                                
                                logger.info(f"[generate_layout_with_quality_control] *** WRITING LAYOUT FILES ***")
                                
                                # layout.tsx書き込み
                                write_file(layout_path, layout_result['layout']['code'])
                                logger.info(f"[generate_layout_with_quality_control] layout.tsx written successfully")
                                
                                # LayoutCacheにセット
                                LayoutCache.set(layout_result['layout']['code'])
                                logger.info(f"[generate_layout_with_quality_control] LayoutCache updated")
                                
                                # globals.css書き込み（既存ファイルがあれば削除）
                                if os.path.exists(css_path):
                                    os.remove(css_path)
                                write_file(css_path, layout_result['globals_css']['code'])
                                logger.info(f"[generate_layout_with_quality_control] globals.css written successfully")
                                
                                logger.info(f"[generate_layout_with_quality_control] *** LAYOUT FILES WRITTEN SUCCESSFULLY ***")
                                
                            except Exception as write_error:
                                logger.error(f"[generate_layout_with_quality_control] *** LAYOUT FILE WRITE ERROR ***: {write_error}")
                                logger.error(f"[generate_layout_with_quality_control] Write error details: {type(write_error).__name__}: {str(write_error)}")
                        else:
                            logger.warning(f"[generate_layout_with_quality_control] Cannot write layout files - missing layout or globals_css data")
                        
                        layout_result['review'] = review_result
                        # globals.css内容を後続処理用に保存
                        nonlocal globals_css_content
                        globals_css_content = layout_result['globals_css']['code']
                        return layout_result
                    else:
                        # 品質基準未達
                        logger.warning(f"[generate_layout_with_quality_control] Layout quality failed attempt {attempt + 1}: score={review_score}")
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
                    logger.error(f"[generate_layout_with_quality_control] Exception attempt {attempt + 1}: {e}")
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
            max_attempts = 3
            page_name = page.get('name', 'unknown')
            slug = page.get('slug', '')
            
            for attempt in range(max_attempts):
                try:
                    logger.info(f"[develop_page_with_quality_control] Attempt {attempt + 1}/{max_attempts} for page: {page_name}")
                    
                    # develop_page実行
                    page_result = develop_page(overall_design, page, sitemap, globals_css_content, project_name)
                    
                    if not isinstance(page_result, dict) or not page_result.get("page") or not page_result.get("module_css"):
                        logger.error(f"[develop_page_with_quality_control] develop_page failed for {page_name} attempt {attempt + 1}: {page_result}")
                        if attempt == max_attempts - 1:  # 最後の試行
                            raise QualityControlException(
                                f"develop_page failed for {page_name} after {max_attempts} attempts", 
                                component=f"page_{page_name}", 
                                attempts=max_attempts
                            )
                        continue

                    # レビュー実行
                    logger.info(f"[develop_page_with_quality_control] Starting review for {page_name} attempt {attempt + 1}")
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
                
                    # review_resultの型チェックとデバッグログ
                    logger.debug(f"[develop_page_with_quality_control] Review result type: {type(review_result)}, value: {review_result}")
                    
                    # review_resultが辞書でない場合の対応
                    if not isinstance(review_result, dict):
                        logger.error(f"[develop_page_with_quality_control] Invalid review_result type for {page_name}: expected dict, got {type(review_result)}")
                        logger.error(f"[develop_page_with_quality_control] Review result content: {review_result}")
                        # デフォルト値で対応
                        review_result = {"score": 0, "feedback": f"Review failed - invalid result type: {review_result}", "passed": False}
                    
                    review_score = review_result.get('score', 0)
                    logger.info(f"[develop_page_with_quality_control] Review score for {page_name} attempt {attempt + 1}: {review_score}")
                    
                    # スコア判定
                    if review_score >= 80:
                        # 品質基準クリア - ファイル書き込みが必要かチェック
                        logger.info(f"[develop_page_with_quality_control] Quality passed with score {review_score} for {page_name}!")
                        
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
                                    logger.info(f"[develop_page_with_quality_control] HOME PAGE PATHS - page: {page_path}, css: {css_path}")
                                else:
                                    # 他のページは slug ディレクトリに配置
                                    slug = page.get('slug', '')
                                    page_dir = os.path.join(project_path, slug)
                                    page_path = os.path.join(page_dir, "page.tsx")
                                    css_path = os.path.join(page_dir, f"{slug}.module.css")
                                    logger.info(f"[develop_page_with_quality_control] NON-HOME PAGE PATHS - page: {page_path}, css: {css_path}")
                                
                                # ファイル書き込み実行
                                write_file(page_path, page_result["page"]["code"])
                                write_file(css_path, page_result["module_css"]["code"])
                                logger.info(f"[develop_page_with_quality_control] *** FILES WRITTEN SUCCESSFULLY *** for {page_name} (home: {is_home_page})")
                                
                            except Exception as write_error:
                                logger.error(f"[develop_page_with_quality_control] *** FILE WRITE ERROR *** for {page_name}: {write_error}")
                                logger.error(f"[develop_page_with_quality_control] Write error details: {type(write_error).__name__}: {str(write_error)}")
                        else:
                            logger.warning(f"[develop_page_with_quality_control] Cannot write files for {page_name} - missing page or module_css data")
                        
                        # レビュー結果を統合して成功を返す
                        logger.info(f"[develop_page_with_quality_control] Page {page_name} completed successfully with score: {review_score}")
                        return page_result
                    else:
                        # 品質基準未達 -> リトライまたはエラー
                        logger.warning(f"[develop_page_with_quality_control] Quality check failed for {page_name} attempt {attempt + 1}: score={review_score}")
                        
                        if attempt == max_attempts - 1:  # 最後の試行
                            logger.error(f"[develop_page_with_quality_control] Quality check failed after {max_attempts} attempts for {page_name}")
                            raise QualityControlException(
                                f"Quality check failed for {page_name} after {max_attempts} attempts (final score: {review_score})",
                                component=f"page_{page_name}",
                                attempts=max_attempts
                            )
                        else:
                            # リトライのためにレビューフィードバックをpage_specに追加
                            page["review_feedback"] = review_result.get('feedback', 'Quality standards not met. Please improve the code.')
                            logger.info(f"[develop_page_with_quality_control] Retrying {page_name} with feedback: {page['review_feedback']}")
                            continue
                    
                except QualityControlException:
                    # QualityControlExceptionは再発生
                    raise
                except Exception as e:
                    logger.error(f"[develop_page_with_quality_control] Exception for {page_name} attempt {attempt + 1}: {e}")
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
            logger.info("[StepGenerationAgent] Starting quality-controlled generation flow")
            
            # 1. Layout品質重視フロー実行
            logger.info("[StepGenerationAgent] Starting layout quality control")
            layout_result = generate_layout_with_quality_control()
            steps.append(layout_result)
            
            # 2. TailwindCSS生成（品質チェック不要）
            logger.info("[StepGenerationAgent] Generating TailwindCSS")
            tailwind_result = generate_tailwind_css(project_name)
            steps.append(tailwind_result)
            
            # 3. 各ページ（homeページ含む）品質重視フローを並列実行（1つ失敗で即座に停止）
            logger.info("[StepGenerationAgent] Starting pages quality control with parallel processing")
            
            # レート制限回避のため、並列度を制限
            max_workers = min(3, len(pages))  # 最大3並列でGemini APIを叩く
            logger.info(f"[StepGenerationAgent] *** PARALLEL PROCESSING MODE *** Using {max_workers} parallel workers for {len(pages)} pages")
            logger.info(f"[StepGenerationAgent] *** FAIL-FAST MODE *** Any single page failure will terminate the entire workflow")
            
            page_list = [p.get('name', 'unknown') for p in pages]
            logger.info(f"[StepGenerationAgent] Pages to process: {', '.join(page_list)}")
            
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
                    logger.info(f"[StepGenerationAgent] Submitted page {page.get('name', 'unknown')} for processing")
                
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
                        logger.info(f"[StepGenerationAgent] Page {page_name} completed successfully ({len(completed_pages)}/{len(pages)} pages done)")
                        
                    except QualityControlException as qce:
                        # ページ生成で品質制御に失敗した場合 - 即座にワークフロー停止
                        logger.error(f"[StepGenerationAgent] *** IMMEDIATE WORKFLOW TERMINATION ***")
                        logger.error(f"[StepGenerationAgent] Page {page_name} failed quality control after 3 attempts")
                        logger.error(f"[StepGenerationAgent] Error details: {str(qce)}")
                        logger.error(f"[StepGenerationAgent] Remaining {len(pages) - len(completed_pages) - 1} pages will be cancelled")
                        logger.error(f"[StepGenerationAgent] Completed pages before failure: {completed_pages}")
                        
                        # 残りのタスクをキャンセル
                        for remaining_future in futures:
                            if remaining_future != future and not remaining_future.done():
                                remaining_future.cancel()
                                logger.info(f"[StepGenerationAgent] Cancelled task for page: {futures[remaining_future]}")
                        
                        # 即座にCriticalWorkflowErrorを発生
                        raise CriticalWorkflowError(
                            f"Page generation failed: {page_name} failed quality control after 3 attempts. Error: {str(qce)}", 
                            failed_component=f"page_{page_name}"
                        )
                        
                    except Exception as e:
                        # その他の予期しないエラー - 即座にワークフロー停止
                        logger.error(f"[StepGenerationAgent] *** IMMEDIATE WORKFLOW TERMINATION ***")
                        logger.error(f"[StepGenerationAgent] Page {page_name} encountered unexpected error")
                        logger.error(f"[StepGenerationAgent] Error details: {str(e)}")
                        logger.error(f"[StepGenerationAgent] Remaining {len(pages) - len(completed_pages) - 1} pages will be cancelled")
                        logger.error(f"[StepGenerationAgent] Completed pages before failure: {completed_pages}")
                        
                        # 残りのタスクをキャンセル
                        for remaining_future in futures:
                            if remaining_future != future and not remaining_future.done():
                                remaining_future.cancel()
                                logger.info(f"[StepGenerationAgent] Cancelled task for page: {futures[remaining_future]}")
                        
                        # 即座にCriticalWorkflowErrorを発生
                        raise CriticalWorkflowError(
                            f"Page generation unexpected error: {page_name} failed with exception: {str(e)}", 
                            failed_component=f"page_{page_name}"
                        )
                
                # 全てのページが正常完了した場合
                logger.info(f"[StepGenerationAgent] All {len(pages)} pages completed successfully!")

        except QualityControlException as qce:
            # Index PageまたはLayoutの品質制御失敗 -> CriticalWorkflowErrorに変換
            logger.error(f"[StepGenerationAgent] *** CRITICAL WORKFLOW ERROR *** Quality control failed during core component generation")
            logger.error(f"[StepGenerationAgent] Failed component: {qce.component}")
            logger.error(f"[StepGenerationAgent] Error details: {str(qce)}")
            logger.error(f"[StepGenerationAgent] Workflow will be terminated")
            raise CriticalWorkflowError(
                f"Core component generation failed: {str(qce)}", 
                failed_component=qce.component
            )
        except CriticalWorkflowError as cwe:
            # CriticalWorkflowErrorは再発生してワークフロー全体を停止
            logger.error(f"[StepGenerationAgent] *** CRITICAL WORKFLOW ERROR *** Workflow termination triggered")
            logger.error(f"[StepGenerationAgent] Failed component: {cwe.failed_component}")
            logger.error(f"[StepGenerationAgent] Error details: {str(cwe)}")
            logger.error(f"[StepGenerationAgent] Workflow will be terminated immediately")
            raise
        except Exception as e:
            logger.error(f"[StepGenerationAgent] *** UNEXPECTED CRITICAL ERROR *** Unhandled exception in quality control flow")
            logger.error(f"[StepGenerationAgent] Exception type: {type(e).__name__}")
            logger.error(f"[StepGenerationAgent] Exception details: {str(e)}")
            logger.error(f"[StepGenerationAgent] Workflow will be terminated")
            raise CriticalWorkflowError(
                f"Unexpected critical error: {str(e)}", 
                failed_component="workflow"
            )
        
        logger.info(f"[StepGenerationAgent] Quality control flow completed. Total required_libs: {all_required_libs}")
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
