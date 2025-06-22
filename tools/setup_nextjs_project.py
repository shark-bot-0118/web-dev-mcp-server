import os
import subprocess
import uuid
from logger import Logger
from config import Config
logger = Logger(log_level="INFO")

def generate_unique_project_name() -> str:
    """ランダムプレフィックス付きのユニークなプロジェクト名を生成"""
    # 8文字のランダムプレフィックスを生成
    random_prefix = uuid.uuid4().hex[:8]
    return f"nextjs_site_{random_prefix}"

def is_setup_done(project_path):
    return os.path.exists(os.path.join(project_path, "package.json")) and os.path.exists(os.path.join(project_path, "app"))

def setup_nextjs_project(output_dir: str = None) -> dict:
    # output_dirが指定されていない場合は、Config.OUTPUT_DIRを使用
    if output_dir is None:
        output_dir = Config.OUTPUT_DIR
    
    # プロジェクトルートディレクトリを取得（tools/の親ディレクトリ）
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # プロジェクトルートからの相対パスでoutput_dirを構築
    output_dir_path = os.path.join(project_root, output_dir)
    
    project_name = generate_unique_project_name()
    logger.info(f"[SetupNextjsProject] Project ID Created: {project_name}")
    logger.info(f"[SetupNextjsProject] Project root: {project_root}")
    logger.info(f"[SetupNextjsProject] Output directory: {output_dir_path}")
    
    project_path = os.path.join(output_dir_path, project_name)
    os.makedirs(output_dir_path, exist_ok=True)

    if is_setup_done(project_path):
        return {"status": "already_exists", "project_path": project_path, "project_name": project_name}

    os.makedirs(project_path, exist_ok=True)
    try:
        # Node.js LTSバージョンを明示的に使う
        nvm_cmd = ["bash", "-c", "source $NVM_DIR/nvm.sh && nvm install --lts && nvm use --lts && node -v"]
        logger.info(f"Ensuring Node.js LTS version via nvm: {' '.join(nvm_cmd)}")
        subprocess.run(nvm_cmd, cwd=output_dir_path, capture_output=True, text=True, check=False)

        # create-next-appの安定版を指定（例: 14.1.0）
        cmd = [
            "npx", "create-next-app@14.1.0", project_name,
            "--use-npm", "--no-git", "--typescript", "--eslint",
            "--app", "--tailwind", "--no-src-dir", "--no-import-alias", "--yes"
        ]

        logger.info(f"Running: {' '.join(cmd)} in {output_dir_path}")
        result = subprocess.run(
            cmd,
            cwd=output_dir_path,
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "CI": "true"}
        )
        logger.info(f"Next.js project initialized at {project_path}\nstdout: {result.stdout}\nstderr: {result.stderr}")
        if is_setup_done(project_path):
            return {
                "status": "success",
                "project_path": project_path,
                "project_name": project_name,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        else:
            return {
                "status": "partial",
                "project_path": project_path,
                "project_name": project_name,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "error": "Project not fully initialized after setup."
            }
    except Exception as e:
        return {
            "status": "error",
            "project_path": project_path,
            "project_name": project_name,
            "error": str(e),
            "stdout": result.stdout if 'result' in locals() else None,
            "stderr": result.stderr if 'result' in locals() else None
        } 
