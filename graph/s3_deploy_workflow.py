"""
S3 Deployment Workflow for Web Development Agent
"""

import logging
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from agents.build_agent import BuildAgent
from agents.s3_deploy_agent import S3DeployAgent
from config import Config

logger = logging.getLogger(__name__)

def prepare_for_deployment(state: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare the project for S3 deployment"""
    try:
        logger.info("Preparing project for S3 deployment...")
        
        build_agent = BuildAgent()
        
        # Ensure the project is built and ready for static export
        result = build_agent.prepare_for_static_export(
            state["project_path"],
            state["project_id"]
        )
        
        if result["success"]:
            state["build_prepared"] = True
            state["static_export_path"] = result["export_path"]
            state["status"] = "prepared"
            logger.info("Project prepared for deployment successfully")
        else:
            error_msg = f"Deployment preparation failed: {result.get('error', 'Unknown error')}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            state["status"] = "failed"
        
        return state
        
    except Exception as e:
        error_msg = f"Deployment preparation failed: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["status"] = "failed"
        return state

def deploy_to_s3(state: Dict[str, Any]) -> Dict[str, Any]:
    """Deploy the static website to AWS S3"""
    try:
        logger.info("Deploying website to AWS S3...")
        
        s3_agent = S3DeployAgent()
        
        # Deploy to S3
        result = s3_agent.deploy_website(
            state["project_id"],
            state["static_export_path"],
            state.get("bucket_name")
        )
        
        if result["success"]:
            state["deployment_result"] = result
            state["bucket_name"] = result["bucket_name"]
            state["website_url"] = result["website_url"]
            state["status"] = "deployed"
            logger.info(f"Deployment successful! Website URL: {result['website_url']}")
        else:
            error_msg = f"S3 deployment failed: {result.get('error', 'Unknown error')}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            state["status"] = "failed"
        
        return state
        
    except Exception as e:
        error_msg = f"S3 deployment failed: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["status"] = "failed"
        return state

def verify_deployment(state: Dict[str, Any]) -> Dict[str, Any]:
    """Verify that the deployment was successful"""
    try:
        logger.info("Verifying S3 deployment...")
        
        s3_agent = S3DeployAgent()
        
        # Verify deployment
        verification = s3_agent.verify_deployment(state["bucket_name"])
        
        state["verification_result"] = verification
        
        if verification["status"] == "success":
            state["status"] = "verified"
            logger.info("Deployment verification successful")
        else:
            state["status"] = "deployment_issues"
            logger.warning(f"Deployment verification found issues: {verification}")
        
        return state
        
    except Exception as e:
        error_msg = f"Deployment verification failed: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["status"] = "verification_failed"
        return state

def finalize_deployment(state: Dict[str, Any]) -> Dict[str, Any]:
    """Finalize the deployment workflow"""
    try:
        logger.info("Finalizing deployment workflow...")
        
        if state["status"] in ["verified", "deployment_issues"]:
            state["status"] = "deployment_completed"
            logger.info("S3 deployment workflow completed!")
        else:
            state["status"] = "deployment_failed"
            logger.error("S3 deployment workflow failed")
        
        return state
        
    except Exception as e:
        error_msg = f"Deployment finalization failed: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["status"] = "deployment_failed"
        return state

def create_s3_deploy_workflow() -> CompiledStateGraph:
    """Create and compile the S3 deployment workflow graph"""
    
    # Create the workflow graph
    workflow = StateGraph(dict)
    
    # Add nodes
    workflow.add_node("prepare", prepare_for_deployment)
    workflow.add_node("deploy", deploy_to_s3)
    workflow.add_node("verify", verify_deployment)
    workflow.add_node("finalize", finalize_deployment)
    
    # Define the workflow edges
    workflow.set_entry_point("prepare")
    workflow.add_edge("prepare", "deploy")
    workflow.add_edge("deploy", "verify")
    workflow.add_edge("verify", "finalize")
    workflow.add_edge("finalize", END)
    
    # Compile the workflow
    return workflow.compile()

def run_s3_deployment(project_id: str, project_path: str, bucket_name: str = None) -> Dict[str, Any]:
    """
    Run the S3 deployment workflow
    
    Args:
        project_id: Unique identifier for the project
        project_path: Path to the Next.js project
        bucket_name: Optional custom S3 bucket name
        
    Returns:
        Dict containing deployment results
    """
    try:
        logger.info(f"Starting S3 deployment workflow for project: {project_id}")
        
        # Initialize deployment state
        initial_state = {
            "project_id": project_id,
            "project_path": project_path,
            "bucket_name": bucket_name,
            "build_prepared": False,
            "static_export_path": "",
            "deployment_result": {},
            "verification_result": {},
            "website_url": "",
            "errors": [],
            "status": "initialized"
        }
        
        # Create and run deployment workflow
        workflow = create_s3_deploy_workflow()
        final_state = workflow.invoke(initial_state)
        
        # Log final results
        if final_state["status"] == "deployment_completed":
            logger.info("S3 deployment workflow completed successfully!")
            logger.info(f"Website URL: {final_state.get('website_url', 'Not available')}")
        else:
            logger.error(f"Deployment workflow completed with status: {final_state['status']}")
            if final_state["errors"]:
                logger.error(f"Errors encountered: {final_state['errors']}")
        
        return final_state
        
    except Exception as e:
        error_msg = f"S3 deployment workflow failed: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "deployment_failed",
            "error": error_msg,
            "errors": [error_msg]
        }