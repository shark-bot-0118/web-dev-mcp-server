import os
from typing import Optional
from agents.build_agent import BuildAgent
from agents.s3_deploy_agent import S3DeployAgent
from logger import Logger
from config import Config

def run_s3_deploy_workflow(project_id: str, bucket_name: Optional[str] = None) -> dict:
    """
    S3デプロイワークフロー
    1. プロジェクトのビルド
    2. S3へのデプロイ
    
    Args:
        project_id (str): デプロイ対象のプロジェクトID
        bucket_name (Optional[str]): S3バケット名（指定しない場合は自動生成）
        
    Returns:
        dict: デプロイ結果
    """
    logger = Logger(log_file=Config.LOG_FILE)
    
    try:
        logger.info(f"[S3DeployWorkflow] Starting S3 deploy workflow for project: {project_id}")
        
        # Step 1: ビルドエージェントでプロジェクトをビルド
        logger.info("[S3DeployWorkflow] Step 1: Building project")
        build_agent = BuildAgent()
        
        # 静的エクスポート用の設定を準備
        prepare_result = build_agent.prepare_for_static_export(project_id)
        if prepare_result["status"] == "error":
            logger.error(f"[S3DeployWorkflow] Failed to prepare static export: {prepare_result['error']}")
            return prepare_result
        
        logger.info("[S3DeployWorkflow] Static export configuration prepared")
        
        # プロジェクトをビルド
        build_result = build_agent.build_project(project_id)
        if build_result["status"] == "error":
            logger.error(f"[S3DeployWorkflow] Build failed: {build_result['error']}")
            return build_result
        
        logger.info(f"[S3DeployWorkflow] Build completed successfully")
        logger.debug(f"[S3DeployWorkflow] Build result: {build_result}")
        
        # ビルドエージェントが既に出力パスを決定済み
        project_path = build_result["project_path"]
        static_output_path = build_result["build_output_path"]
        
        # ビルド出力パスの存在確認
        if not os.path.exists(static_output_path):
            error_msg = f"Build output directory not found: {static_output_path}"
            logger.error(f"[S3DeployWorkflow] {error_msg}")
            return {"status": "error", "error": error_msg}
        
        logger.info(f"[S3DeployWorkflow] Using build output path: {static_output_path}")
        
        # Step 2: S3デプロイエージェントでS3にデプロイ
        logger.info("[S3DeployWorkflow] Step 2: Deploying to S3")
        s3_agent = S3DeployAgent()
        
        deploy_result = s3_agent.deploy_website(
            project_id=project_id,
            source_path=static_output_path,
            bucket_name=bucket_name
        )
        
        if deploy_result["status"] == "error":
            logger.error(f"[S3DeployWorkflow] S3 deployment failed: {deploy_result['error']}")
            return deploy_result
        
        logger.info(f"[S3DeployWorkflow] S3 deployment completed successfully")
        logger.info(f"[S3DeployWorkflow] Website URL: {deploy_result['website_url']}")
        
        # 最終結果をまとめる
        final_result = {
            "status": "success",
            "project_id": project_id,
            "bucket_name": deploy_result["bucket_name"],
            "website_url": deploy_result["website_url"],
            "region": deploy_result["region"],
            "project_path": project_path,
            "build_output_path": static_output_path,
            "message": f"S3 deployment completed successfully! Website is available at: {deploy_result['website_url']}",
            "workflow_steps": {
                "1_static_export_preparation": prepare_result,
                "2_build": build_result,
                "3_s3_deployment": deploy_result
            }
        }
        
        logger.info("[S3DeployWorkflow] *** S3 DEPLOY WORKFLOW COMPLETED SUCCESSFULLY ***")
        logger.info(f"[S3DeployWorkflow] Project: {project_id}")
        logger.info(f"[S3DeployWorkflow] S3 Bucket: {deploy_result['bucket_name']}")
        logger.info(f"[S3DeployWorkflow] Website URL: {deploy_result['website_url']}")
        logger.info("[S3DeployWorkflow] *** DEPLOYMENT COMPLETE ***")
        
        return final_result
        
    except Exception as e:
        error_msg = f"S3 deploy workflow failed: {str(e)}"
        logger.error(f"[S3DeployWorkflow] {error_msg}")
        return {"status": "error", "error": error_msg}

def check_s3_deployment_status(bucket_name: str) -> dict:
    """
    S3デプロイメントの状態をチェックする
    
    Args:
        bucket_name (str): チェック対象のバケット名
        
    Returns:
        dict: 状態チェック結果
    """
    logger = Logger(log_file=Config.LOG_FILE)
    
    try:
        logger.info(f"[S3DeployWorkflow] Checking deployment status for bucket: {bucket_name}")
        
        s3_agent = S3DeployAgent()
        status_result = s3_agent.check_deployment_status(bucket_name)
        
        logger.info(f"[S3DeployWorkflow] Status check completed")
        
        return status_result
        
    except Exception as e:
        error_msg = f"Failed to check deployment status: {str(e)}"
        logger.error(f"[S3DeployWorkflow] {error_msg}")
        return {"status": "error", "error": error_msg} 
