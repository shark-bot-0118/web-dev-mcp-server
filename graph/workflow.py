# Langgraphワークフロー雛形

import sys
import os
from config import Config
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from tools.setup_nextjs_project import setup_nextjs_project

def run_workflow(user_instruction: str) -> dict:
    from agents.instruction_analysis import InstructionAnalysisAgent
    from agents.step_generation import StepGenerationAgent, CriticalWorkflowError
    from agents.execution import ExecutionAgent
    from logger import Logger
    logger = Logger(log_level="INFO")

    logger.info("[Workflow] Start workflow")
    # 1. 指示解析
    analysis_agent = InstructionAnalysisAgent()
    analysis_result = analysis_agent.analyze(user_instruction)
    requirements = analysis_result
    logger.info("[Workflow] Instruction analysis complete")
    logger.debug(f"[Workflow] requirements: {requirements}")

    # 2. Next.jsセットアップ（setup_nextjs_project.pyを一度だけ実行）
    logger.info("[Workflow] Project setup start")
    setup_result = setup_nextjs_project()
    if setup_result.get("status") == "error":
        logger.debug(f"[Workflow] setup_nextjs_project.py failed: {setup_result}")
        return {"status": "error", "error": setup_result.get("error", "setup failed")}
    
    # プロジェクト名を取得
    project_name = setup_result.get("project_name")
    if not project_name:
        return {"status": "error", "error": "Failed to get project name from setup"}
    
    logger.info(f"[Workflow] Project setup complete with name: {project_name}")

    # 3. ステップ生成（品質制御付き）
    logger.info("[Workflow] Step generation start")
    try:
        step_agent = StepGenerationAgent()
        steps, all_required_libs = step_agent.generate_steps(requirements, project_name)
        logger.info("[Workflow] Step generation complete")
        logger.debug(f"[Workflow] steps: {steps}")
        logger.debug(f"[Workflow] all_required_libs: {all_required_libs}")
    except CriticalWorkflowError as cwe:
        # 品質制御で3回失敗した場合はワークフロー全体を停止
        logger.error(f"[Workflow] *** CRITICAL WORKFLOW TERMINATION ***")
        logger.error(f"[Workflow] Reason: Quality control failed after maximum attempts")
        logger.error(f"[Workflow] Failed component: {cwe.failed_component}")
        logger.error(f"[Workflow] Error details: {str(cwe)}")
        logger.error(f"[Workflow] Recommendation: Review and improve the generated content quality")
        logger.error(f"[Workflow] *** WORKFLOW TERMINATED ***")
        return {
            "status": "error", 
            "error": f"Critical workflow failure: {str(cwe)}",
            "failed_component": cwe.failed_component,
            "error_type": "quality_control_failure",
            "recommendation": "The system attempted to generate content 3 times but failed to meet quality standards. Please review the requirements and try again."
        }

    # 4. 必要なnpmパッケージをまとめてインストール
    # プロジェクトパスの構築
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir_path = os.path.join(project_root, Config.OUTPUT_DIR)
    project_path = os.path.join(output_dir_path, project_name)
    
    # Next.jsのデフォルトライブラリリスト（これらはインストール不要）
    nextjs_default_libs = {
        'next/image',
        'next/link', 
        'next/router',
        'next/head',
        'next/script',
        'next/document',
        'next/app',
        'next/server',
        'next/navigation',
        'next/headers',
        'next/cookies',
        'next/cache',
        'next/font',
        'react',
        'react-dom'
    }
    
    # デフォルトライブラリを除外した実際にインストールが必要なライブラリのみを抽出
    libs_to_install = [lib for lib in all_required_libs if lib not in nextjs_default_libs] if all_required_libs else []
    
    if libs_to_install:
        logger.info(f"[Workflow] npm install start for: {libs_to_install}")
        import subprocess
        try:
            # 必ずNext.jsプロジェクトディレクトリでnpm installを実行
            result = subprocess.run(["npm", "install"] + libs_to_install, cwd=project_path, capture_output=True, text=True, check=True)
            logger.debug(f"[Workflow] npm install stdout: {result.stdout}")
            logger.debug(f"[Workflow] npm install stderr: {result.stderr}")
            logger.info("[Workflow] npm install complete")
        except Exception as e:
            logger.debug(f"[Workflow] npm install failed: {e}")
            return {"status": "error", "error": str(e)}
    else:
        logger.info("[Workflow] No additional packages to install (all required libraries are Next.js defaults)")

    # 5. サーバー起動とページ表示
    logger.info("[Workflow] Next.js server startup start")
    exec_agent = ExecutionAgent()
    
    # サーバーを起動
    server_result = exec_agent.start_nextjs_server(project_path)
    
    if server_result.get("status") == "error":
        logger.error(f"[Workflow] Failed to start server: {server_result.get('error')}")
        return {"status": "error", "error": server_result.get("error")}
    
    logger.info(f"[Workflow] Server started: {server_result.get('message')}")
    logger.info(f"[Workflow] Server URL: {server_result.get('url')}")
    logger.info("[Workflow] Next.js server startup complete")
    
    # サーバーの継続実行メッセージ
    logger.info("[Workflow] Development server is now running.")
    logger.info(f"[Workflow] You can access your site at: {server_result.get('url')}")
    logger.info("[Workflow] The server is running in the background.")
    
    # サーバープロセスが実行中であることを確認
    process = server_result.get("process")
    if process and process.poll() is None:
        logger.info("[Workflow] Server process is running successfully")
        logger.info("[Workflow] Server PID: {0}".format(process.pid))
        
        # サーバー起動完了をログに記録（無限待機はしない）
        logger.info("[Workflow] *** WORKFLOW COMPLETED SUCCESSFULLY ***")
        logger.info("[Workflow] Next.js development server is now running in the background")
        logger.info(f"[Workflow] Site URL: {server_result.get('url')}")
        logger.info(f"[Workflow] Project location: {project_path}")
        logger.info("[Workflow] The server will continue running until manually stopped")
        logger.info("[Workflow] To stop the server, you can:")
        logger.info(f"[Workflow]   1. Kill process with PID {process.pid}")
        logger.info("[Workflow]   2. Press Ctrl+C if running in terminal")
        logger.info("[Workflow]   3. Close the terminal/command window")
        logger.info("[Workflow] *** WORKFLOW EXECUTION COMPLETE ***")
    else:
        logger.warning("[Workflow] Server process not found or already terminated")
        logger.warning("[Workflow] Please check server startup manually")

    return {
        "status": "success",
        "project_name": project_name,
        "server_url": server_result.get("url"),
        "port": server_result.get("port"),
        "project_path": project_path,
        "process_pid": process.pid if (process and process.poll() is None) else None,
        "message": f"Workflow completed successfully! Server running at {server_result.get('url')}",
        "completion_status": "workflow_complete_server_running"
    } 
