from jinja2 import Environment, FileSystemLoader
import os
import subprocess
import threading
import time
import webbrowser
import requests
import sys
import signal
from config import Config
from logger import Logger

logger = Logger(log_file=Config.LOG_FILE)

class ExecutionAgent:
    def start_nextjs_server(self, project_path: str, port: int = 3000) -> dict:
        """Next.jsサーバーを起動してブラウザでページを開く"""
        try:
            logger.info(f"[ExecutionAgent] Starting Next.js development server at {project_path}")
            
            # まずプロジェクトディレクトリの確認
            if not os.path.exists(project_path):
                logger.error(f"[ExecutionAgent] Project path does not exist: {project_path}")
                return {
                    "status": "error",
                    "error": f"Project path does not exist: {project_path}"
                }
            
            # package.jsonの確認
            package_json_path = os.path.join(project_path, "package.json")
            if not os.path.exists(package_json_path):
                logger.error(f"[ExecutionAgent] package.json not found at {package_json_path}")
                return {
                    "status": "error",
                    "error": f"package.json not found at {package_json_path}"
                }
            
            # 既存のプロセスを確認してポートが使用されているかチェック
            if self._is_port_in_use(port):
                logger.warning(f"[ExecutionAgent] Port {port} is already in use, trying next port")
                port = self._find_available_port(port)
                logger.info(f"[ExecutionAgent] Using port {port} instead")
            
            
            # npm run devでサーバーを起動
            logger.info(f"[ExecutionAgent] Starting development server on port {port}")
            process = subprocess.Popen(
                ["npm", "run", "dev", "--", "--port", str(port)],
                cwd=project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # エラーメッセージと出力を収集するためのリスト
            server_errors = []
            server_output = []
            server_ready = False
            
            # サーバーの出力をモニタリングするスレッド
            def monitor_server_output():
                nonlocal server_ready
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        line = output.strip()
                        server_output.append(line)
                        logger.debug(f"[ExecutionAgent] Server output: {line}")
                        
                        # Next.jsの起動完了メッセージを確認
                        if "ready" in line.lower() or "started" in line.lower():
                            logger.info(f"[ExecutionAgent] Server ready signal detected")
                            server_ready = True
                        
                        # コンパイルエラーを検出
                        if self._is_compilation_error(line):
                            error_info = self._parse_compilation_error(line, server_output)
                            if error_info:
                                server_errors.append(error_info)
                                logger.warning(f"[ExecutionAgent] Compilation error detected: {error_info}")
            
            # エラーメッセージをモニタリングするスレッド
            def monitor_server_errors():
                while True:
                    error = process.stderr.readline()
                    if error == '' and process.poll() is not None:
                        break
                    if error:
                        line = error.strip()
                        server_output.append(f"[STDERR] {line}")
                        logger.debug(f"[ExecutionAgent] Server error: {line}")
                        
                        # コンパイルエラーを検出
                        if self._is_compilation_error(line):
                            error_info = self._parse_compilation_error(line, server_output)
                            if error_info:
                                server_errors.append(error_info)
                                logger.warning(f"[ExecutionAgent] Compilation error detected: {error_info}")
            
            # サーバー出力モニタリングを開始
            monitor_thread = threading.Thread(target=monitor_server_output)
            monitor_thread.daemon = False  # デーモンスレッドにしない
            monitor_thread.start()
            
            # エラーモニタリングを開始
            error_thread = threading.Thread(target=monitor_server_errors)
            error_thread.daemon = False
            error_thread.start()
            
            # サーバーが起動するまで待機し、ブラウザを開く
            url = f"http://localhost:{port}"
            server_ready = self._wait_for_server_with_detailed_check(url, process)
            
            if not server_ready:
                # サーバーが起動しない場合の詳細エラー
                stdout, stderr = process.communicate(timeout=5)
                logger.error(f"[ExecutionAgent] Server failed to start properly")
                logger.error(f"[ExecutionAgent] stdout: {stdout}")
                logger.error(f"[ExecutionAgent] stderr: {stderr}")
                return {
                    "status": "error",
                    "error": f"Server failed to start: {stderr}",
                    "stdout": stdout,
                    "stderr": stderr
                }
            
            # ブラウザを確実に開く
            logger.info(f"[ExecutionAgent] Opening browser at {url}")
            success = self._open_browser_reliably(url)
            
            if not success:
                logger.warning(f"[ExecutionAgent] Failed to open browser automatically")
            
            # プロセス終了時のクリーンアップを設定
            def cleanup_handler(signum, frame):
                logger.info(f"[ExecutionAgent] Cleaning up server process")
                if process.poll() is None:
                    process.terminate()
                    time.sleep(2)
                    if process.poll() is None:
                        process.kill()
                sys.exit(0)
            
            signal.signal(signal.SIGINT, cleanup_handler)
            signal.signal(signal.SIGTERM, cleanup_handler)
            
            logger.info(f"[ExecutionAgent] Next.js server started successfully on port {port}")
            logger.info(f"[ExecutionAgent] Access your site at: {url}")
            
            return {
                "status": "success",
                "url": url,
                "process": process,
                "port": port,
                "message": f"Development server is running at {url}. Browser should open automatically.",
                "compilation_errors": server_errors,
                "server_output": server_output,
                "has_errors": len(server_errors) > 0
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"[ExecutionAgent] npm install timed out")
            return {
                "status": "error",
                "error": "npm install timed out after 5 minutes"
            }
        except Exception as e:
            logger.error(f"[ExecutionAgent] Failed to start Next.js server: {e}")
            return {
                "status": "error",
                "error": str(e)
            } 
    
    def _is_port_in_use(self, port: int) -> bool:
        """ポートが使用中かどうかをチェック"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    def _find_available_port(self, start_port: int) -> int:
        """利用可能なポートを見つける"""
        port = start_port
        while port < start_port + 100:  # 最大100ポート試す
            if not self._is_port_in_use(port):
                return port
            port += 1
        return start_port  # 見つからない場合は元のポートを返す
    
    def _wait_for_server_with_detailed_check(self, url: str, process: subprocess.Popen, max_attempts: int = 60) -> bool:
        """サーバーが起動するまで詳細チェックで待機"""
        logger.info(f"[ExecutionAgent] Waiting for server to be ready at {url}")
        
        for attempt in range(max_attempts):
            # プロセスがまだ生きているかチェック
            if process.poll() is not None:
                logger.error(f"[ExecutionAgent] Server process exited unexpectedly")
                return False
            
            try:
                # HTTPリクエストでサーバーの応答をチェック
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    logger.info(f"[ExecutionAgent] Server is responding! Status: {response.status_code}")
                    time.sleep(2)  # 少し待ってから確実にする
                    return True
                else:
                    logger.debug(f"[ExecutionAgent] Server responded with status: {response.status_code}")
            except requests.exceptions.ConnectionError:
                # まだサーバーが起動してない（正常）
                logger.debug(f"[ExecutionAgent] Attempt {attempt + 1}/{max_attempts}: Server not ready yet")
            except requests.exceptions.Timeout:
                logger.debug(f"[ExecutionAgent] Attempt {attempt + 1}/{max_attempts}: Request timeout")
            except Exception as e:
                logger.debug(f"[ExecutionAgent] Attempt {attempt + 1}/{max_attempts}: Error {e}")
            
            time.sleep(1)
        
        logger.warning(f"[ExecutionAgent] Server did not respond after {max_attempts} seconds")
        return False
    
    def _open_browser_reliably(self, url: str) -> bool:
        """ブラウザを確実に開く"""
        try:
            # 複数の方法でブラウザを開こうとする
            methods = [
                lambda: webbrowser.open(url),
                lambda: webbrowser.open_new_tab(url),
                lambda: webbrowser.open_new(url)
            ]
            
            for i, method in enumerate(methods):
                try:
                    logger.info(f"[ExecutionAgent] Trying browser open method {i + 1}")
                    result = method()
                    if result:
                        logger.info(f"[ExecutionAgent] Browser opened successfully using method {i + 1}")
                        return True
                    time.sleep(1)
                except Exception as e:
                    logger.debug(f"[ExecutionAgent] Browser open method {i + 1} failed: {e}")
            
            # macOSの場合はopenコマンドも試す
            if sys.platform == "darwin":
                try:
                    logger.info(f"[ExecutionAgent] Trying macOS open command")
                    subprocess.run(["open", url], check=True)
                    logger.info(f"[ExecutionAgent] Browser opened using macOS open command")
                    return True
                except Exception as e:
                    logger.debug(f"[ExecutionAgent] macOS open command failed: {e}")
            
            # Linuxの場合はxdg-openも試す
            elif sys.platform.startswith("linux"):
                try:
                    logger.info(f"[ExecutionAgent] Trying Linux xdg-open command")
                    subprocess.run(["xdg-open", url], check=True)
                    logger.info(f"[ExecutionAgent] Browser opened using xdg-open")
                    return True
                except Exception as e:
                    logger.debug(f"[ExecutionAgent] Linux xdg-open failed: {e}")
            
            # Windowsの場合はstartコマンドも試す
            elif sys.platform == "win32":
                try:
                    logger.info(f"[ExecutionAgent] Trying Windows start command")
                    subprocess.run(["start", url], shell=True, check=True)
                    logger.info(f"[ExecutionAgent] Browser opened using Windows start command")
                    return True
                except Exception as e:
                    logger.debug(f"[ExecutionAgent] Windows start command failed: {e}")
            
            logger.warning(f"[ExecutionAgent] All browser opening methods failed")
            logger.info(f"[ExecutionAgent] Please manually open your browser and go to: {url}")
            return False
            
        except Exception as e:
            logger.error(f"[ExecutionAgent] Error in browser opening: {e}")
            return False
    
    def _is_compilation_error(self, line: str) -> bool:
        """コンパイルエラーかどうかを判定"""
        error_patterns = [
            "error",
            "failed to compile",
            "syntax error",
            "type error",
            "module not found",
            "cannot resolve",
            "unexpected token",
            "parsing error",
            "build error",
            "compilation error"
        ]
        
        line_lower = line.lower()
        return any(pattern in line_lower for pattern in error_patterns)
    
    def _parse_compilation_error(self, error_line: str, full_output: list) -> dict:
        """コンパイルエラーを解析してファイル情報を抽出"""
        try:
            # Next.jsの典型的なエラーパターンを解析
            error_info = {
                "error_line": error_line,
                "file_path": None,
                "line_number": None,
                "column_number": None,
                "error_type": None,
                "error_message": None,
                "suggested_fix": None
            }
            
            # ファイルパスと行番号の抽出 (例: ./app/page.tsx:15:20)
            import re
            file_pattern = r'([./][\w/.-]+\.(?:tsx?|jsx?|css|scss|sass)):(\d+):?(\d+)?'
            file_match = re.search(file_pattern, error_line)
            
            if file_match:
                error_info["file_path"] = file_match.group(1)
                error_info["line_number"] = int(file_match.group(2))
                if file_match.group(3):
                    error_info["column_number"] = int(file_match.group(3))
            
            # エラータイプの判定
            error_line_lower = error_line.lower()
            if "syntax error" in error_line_lower:
                error_info["error_type"] = "syntax"
            elif "type error" in error_line_lower or "typescript" in error_line_lower:
                error_info["error_type"] = "typescript"
            elif "module not found" in error_line_lower:
                error_info["error_type"] = "module_not_found"
            elif "cannot resolve" in error_line_lower:
                error_info["error_type"] = "import_error"
            elif "unexpected token" in error_line_lower:
                error_info["error_type"] = "syntax"
            else:
                error_info["error_type"] = "general"
            
            # エラーメッセージの抽出
            if "error:" in error_line_lower:
                error_info["error_message"] = error_line.split("error:", 1)[1].strip()
            else:
                error_info["error_message"] = error_line
            
            # 修正案の生成
            error_info["suggested_fix"] = self._generate_error_fix_suggestion(error_info)
            
            return error_info
            
        except Exception as e:
            logger.debug(f"[ExecutionAgent] Error parsing compilation error: {e}")
            return {
                "error_line": error_line,
                "file_path": None,
                "line_number": None,
                "error_type": "parse_failed",
                "error_message": error_line,
                "suggested_fix": None
            }
    
    def _generate_error_fix_suggestion(self, error_info: dict) -> str:
        """エラータイプに基づいて修正案を生成"""
        error_type = error_info.get("error_type")
        error_message = error_info.get("error_message", "").lower()
        
        if error_type == "syntax":
            if "expected" in error_message and "received" in error_message:
                return "シンタックスエラー: 括弧やクォートの不一致を確認してください"
            return "シンタックスエラー: コードの構文を確認してください"
        
        elif error_type == "typescript":
            if "cannot find name" in error_message:
                return "TypeScriptエラー: 変数や関数が定義されていません。インポートまたは宣言を確認してください"
            elif "type" in error_message and "is not assignable" in error_message:
                return "TypeScriptエラー: 型の不一致です。正しい型を確認してください"
            return "TypeScriptエラー: 型定義を確認してください"
        
        elif error_type == "module_not_found":
            return "モジュールエラー: パッケージが見つかりません。npm installまたはインポートパスを確認してください"
        
        elif error_type == "import_error":
            return "インポートエラー: ファイルパスまたはエクスポート名を確認してください"
        
        else:
            return "一般的なエラー: コードとファイル構造を確認してください"
    
    def auto_fix_compilation_errors(self, project_path: str, errors: list) -> dict:
        """コンパイルエラーを自動修正する"""
        if not errors:
            return {"status": "no_errors", "message": "修正するエラーがありません"}
        
        fixed_errors = []
        failed_fixes = []
        
        for error in errors:
            try:
                fix_result = self._attempt_error_fix(project_path, error)
                if fix_result["success"]:
                    fixed_errors.append({
                        "error": error,
                        "fix_applied": fix_result["fix_applied"]
                    })
                else:
                    failed_fixes.append({
                        "error": error,
                        "reason": fix_result["reason"]
                    })
            except Exception as e:
                failed_fixes.append({
                    "error": error,
                    "reason": f"修正処理中にエラーが発生: {str(e)}"
                })
        
        return {
            "status": "completed",
            "fixed_errors": fixed_errors,
            "failed_fixes": failed_fixes,
            "total_errors": len(errors),
            "fixed_count": len(fixed_errors),
            "failed_count": len(failed_fixes)
        }
    
    def _attempt_error_fix(self, project_path: str, error: dict) -> dict:
        """個別エラーの修正を試行"""
        file_path = error.get("file_path")
        error_type = error.get("error_type")
        error_message = error.get("error_message", "").lower()
        
        if not file_path:
            return {"success": False, "reason": "ファイルパスが特定できません"}
        
        # 絶対パスに変換
        if file_path.startswith('./'):
            file_path = file_path[2:]
        full_path = os.path.join(project_path, file_path)
        
        if not os.path.exists(full_path):
            return {"success": False, "reason": f"ファイルが見つかりません: {full_path}"}
        
        try:
            # ファイル内容を読み込み
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # エラータイプ別の修正処理
            if error_type == "module_not_found" and "react" in error_message:
                # Reactインポートの追加
                if "import React from 'react'" not in content:
                    fixed_content = "import React from 'react';\n" + content
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    return {"success": True, "fix_applied": "Reactインポートを追加しました"}
            
            elif error_type == "syntax" and "unexpected token" in error_message:
                # よくあるシンタックスエラーの修正（簡単なもの）
                lines = content.split('\n')
                line_num = error.get("line_number")
                if line_num and line_num <= len(lines):
                    # セミコロン不足の修正
                    target_line = lines[line_num - 1]
                    if not target_line.strip().endswith((';', '{', '}', ')', ']')):
                        lines[line_num - 1] = target_line + ';'
                        fixed_content = '\n'.join(lines)
                        with open(full_path, 'w', encoding='utf-8') as f:
                            f.write(fixed_content)
                        return {"success": True, "fix_applied": "セミコロンを追加しました"}
            
            return {"success": False, "reason": "自動修正パターンに該当しませんでした"}
            
        except Exception as e:
            return {"success": False, "reason": f"ファイル処理エラー: {str(e)}"}
    
    def monitor_and_fix_continuously(self, project_path: str, port: int = 3000, auto_fix: bool = True) -> dict:
        """サーバーを起動して継続的にエラーを監視・修正する"""
        logger.info(f"[ExecutionAgent] Starting continuous monitoring for {project_path}")
        
        # サーバーを起動
        result = self.start_nextjs_server(project_path, port)
        
        if result["status"] != "success":
            return result
        
        # エラーが検出された場合の処理
        if result["has_errors"] and auto_fix:
            logger.info(f"[ExecutionAgent] {len(result['compilation_errors'])} compilation errors detected, attempting auto-fix")
            
            fix_result = self.auto_fix_compilation_errors(project_path, result["compilation_errors"])
            result["auto_fix_result"] = fix_result
            
            if fix_result["fixed_count"] > 0:
                logger.info(f"[ExecutionAgent] Successfully fixed {fix_result['fixed_count']} errors")
                result["message"] += f" ({fix_result['fixed_count']} errors auto-fixed)"
            
            if fix_result["failed_count"] > 0:
                logger.warning(f"[ExecutionAgent] Failed to fix {fix_result['failed_count']} errors")
                result["message"] += f" ({fix_result['failed_count']} errors need manual fix)"
        
        return result 
