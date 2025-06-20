import os
import subprocess
from logger import Logger
from config import Config

class BuildAgent:
    """Next.jsプロジェクトをビルドするエージェント"""
    
    def __init__(self):
        self.logger = Logger(log_file=Config.LOG_FILE)
    
    def build_project(self, project_id: str) -> dict:
        """
        指定されたプロジェクトIDのNext.jsプロジェクトをビルドする
        
        Args:
            project_id (str): ビルド対象のプロジェクトID
            
        Returns:
            dict: ビルド結果
        """
        try:
            self.logger.info(f"[BuildAgent] Starting build for project: {project_id}")
            
            base_dir = os.path.dirname(os.path.dirname(__file__))  # web_development_agentディレクトリ
            project_path = os.path.join(base_dir, Config.OUTPUT_DIR, project_id)
            
            if not os.path.exists(project_path):
                error_msg = f"Project directory not found: {project_path}"
                self.logger.error(f"[BuildAgent] {error_msg}")
                return {"status": "error", "error": error_msg}
            
            # package.jsonの存在確認
            package_json_path = os.path.join(project_path, "package.json")
            if not os.path.exists(package_json_path):
                error_msg = f"package.json not found in: {project_path}"
                self.logger.error(f"[BuildAgent] {error_msg}")
                return {"status": "error", "error": error_msg}
            
            self.logger.info(f"[BuildAgent] Building project at: {project_path}")
            
            # npm run buildを実行
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            self.logger.info(f"[BuildAgent] Build completed successfully")
            self.logger.debug(f"[BuildAgent] Build stdout: {result.stdout}")
            self.logger.debug(f"[BuildAgent] Build stderr: {result.stderr}")
            
            # ビルド出力ディレクトリの確認
            build_output_path = os.path.join(project_path, "out")
            if not os.path.exists(build_output_path):
                # Next.jsの場合、.next/static や .next/server なども確認
                next_build_path = os.path.join(project_path, ".next")
                if os.path.exists(next_build_path):
                    build_output_path = next_build_path
                else:
                    error_msg = "Build output directory not found"
                    self.logger.warning(f"[BuildAgent] {error_msg}")
                    # ただし、ビルド自体は成功した場合はエラーにしない
            
            return {
                "status": "success",
                "project_id": project_id,
                "project_path": project_path,
                "build_output_path": build_output_path,
                "message": f"Build completed successfully for project: {project_id}",
                "build_stdout": result.stdout,
                "build_stderr": result.stderr
            }
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Build failed with exit code {e.returncode}: {e.stderr}"
            self.logger.error(f"[BuildAgent] {error_msg}")
            return {
                "status": "error",
                "error": error_msg,
                "project_id": project_id,
                "stdout": e.stdout,
                "stderr": e.stderr
            }
            
        except Exception as e:
            error_msg = f"Unexpected error during build: {str(e)}"
            self.logger.error(f"[BuildAgent] {error_msg}")
            return {
                "status": "error",
                "error": error_msg,
                "project_id": project_id
            }
    
    def prepare_for_static_export(self, project_id: str) -> dict:
        """
        静的エクスポート用にNext.jsプロジェクトを準備する
        
        Args:
            project_id (str): プロジェクトID
            
        Returns:
            dict: 準備結果
        """
        try:
            self.logger.info(f"[BuildAgent] Preparing static export for project: {project_id}")
            
            # base_dirを使って絶対パスで解決（build_projectメソッドと同じパス解決方法）
            base_dir = os.path.dirname(os.path.dirname(__file__))  # web_development_agentディレクトリ
            project_path = os.path.join(base_dir, Config.OUTPUT_DIR, project_id)
            
            if not os.path.exists(project_path):
                error_msg = f"Project directory not found: {project_path}"
                self.logger.error(f"[BuildAgent] {error_msg}")
                return {"status": "error", "error": error_msg}
            
            # next.config.jsを確認・作成
            next_config_path = os.path.join(project_path, "next.config.js")
            
            static_export_config = '''/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
}

module.exports = nextConfig
'''
            
            # 既存のnext.config.jsがあるかチェック
            if os.path.exists(next_config_path):
                self.logger.info("[BuildAgent] next.config.js already exists, backing up...")
                # バックアップを作成
                backup_path = next_config_path + ".backup"
                os.rename(next_config_path, backup_path)
            
            # 静的エクスポート用の設定を書き込み
            with open(next_config_path, 'w') as f:
                f.write(static_export_config)
            
            self.logger.info(f"[BuildAgent] Static export configuration created at: {project_path}")
            
            return {
                "status": "success",
                "message": "Project prepared for static export",
                "project_path": project_path,
                "config_path": next_config_path
            }
            
        except Exception as e:
            error_msg = f"Failed to prepare static export: {str(e)}"
            self.logger.error(f"[BuildAgent] {error_msg}")
            return {"status": "error", "error": error_msg} 