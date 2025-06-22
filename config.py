import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "static_site_output")
    TEMPLATE_DIR = os.getenv("TEMPLATE_DIR", "templates")
    LOG_FILE = os.getenv("LOG_FILE", "app.log")
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-1")
    
    # S3 Website Hosting Configuration
    S3_WEBSITE_CONFIG = {
        'IndexDocument': {'Suffix': 'index.html'},
        'ErrorDocument': {'Key': 'error.html'}
    }
    
    # S3 Bucket Policy Template (セキュアなパブリック読み取り専用)
    @staticmethod
    def get_s3_bucket_policy(bucket_name: str) -> dict:
        """
        セキュアなS3バケットポリシーを取得
        - インターネットからのGET（読み取り）のみ許可
        - IAMユーザーからの操作は許可
        - 匿名ユーザーのPUT、DELETE、その他の操作は明示的に拒否
        """
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadOnlyAccess",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": [
                        "s3:GetObject"
                    ],
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                },
                {
                    "Sid": "AllowIAMUserAccess",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": "*"
                    },
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:PutObjectAcl",
                        "s3:DeleteObject",
                        "s3:DeleteObjectVersion",
                        "s3:ListBucket",
                        "s3:GetBucketLocation",
                        "s3:GetBucketPolicy",
                        "s3:PutBucketPolicy",
                        "s3:PutBucketWebsite",
                        "s3:GetBucketWebsite"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{bucket_name}",
                        f"arn:aws:s3:::{bucket_name}/*"
                    ],
                    "Condition": {
                        "StringEquals": {
                            "aws:PrincipalType": "User"
                        }
                    }
                },
                {
                    "Sid": "DenyAnonymousDestructiveOperations",
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": [
                        "s3:PutObject",
                        "s3:PutObjectAcl",
                        "s3:DeleteObject",
                        "s3:DeleteObjectVersion",
                        "s3:PutBucketPolicy",
                        "s3:DeleteBucketPolicy",
                        "s3:PutBucketAcl",
                        "s3:PutBucketVersioning",
                        "s3:PutBucketLogging",
                        "s3:PutBucketWebsite",
                        "s3:DeleteBucket"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{bucket_name}",
                        f"arn:aws:s3:::{bucket_name}/*"
                    ],
                    "Condition": {
                        "StringNotEquals": {
                            "aws:PrincipalType": ["User", "Root"]
                        }
                    }
                }
            ]
        }
    
    # S3 CORS設定（必要に応じて）
    S3_CORS_CONFIG = [
        {
            'AllowedHeaders': ['*'],
            'AllowedMethods': ['GET'],
            'AllowedOrigins': ['*'],
            'ExposeHeaders': ['ETag'],
            'MaxAgeSeconds': 3000
        }
    ] 
