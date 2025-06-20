"""
Next.js Project Setup Utilities
"""

import os
import subprocess
import logging
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

from config import Config

logger = logging.getLogger(__name__)

class NextJSProjectSetup:
    """Utility class for setting up Next.js projects"""
    
    def __init__(self):
        self.config = Config()
    
    def generate_project_id(self) -> str:
        """Generate a unique project identifier"""
        # Use first 8 characters of UUID for uniqueness while keeping it readable
        project_uuid = str(uuid.uuid4())[:8]
        project_id = f"nextjs-site-{project_uuid}"
        logger.info(f"Generated project ID: {project_id}")
        return project_id
    
    def create_nextjs_project(self, project_id: str) -> Dict[str, Any]:
        """
        Create a new Next.js project with TypeScript and TailwindCSS
        
        Args:
            project_id: Unique identifier for the project
            
        Returns:
            Dict containing project creation results
        """
        try:
            project_path = os.path.join(self.config.OUTPUT_DIR, project_id)
            
            # Ensure output directory exists
            os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)
            
            logger.info(f"Creating Next.js project at: {project_path}")
            
            # Create Next.js project with TypeScript and TailwindCSS
            cmd = [
                "npx", "create-next-app@latest", project_id,
                "--typescript",
                "--tailwind", 
                "--eslint",
                "--app",
                "--src-dir",
                "--import-alias", "@/*",
                "--yes"  # Auto-accept prompts
            ]
            
            # Run the command in the output directory
            result = subprocess.run(
                cmd,
                cwd=self.config.OUTPUT_DIR,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Next.js project created successfully at: {project_path}")
                
                # Verify project structure
                if self._verify_project_structure(project_path):
                    return {
                        "success": True,
                        "project_id": project_id,
                        "project_path": project_path,
                        "message": "Next.js project created successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Project structure verification failed"
                    }
            else:
                error_msg = f"Failed to create Next.js project: {result.stderr}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            error_msg = "Next.js project creation timed out"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error creating Next.js project: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    def _verify_project_structure(self, project_path: str) -> bool:
        """Verify that the Next.js project was created correctly"""
        try:
            required_files = [
                "package.json",
                "next.config.js",
                "tailwind.config.ts",
                "tsconfig.json"
            ]
            
            required_dirs = [
                "src",
                "src/app"
            ]
            
            # Check required files
            for file_name in required_files:
                file_path = os.path.join(project_path, file_name)
                if not os.path.exists(file_path):
                    logger.warning(f"Required file missing: {file_name}")
                    return False
            
            # Check required directories
            for dir_name in required_dirs:
                dir_path = os.path.join(project_path, dir_name)
                if not os.path.exists(dir_path):
                    logger.warning(f"Required directory missing: {dir_name}")
                    return False
            
            logger.info("Project structure verification passed")
            return True
            
        except Exception as e:
            logger.error(f"Project structure verification failed: {str(e)}")
            return False

def setup_nextjs_project(project_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to set up a new Next.js project
    
    Args:
        project_id: Optional project identifier. If not provided, one will be generated.
        
    Returns:
        Dict containing setup results
    """
    setup = NextJSProjectSetup()
    
    if not project_id:
        project_id = setup.generate_project_id()
    
    return setup.create_nextjs_project(project_id)