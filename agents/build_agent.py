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
            
            # ビルド出力ディレクトリの確認（改良版）
            build_output_path = None
            
            # 1. 静的エクスポート用のoutディレクトリをチェック
            out_dir = os.path.join(project_path, "out")
            if os.path.exists(out_dir) and os.listdir(out_dir):
                build_output_path = out_dir
                self.logger.info(f"[BuildAgent] Using static export output directory: {build_output_path}")
            
            # 2. outディレクトリが存在しない場合、.nextディレクトリをチェック
            elif os.path.exists(os.path.join(project_path, ".next")):
                build_output_path = os.path.join(project_path, ".next")
                self.logger.info(f"[BuildAgent] Using Next.js build directory: {build_output_path}")
            
            # 3. 両方とも存在しない場合は警告を出すが、エラーにはしない
            else:
                self.logger.warning(f"[BuildAgent] No build output directory found in {project_path}")
                # プロジェクトパス自体を出力パスとして使用（フォールバック）
                build_output_path = project_path
            
            # next.config.jsの存在をチェックして静的エクスポート設定を確認
            next_config_path = os.path.join(project_path, "next.config.js")
            is_static_export = False
            if os.path.exists(next_config_path):
                try:
                    with open(next_config_path, 'r', encoding='utf-8') as f:
                        config_content = f.read()
                        is_static_export = "output: 'export'" in config_content
                        self.logger.debug(f"[BuildAgent] Static export detected: {is_static_export}")
                except Exception as e:
                    self.logger.warning(f"[BuildAgent] Failed to read next.config.js: {e}")
            
            # 静的エクスポートが設定されているのにoutディレクトリがない場合の対処
            if is_static_export and not os.path.exists(out_dir):
                self.logger.warning("[BuildAgent] Static export configured but 'out' directory not found")
                self.logger.info("[BuildAgent] This might indicate a build configuration issue")
            
            return {
                "status": "success",
                "project_id": project_id,
                "project_path": project_path,
                "build_output_path": build_output_path,
                "is_static_export": is_static_export,
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
            
            # next.config.jsをチェック
            next_config_path = os.path.join(project_path, "next.config.js")
            
            # 既存の設定を確認
            has_static_export = False
            if os.path.exists(next_config_path):
                try:
                    with open(next_config_path, 'r', encoding='utf-8') as f:
                        config_content = f.read()
                        has_static_export = "output: 'export'" in config_content
                        self.logger.info(f"[BuildAgent] Static export already configured: {has_static_export}")
                except Exception as e:
                    self.logger.warning(f"[BuildAgent] Failed to read next.config.js: {e}")
            
            # 静的エクスポートが設定されていない場合のみ、最小限の設定を追加
            if not has_static_export:
                self.logger.info("[BuildAgent] Adding minimal static export configuration")
                
                # バックアップを作成（存在する場合）
                if os.path.exists(next_config_path):
                    backup_path = next_config_path + ".backup"
                    if not os.path.exists(backup_path):
                        import shutil
                        shutil.copy2(next_config_path, backup_path)
                        self.logger.info(f"[BuildAgent] Backup created: {backup_path}")
                
                # 最小限の静的エクスポート設定
                minimal_config = '''/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
}

module.exports = nextConfig
'''
                
                # 設定を書き込み
                with open(next_config_path, 'w', encoding='utf-8') as f:
                    f.write(minimal_config)
                
                self.logger.info(f"[BuildAgent] Minimal static export configuration created")
            else:
                self.logger.info("[BuildAgent] Static export already configured, no changes needed")
            
            return {
                "status": "success",
                "message": "Project prepared for static export with minimal changes",
                "project_path": project_path,
                "config_path": next_config_path,
                "config_modified": not has_static_export
            }
            
        except Exception as e:
            error_msg = f"Failed to prepare static export: {str(e)}"
            self.logger.error(f"[BuildAgent] {error_msg}")
            return {"status": "error", "error": error_msg}
    
 
