from mcp.server.fastmcp import FastMCP
from graph.workflow import run_workflow
from graph.s3_deploy_workflow import run_s3_deploy_workflow, check_s3_deployment_status
from logger import Logger
from config import Config
from typing import Optional

logger = Logger(log_file=Config.LOG_FILE)
mcp = FastMCP("webdev")

@mcp.tool(
    description="Generates static websites automatically from natural language instructions. The user_instruction should ideally include: page layouts/design concepts, number of pages needed, and specific content for each page (text, images, functionality). For example: 'Create a 3-page portfolio site with a modern dark theme, including home page with hero section, about page with skills, and contact page with form'.",
    name="create_website"
)
def create_website(user_instruction: str) -> dict:
    """
    Automatically generates static websites from natural language instructions.
    Args:
        user_instruction (str): Detailed instructions for website creation including page layouts, 
                               number of pages, content specifications, design preferences, and functionality requirements.
                               Best results when including: layout concepts, visual design preferences, 
                               page structure, content details, and any specific features needed.
    Returns:
        dict: Generation results including file paths, project ID, and preview information
    """
    logger.info(f"[create_website] user_instruction: {user_instruction}")
    result = run_workflow(user_instruction)
    logger.debug(f"[create_website] result: {result}")
    return result

@mcp.tool(
    description="Builds a Next.js project and deploys it as a static website to AWS S3. Automatically configures S3 bucket for public website hosting with proper permissions. If bucket_name is not specified, generates a unique name automatically in format: website-{processed_project_id}-{timestamp}.",
    name="deploy_to_s3"
)
def deploy_to_s3(project_id: str, bucket_name: Optional[str] = None) -> dict:
    """
    Builds and deploys a Next.js project as a static website to AWS S3.
    Args:
        project_id (str): The project identifier for the target Next.js project to deploy
        bucket_name (Optional[str]): S3 bucket name for deployment. If not provided, 
                                   auto-generates as: website-{processed_project_id}-{yyyymmddhhmmss}
    Returns:
        dict: Deployment results including bucket name, website URL, build status, and deployment details
    """
    logger.info(f"[deploy_to_s3] project_id: {project_id}, bucket_name: {bucket_name}")
    result = run_s3_deploy_workflow(project_id, bucket_name)
    logger.debug(f"[deploy_to_s3] result: {result}")
    return result

@mcp.tool(
    description="Verifies the deployment status of an S3 bucket configured for static website hosting. Checks bucket existence, public access configuration, website hosting settings, and validates that the site is publicly accessible via the S3 website endpoint.",
    name="check_s3_deployment"
)
def check_s3_deployment(bucket_name: str) -> dict:
    """
    Checks and validates the deployment status of an S3 static website.
    Args:
        bucket_name (str): The name of the S3 bucket to check for deployment status
    Returns:
        dict: Comprehensive deployment status including bucket existence, public access settings, 
              website configuration, accessibility status, and website URL if available
    """
    logger.info(f"[check_s3_deployment] bucket_name: {bucket_name}")
    result = check_s3_deployment_status(bucket_name)
    logger.debug(f"[check_s3_deployment] result: {result}")
    return result

if __name__ == "__main__":
    logger.info("Starting MCP server for web development")
    mcp.run()