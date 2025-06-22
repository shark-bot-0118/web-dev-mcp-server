# Webページホスト処理のワークフロー実行用のテストスクリプト
# 事前に生成したページをS3にアップロードできます
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from graph.s3_deploy_workflow import run_s3_deploy_workflow

print("[INFO]test_s3_workflow.py start")

# プロジェクト生成ディレクトリに生成されたプロジェクト名を入力(例：next_site_xxxxxxxx)
project_id =input("project_id:")
# 生成したいS3バケット名を入力 
# 無入力の場合はデフォルトで自動的に設定されます
bucket_name =input("bucket_name:")

print(f'[INFO]project_id : {project_id} bucket_name : {bucket_name}')
result = run_s3_deploy_workflow(project_id,bucket_name)
print(result)
