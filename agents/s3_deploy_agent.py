"""
S3 Deployment Agent - Handles AWS S3 deployment for static websites
"""

import os
import json
import boto3
import logging
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError, NoCredentialsError
from pathlib import Path
import mimetypes

from config import Config

logger = logging.getLogger(__name__)

class S3DeployAgent:
    """Agent responsible for deploying static websites to AWS S3"""
    
    def __init__(self):
        """Initialize S3 client and configuration"""
        self.config = Config()
        try:
            # Initialize S3 client
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.config.AWS_SECRET_ACCESS_KEY,
                region_name=self.config.AWS_REGION
            )
            logger.info("S3 client initialized successfully")
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS credentials.")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    def generate_bucket_name(self, project_id: str) -> str:
        """Generate a unique S3 bucket name for the project"""
        import time
        timestamp = str(int(time.time()))
        # S3 bucket names must be lowercase and contain only letters, numbers, and hyphens
        safe_project_id = project_id.lower().replace('_', '-')
        bucket_name = f"website-{safe_project_id}-{timestamp}"
        logger.info(f"Generated bucket name: {bucket_name}")
        return bucket_name
    
    def create_s3_bucket(self, bucket_name: str) -> bool:
        """Create S3 bucket with proper configuration for static website hosting"""
        try:
            # Create bucket
            if self.config.AWS_REGION == 'us-east-1':
                # us-east-1 doesn't need LocationConstraint
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.config.AWS_REGION}
                )
            
            logger.info(f"S3 bucket '{bucket_name}' created successfully")
            
            # Configure bucket for static website hosting
            self._configure_website_hosting(bucket_name)
            
            # Set bucket policy for public read access
            self._set_bucket_policy(bucket_name)
            
            # Disable block public access settings
            self._configure_public_access(bucket_name)
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'BucketAlreadyExists':
                logger.error(f"Bucket name '{bucket_name}' already exists globally")
            elif error_code == 'BucketAlreadyOwnedByYou':
                logger.info(f"Bucket '{bucket_name}' already exists and is owned by you")
                # Still configure it for website hosting
                self._configure_website_hosting(bucket_name)
                self._set_bucket_policy(bucket_name)
                self._configure_public_access(bucket_name)
                return True
            else:
                logger.error(f"Failed to create bucket: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating bucket: {e}")
            return False
    
    def _configure_website_hosting(self, bucket_name: str) -> None:
        """Configure S3 bucket for static website hosting"""
        try:
            website_configuration = {
                'IndexDocument': {'Suffix': 'index.html'},
                'ErrorDocument': {'Key': 'error.html'}
            }
            
            self.s3_client.put_bucket_website(
                Bucket=bucket_name,
                WebsiteConfiguration=website_configuration
            )
            logger.info(f"Website hosting configured for bucket '{bucket_name}'")
            
        except ClientError as e:
            logger.error(f"Failed to configure website hosting: {e}")
            raise
    
    def _set_bucket_policy(self, bucket_name: str) -> None:
        """Set bucket policy to allow public read access"""
        try:
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "PublicReadGetObject",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{bucket_name}/*"
                    }
                ]
            }
            
            policy_json = json.dumps(bucket_policy)
            self.s3_client.put_bucket_policy(Bucket=bucket_name, Policy=policy_json)
            logger.info(f"Public read policy set for bucket '{bucket_name}'")
            
        except ClientError as e:
            logger.error(f"Failed to set bucket policy: {e}")
            raise
    
    def _configure_public_access(self, bucket_name: str) -> None:
        """Configure public access block settings"""
        try:
            self.s3_client.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': False,
                    'IgnorePublicAcls': False,
                    'BlockPublicPolicy': False,
                    'RestrictPublicBuckets': False
                }
            )
            logger.info(f"Public access configured for bucket '{bucket_name}'")
            
        except ClientError as e:
            logger.error(f"Failed to configure public access: {e}")
            raise
    
    def get_mime_type(self, file_path: str) -> str:
        """Get MIME type for a file"""
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            return 'application/octet-stream'
        return mime_type
    
    def upload_directory_to_s3(self, local_directory: str, bucket_name: str) -> bool:
        """Upload entire directory to S3 bucket"""
        try:
            local_path = Path(local_directory)
            if not local_path.exists():
                logger.error(f"Local directory does not exist: {local_directory}")
                return False
            
            uploaded_files = 0
            failed_files = 0
            
            # Walk through all files in the directory
            for file_path in local_path.rglob('*'):
                if file_path.is_file():
                    # Calculate relative path for S3 key
                    relative_path = file_path.relative_to(local_path)
                    s3_key = str(relative_path).replace('\\', '/')  # Ensure forward slashes
                    
                    try:
                        # Get MIME type
                        content_type = self.get_mime_type(str(file_path))
                        
                        # Upload file
                        with open(file_path, 'rb') as file_data:
                            self.s3_client.put_object(
                                Bucket=bucket_name,
                                Key=s3_key,
                                Body=file_data,
                                ContentType=content_type
                            )
                        
                        uploaded_files += 1
                        logger.info(f"Uploaded: {s3_key} (Content-Type: {content_type})")
                        
                    except Exception as e:
                        failed_files += 1
                        logger.error(f"Failed to upload {file_path}: {e}")
            
            logger.info(f"Upload complete. {uploaded_files} files uploaded, {failed_files} failed")
            return failed_files == 0
            
        except Exception as e:
            logger.error(f"Failed to upload directory: {e}")
            return False
    
    def get_website_url(self, bucket_name: str) -> str:
        """Get the website URL for the S3 bucket"""
        region = self.config.AWS_REGION
        if region == 'us-east-1':
            return f"http://{bucket_name}.s3-website-us-east-1.amazonaws.com"
        else:
            return f"http://{bucket_name}.s3-website-{region}.amazonaws.com"
    
    def verify_deployment(self, bucket_name: str) -> Dict[str, Any]:
        """Verify that the deployment was successful"""
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=bucket_name)
            
            # Check if index.html exists
            try:
                self.s3_client.head_object(Bucket=bucket_name, Key='index.html')
                index_exists = True
            except ClientError:
                index_exists = False
            
            # Get website configuration
            try:
                website_config = self.s3_client.get_bucket_website(Bucket=bucket_name)
                website_enabled = True
            except ClientError:
                website_enabled = False
            
            # Get bucket policy
            try:
                self.s3_client.get_bucket_policy(Bucket=bucket_name)
                policy_exists = True
            except ClientError:
                policy_exists = False
            
            website_url = self.get_website_url(bucket_name)
            
            verification_result = {
                'bucket_exists': True,
                'index_exists': index_exists,
                'website_enabled': website_enabled,
                'policy_exists': policy_exists,
                'website_url': website_url,
                'status': 'success' if all([index_exists, website_enabled, policy_exists]) else 'partial'
            }
            
            logger.info(f"Deployment verification: {verification_result}")
            return verification_result
            
        except ClientError as e:
            logger.error(f"Deployment verification failed: {e}")
            return {
                'bucket_exists': False,
                'status': 'failed',
                'error': str(e)
            }
    
    def deploy_website(self, project_id: str, build_directory: str, bucket_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete deployment workflow
        
        Args:
            project_id: Unique identifier for the project
            build_directory: Path to the built website files
            bucket_name: Optional custom bucket name
            
        Returns:
            Dict containing deployment results
        """
        try:
            # Generate bucket name if not provided
            if not bucket_name:
                bucket_name = self.generate_bucket_name(project_id)
            
            logger.info(f"Starting deployment for project '{project_id}' to bucket '{bucket_name}'")
            
            # Create S3 bucket
            if not self.create_s3_bucket(bucket_name):
                return {
                    'success': False,
                    'error': 'Failed to create S3 bucket',
                    'bucket_name': bucket_name
                }
            
            # Upload files
            if not self.upload_directory_to_s3(build_directory, bucket_name):
                return {
                    'success': False,
                    'error': 'Failed to upload files to S3',
                    'bucket_name': bucket_name
                }
            
            # Verify deployment
            verification = self.verify_deployment(bucket_name)
            
            if verification['status'] == 'success':
                website_url = verification['website_url']
                logger.info(f"Deployment successful! Website available at: {website_url}")
                
                return {
                    'success': True,
                    'bucket_name': bucket_name,
                    'website_url': website_url,
                    'verification': verification
                }
            else:
                return {
                    'success': False,
                    'error': 'Deployment verification failed',
                    'bucket_name': bucket_name,
                    'verification': verification
                }
                
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'bucket_name': bucket_name if 'bucket_name' in locals() else None
            }

def deploy_to_s3(project_id: str, build_directory: str, bucket_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function for S3 deployment
    
    Args:
        project_id: Unique identifier for the project
        build_directory: Path to the built website files  
        bucket_name: Optional custom bucket name
        
    Returns:
        Dict containing deployment results
    """
    agent = S3DeployAgent()
    return agent.deploy_website(project_id, build_directory, bucket_name)