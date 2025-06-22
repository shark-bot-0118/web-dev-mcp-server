import os
import boto3
import json
from datetime import datetime
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError, NoCredentialsError
from logger import Logger
from config import Config

class S3DeployAgent:
    """S3への静的ウェブサイトデプロイを管理するエージェント"""
    
    def __init__(self):
        self.logger = Logger(log_file=Config.LOG_FILE)
        self.region = Config.AWS_DEFAULT_REGION
        
        # boto3クライアントの初期化（.env認証情報使用）
        try:
            # .envから認証情報を取得
            aws_config = {}
            if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
                aws_config.update({
                    'aws_access_key_id': Config.AWS_ACCESS_KEY_ID,
                    'aws_secret_access_key': Config.AWS_SECRET_ACCESS_KEY,
                    'region_name': self.region
                })
                self.logger.info(f"[S3DeployAgent] Using AWS credentials from .env file")
            else:
                # .envに認証情報がない場合はデフォルトプロファイルを使用
                aws_config.update({'region_name': self.region})
                self.logger.info(f"[S3DeployAgent] Using default AWS credentials (profile/IAM role)")
            
            self.s3_client = boto3.client('s3', **aws_config)
            self.s3_resource = boto3.resource('s3', **aws_config)
            self.logger.info(f"[S3DeployAgent] boto3 clients initialized for region: {self.region}")
            
        except NoCredentialsError:
            self.logger.error("[S3DeployAgent] AWS credentials not found. Please check .env file or AWS configuration.")
            raise
        except Exception as e:
            self.logger.error(f"[S3DeployAgent] Failed to initialize boto3 clients: {str(e)}")
            raise
    
    def generate_bucket_name(self, project_id: str) -> str:
        """
        バケット名を生成する
        
        Args:
            project_id (str): プロジェクトID (例: nextjs_site_c66304a5)
            
        Returns:
            str: 生成されたバケット名
        """
        # プロジェクトIDからnextjs_site_プレフィックスを除去
        # nextjs_site_c66304a5 -> c66304a5
        clean_project_id = project_id
        if project_id.startswith("nextjs_site_"):
            clean_project_id = project_id.replace("nextjs_site_", "")
            self.logger.info(f"[S3DeployAgent] Cleaned project ID: {project_id} -> {clean_project_id}")
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        bucket_name = f"website-{clean_project_id}-{timestamp}"
        
        self.logger.info(f"[S3DeployAgent] Generated bucket name: {bucket_name}")
        return bucket_name
    
    def create_s3_bucket(self, bucket_name: str) -> dict:
        """
        S3バケットを作成する
        
        Args:
            bucket_name (str): 作成するバケット名
            
        Returns:
            dict: 作成結果
        """
        try:
            self.logger.info(f"[S3DeployAgent] Creating S3 bucket: {bucket_name}")
            
            # boto3を使用してバケットを作成
            if self.region == 'us-east-1':
                response = self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                # その他のリージョンの場合はLocationConstraintを指定
                response = self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            
            self.logger.info(f"[S3DeployAgent] Bucket created successfully: {bucket_name}")
            self.logger.debug(f"[S3DeployAgent] Create bucket response: {response}")
            
            return {
                "status": "success",
                "bucket_name": bucket_name,
                "region": self.region,
                "location": response.get('Location', ''),
                "message": f"Bucket {bucket_name} created successfully"
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            
            if error_code == 'BucketAlreadyExists':
                error_detail = f"Bucket {bucket_name} already exists (owned by another account)"
            elif error_code == 'BucketAlreadyOwnedByYou':
                error_detail = f"Bucket {bucket_name} already exists and is owned by you"
            else:
                error_detail = f"Failed to create bucket {bucket_name}: {error_msg}"
            
            self.logger.error(f"[S3DeployAgent] {error_detail}")
            return {"status": "error", "error": error_detail, "error_code": error_code}
            
        except Exception as e:
            error_msg = f"Unexpected error creating bucket: {str(e)}"
            self.logger.error(f"[S3DeployAgent] {error_msg}")
            return {"status": "error", "error": error_msg}
    
    def configure_public_access(self, bucket_name: str) -> dict:
        """
        S3バケットのパブリックアクセス設定を行う（セキュア設定）
        
        Args:
            bucket_name (str): 設定対象のバケット名
            
        Returns:
            dict: 設定結果
        """
        try:
            self.logger.info(f"[S3DeployAgent] Configuring secure public access for bucket: {bucket_name}")
            
            # パブリックアクセスブロックを削除
            try:
                self.s3_client.delete_public_access_block(Bucket=bucket_name)
                self.logger.info(f"[S3DeployAgent] Public access block removed")
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchPublicAccessBlockConfiguration':
                    raise
                self.logger.info(f"[S3DeployAgent] No public access block to remove")
            
            # ウェブサイトホスティング設定（config.pyから取得）
            self.s3_client.put_bucket_website(
                Bucket=bucket_name,
                WebsiteConfiguration=Config.S3_WEBSITE_CONFIG
            )
            
            self.logger.info(f"[S3DeployAgent] Website hosting configured")
            
            # セキュアなバケットポリシーを設定（config.pyから取得）
            bucket_policy = Config.get_s3_bucket_policy(bucket_name)
            
            self.s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            
            self.logger.info(f"[S3DeployAgent] Secure bucket policy configured (GET-only access)")
            
            # CORS設定を追加（必要に応じて）
            try:
                self.s3_client.put_bucket_cors(
                    Bucket=bucket_name,
                    CORSConfiguration={'CORSRules': Config.S3_CORS_CONFIG}
                )
                self.logger.info(f"[S3DeployAgent] CORS configuration applied")
            except Exception as cors_error:
                self.logger.warning(f"[S3DeployAgent] Failed to set CORS configuration: {str(cors_error)}")
            
            # ウェブサイトURLを生成
            website_url = f"http://{bucket_name}.s3-website-{self.region}.amazonaws.com/"
            
            return {
                "status": "success",
                "bucket_name": bucket_name,
                "website_url": website_url,
                "message": "Secure public access configured successfully"
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            error_detail = f"Failed to configure public access for {bucket_name}: {error_msg}"
            
            self.logger.error(f"[S3DeployAgent] {error_detail}")
            return {"status": "error", "error": error_detail, "error_code": error_code}
            
        except Exception as e:
            error_msg = f"Unexpected error configuring public access: {str(e)}"
            self.logger.error(f"[S3DeployAgent] {error_msg}")
            return {"status": "error", "error": error_msg}
    
    def upload_website(self, bucket_name: str, source_path: str) -> dict:
        """
        ウェブサイトファイルをS3にアップロードする
        
        Args:
            bucket_name (str): アップロード先バケット名
            source_path (str): アップロード元のパス
            
        Returns:
            dict: アップロード結果
        """
        try:
            self.logger.info(f"[S3DeployAgent] Uploading website from {source_path} to {bucket_name}")
            
            if not os.path.exists(source_path):
                error_msg = f"Source path does not exist: {source_path}"
                self.logger.error(f"[S3DeployAgent] {error_msg}")
                return {"status": "error", "error": error_msg}
            
            # boto3を使用してファイルをアップロード
            uploaded_files = []
            bucket = self.s3_resource.Bucket(bucket_name)
            
            for root, dirs, files in os.walk(source_path):
                for file in files:
                    local_file_path = os.path.join(root, file)
                    
                    # S3キーを生成（相対パス）
                    relative_path = os.path.relpath(local_file_path, source_path)
                    s3_key = relative_path.replace(os.sep, '/')  # Windowsの場合の区切り文字対応
                    
                    # MIMEタイプを推測
                    content_type = self._get_content_type(file)
                    
                    try:
                        # ファイルをアップロード
                        bucket.upload_file(
                            local_file_path,
                            s3_key,
                            ExtraArgs={'ContentType': content_type} if content_type else None
                        )
                        uploaded_files.append(s3_key)
                        self.logger.debug(f"[S3DeployAgent] Uploaded: {s3_key}")
                        
                    except Exception as upload_error:
                        self.logger.warning(f"[S3DeployAgent] Failed to upload {s3_key}: {str(upload_error)}")
            
            self.logger.info(f"[S3DeployAgent] Website uploaded successfully. {len(uploaded_files)} files uploaded.")
            
            # ウェブサイトURLを生成
            website_url = f"http://{bucket_name}.s3-website-{self.region}.amazonaws.com/"
            
            return {
                "status": "success",
                "bucket_name": bucket_name,
                "website_url": website_url,
                "source_path": source_path,
                "uploaded_files": uploaded_files,
                "files_count": len(uploaded_files),
                "message": f"Website uploaded successfully to {website_url}"
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            error_detail = f"Failed to upload website to {bucket_name}: {error_msg}"
            
            self.logger.error(f"[S3DeployAgent] {error_detail}")
            return {"status": "error", "error": error_detail, "error_code": error_code}
            
        except Exception as e:
            error_msg = f"Unexpected error uploading website: {str(e)}"
            self.logger.error(f"[S3DeployAgent] {error_msg}")
            return {"status": "error", "error": error_msg}
    
    def _get_content_type(self, filename: str) -> Optional[str]:
        """
        ファイル名からContent-Typeを推測する
        
        Args:
            filename (str): ファイル名
            
        Returns:
            Optional[str]: Content-Type文字列
        """
        import mimetypes
        
        content_type, _ = mimetypes.guess_type(filename)
        
        # よく使われるファイルタイプの明示的な定義
        if not content_type:
            ext = filename.lower().split('.')[-1] if '.' in filename else ''
            content_type_map = {
                'html': 'text/html',
                'css': 'text/css',
                'js': 'application/javascript',
                'json': 'application/json',
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'gif': 'image/gif',
                'svg': 'image/svg+xml',
                'ico': 'image/x-icon',
                'woff': 'font/woff',
                'woff2': 'font/woff2',
                'ttf': 'font/ttf',
                'eot': 'application/vnd.ms-fontobject'
            }
            content_type = content_type_map.get(ext)
        
        return content_type
    
    def deploy_website(self, project_id: str, source_path: str, bucket_name: Optional[str] = None) -> dict:
        """
        ウェブサイトの完全デプロイ（バケット作成〜アップロードまで）
        セキュアなポリシー適用
        
        Args:
            project_id (str): プロジェクトID
            source_path (str): アップロード元のパス
            bucket_name (Optional[str]): バケット名（指定しない場合は自動生成）
            
        Returns:
            dict: デプロイ結果
        """
        try:
            self.logger.info(f"[S3DeployAgent] Starting secure website deployment for project: {project_id}")
            
            # バケット名が指定されていない場合は自動生成
            if not bucket_name:
                bucket_name = self.generate_bucket_name(project_id)
            
            # 1. S3バケット作成
            create_result = self.create_s3_bucket(bucket_name)
            if create_result["status"] == "error":
                return create_result
            
            # 2. セキュアなパブリックアクセス設定
            config_result = self.configure_public_access(bucket_name)
            if config_result["status"] == "error":
                return config_result
            
            # 3. ウェブサイトアップロード
            upload_result = self.upload_website(bucket_name, source_path)
            if upload_result["status"] == "error":
                return upload_result
            
            website_url = upload_result["website_url"]
            
            self.logger.info(f"[S3DeployAgent] Secure website deployment completed successfully")
            self.logger.info(f"[S3DeployAgent] Website URL: {website_url}")
            
            return {
                "status": "success",
                "project_id": project_id,
                "bucket_name": bucket_name,
                "website_url": website_url,
                "region": self.region,
                "source_path": source_path,
                "message": f"Secure website deployed successfully! Access at: {website_url}",
                "deployment_steps": {
                    "bucket_creation": create_result,
                    "public_access_config": config_result,
                    "file_upload": upload_result
                }
            }
            
        except Exception as e:
            error_msg = f"Deployment failed: {str(e)}"
            self.logger.error(f"[S3DeployAgent] {error_msg}")
            return {"status": "error", "error": error_msg}
    
    def check_deployment_status(self, bucket_name: str) -> dict:
        """
        デプロイメントの状態をチェックする
        
        Args:
            bucket_name (str): チェック対象のバケット名
            
        Returns:
            dict: 状態チェック結果
        """
        try:
            self.logger.info(f"[S3DeployAgent] Checking deployment status for bucket: {bucket_name}")
            
            # バケットの存在確認
            try:
                self.s3_client.head_bucket(Bucket=bucket_name)
                bucket_exists = True
            except ClientError as e:
                if e.response['Error']['Code'] in ['404', 'NoSuchBucket']:
                    return {
                        "status": "error",
                        "error": f"Bucket {bucket_name} does not exist"
                    }
                elif e.response['Error']['Code'] == '403':
                    return {
                        "status": "error", 
                        "error": f"Access denied to bucket {bucket_name}"
                    }
                else:
                    raise
            
            # ウェブサイト設定の確認
            try:
                website_config = self.s3_client.get_bucket_website(Bucket=bucket_name)
                website_configured = True
                index_document = website_config.get('IndexDocument', {}).get('Suffix', 'index.html')
                error_document = website_config.get('ErrorDocument', {}).get('Key', 'error.html')
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchWebsiteConfiguration':
                    website_configured = False
                    index_document = None
                    error_document = None
                else:
                    raise
            
            # バケットポリシーの確認
            try:
                policy = self.s3_client.get_bucket_policy(Bucket=bucket_name)
                public_read_enabled = True
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                    public_read_enabled = False
                else:
                    raise
            
            website_url = f"http://{bucket_name}.s3-website-{self.region}.amazonaws.com/" if website_configured else None
            
            return {
                "status": "success",
                "bucket_name": bucket_name,
                "bucket_exists": bucket_exists,
                "website_configured": website_configured,
                "public_read_enabled": public_read_enabled,
                "index_document": index_document,
                "error_document": error_document,
                "website_url": website_url,
                "region": self.region,
                "message": "Deployment status checked successfully"
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            error_detail = f"Failed to check deployment status for {bucket_name}: {error_msg}"
            
            self.logger.error(f"[S3DeployAgent] {error_detail}")
            return {"status": "error", "error": error_detail, "error_code": error_code}
            
        except Exception as e:
            error_msg = f"Failed to check deployment status: {str(e)}"
            self.logger.error(f"[S3DeployAgent] {error_msg}")
            return {"status": "error", "error": error_msg} 
