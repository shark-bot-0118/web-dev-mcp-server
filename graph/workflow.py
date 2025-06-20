"""
Main Workflow Orchestration for Web Development Agent
"""

import logging
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from agents.instruction_analysis import InstructionAnalysisAgent
from agents.step_generation import StepGenerationAgent
from agents.page_development import PageDevelopmentAgent
from agents.review_page import ReviewPageAgent
from agents.execution import ExecutionAgent
from agents.build_agent import BuildAgent
from config import Config

logger = logging.getLogger(__name__)

class WorkflowState:
    """State management for the web development workflow"""
    
    def __init__(self):
        self.instruction: str = ""
        self.analysis: Dict[str, Any] = {}
        self.layout: Dict[str, Any] = {}
        self.steps: List[Dict[str, Any]] = []
        self.pages: List[Dict[str, Any]] = []
        self.project_id: str = ""
        self.project_path: str = ""
        self.server_info: Dict[str, Any] = {}
        self.build_result: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.status: str = "initialized"
        self.current_step: int = 0

def analyze_instruction(state: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze user instruction and extract requirements"""
    try:
        logger.info("Starting instruction analysis...")
        agent = InstructionAnalysisAgent()
        
        analysis = agent.analyze_instruction(state["instruction"])
        
        state["analysis"] = analysis
        state["status"] = "analyzed"
        state["current_step"] = 1
        
        logger.info(f"Instruction analysis completed: {analysis.get('website_type', 'Unknown')}")
        return state
        
    except Exception as e:
        error_msg = f"Instruction analysis failed: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["status"] = "failed"
        return state

def generate_steps_and_layout(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate development steps and layout configuration"""
    try:
        logger.info("Generating steps and layout...")
        agent = StepGenerationAgent()
        
        # Generate layout and steps
        result = agent.generate_layout_with_quality_control(state["analysis"])
        
        if result["success"]:
            state["layout"] = result["layout"]
            state["steps"] = result.get("steps", [])
            state["status"] = "planned"
            state["current_step"] = 2
            logger.info("Steps and layout generation completed successfully")
        else:
            error_msg = f"Layout generation failed: {result.get('error', 'Unknown error')}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            state["status"] = "failed"
        
        return state
        
    except Exception as e:
        error_msg = f"Step generation failed: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["status"] = "failed"
        return state

def develop_pages(state: Dict[str, Any]) -> Dict[str, Any]:
    """Develop individual pages with quality control"""
    try:
        logger.info("Starting page development...")
        
        page_dev_agent = PageDevelopmentAgent()
        review_agent = ReviewPageAgent()
        
        pages = state["analysis"].get("pages", [])
        layout = state["layout"]
        developed_pages = []
        
        for page_info in pages:
            logger.info(f"Developing page: {page_info['name']}")
            
            # Develop page with quality control
            page_result = page_dev_agent.develop_page_with_quality_control(
                page_info, layout
            )
            
            if page_result["success"]:
                developed_pages.append(page_result["page"])
                logger.info(f"Page '{page_info['name']}' developed successfully")
            else:
                error_msg = f"Failed to develop page '{page_info['name']}': {page_result.get('error', 'Unknown error')}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
        
        if developed_pages:
            state["pages"] = developed_pages
            state["status"] = "developed"
            state["current_step"] = 3
            logger.info(f"Page development completed. {len(developed_pages)} pages created.")
        else:
            state["status"] = "failed"
            state["errors"].append("No pages were successfully developed")
        
        return state
        
    except Exception as e:
        error_msg = f"Page development failed: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["status"] = "failed"
        return state

def setup_and_execute(state: Dict[str, Any]) -> Dict[str, Any]:
    """Setup Next.js project and start development server"""
    try:
        logger.info("Setting up Next.js project and starting server...")
        
        execution_agent = ExecutionAgent()
        
        # Setup and start the project
        result = execution_agent.setup_and_start_project(
            state["analysis"], 
            state["layout"], 
            state["pages"]
        )
        
        if result["success"]:
            state["project_id"] = result["project_id"]
            state["project_path"] = result["project_path"]
            state["server_info"] = result["server_info"]
            state["status"] = "running"
            state["current_step"] = 4
            logger.info(f"Project setup completed. Server running at: {result['server_info'].get('url', 'Unknown')}")
        else:
            error_msg = f"Project setup failed: {result.get('error', 'Unknown error')}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            state["status"] = "failed"
        
        return state
        
    except Exception as e:
        error_msg = f"Project setup failed: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["status"] = "failed"
        return state

def build_project(state: Dict[str, Any]) -> Dict[str, Any]:
    """Build the Next.js project for deployment"""
    try:
        logger.info("Building project for deployment...")
        
        build_agent = BuildAgent()
        
        # Build the project
        result = build_agent.build_project(
            state["project_path"],
            state["project_id"]
        )
        
        if result["success"]:
            state["build_result"] = result
            state["status"] = "built"
            state["current_step"] = 5
            logger.info("Project build completed successfully")
        else:
            error_msg = f"Project build failed: {result.get('error', 'Unknown error')}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            state["status"] = "failed"
        
        return state
        
    except Exception as e:
        error_msg = f"Project build failed: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["status"] = "failed"
        return state

def finalize_workflow(state: Dict[str, Any]) -> Dict[str, Any]:
    """Finalize the workflow and prepare final response"""
    try:
        logger.info("Finalizing workflow...")
        
        if state["status"] == "built":
            state["status"] = "completed"
            logger.info("Workflow completed successfully!")
        else:
            state["status"] = "completed_with_errors"
            logger.warning("Workflow completed with errors")
        
        return state
        
    except Exception as e:
        error_msg = f"Workflow finalization failed: {str(e)}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["status"] = "failed"
        return state

def create_workflow() -> CompiledStateGraph:
    """Create and compile the workflow graph"""
    
    # Create the workflow graph
    workflow = StateGraph(dict)
    
    # Add nodes
    workflow.add_node("analyze", analyze_instruction)
    workflow.add_node("plan", generate_steps_and_layout)
    workflow.add_node("develop", develop_pages)
    workflow.add_node("execute", setup_and_execute)
    workflow.add_node("build", build_project)
    workflow.add_node("finalize", finalize_workflow)
    
    # Define the workflow edges
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "plan")
    workflow.add_edge("plan", "develop")
    workflow.add_edge("develop", "execute")
    workflow.add_edge("execute", "build")
    workflow.add_edge("build", "finalize")
    workflow.add_edge("finalize", END)
    
    # Compile the workflow
    return workflow.compile()

def run_workflow(instruction: str) -> Dict[str, Any]:
    """
    Run the complete website creation workflow
    
    Args:
        instruction: User's natural language instruction for website creation
        
    Returns:
        Dict containing workflow results and project information
    """
    try:
        logger.info(f"Starting website creation workflow with instruction: {instruction[:100]}...")
        
        # Initialize workflow state
        initial_state = {
            "instruction": instruction,
            "analysis": {},
            "layout": {},
            "steps": [],
            "pages": [],
            "project_id": "",
            "project_path": "",
            "server_info": {},
            "build_result": {},
            "errors": [],
            "status": "initialized",
            "current_step": 0
        }
        
        # Create and run workflow
        workflow = create_workflow()
        final_state = workflow.invoke(initial_state)
        
        # Log final results
        if final_state["status"] == "completed":
            logger.info("Website creation workflow completed successfully!")
        else:
            logger.error(f"Workflow completed with status: {final_state['status']}")
            if final_state["errors"]:
                logger.error(f"Errors encountered: {final_state['errors']}")
        
        return final_state
        
    except Exception as e:
        error_msg = f"Workflow execution failed: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "failed",
            "error": error_msg,
            "errors": [error_msg]
        }