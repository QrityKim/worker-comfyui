import os
import boto3
from botocore.client import Config

# 1. 환경 변수 로드 및 확인
ENDPOINT_URL = os.environ.get("https://c5731df4e6f9d7b2c586ee56d2936da0.r2.cloudflarestorage.com")
ACCESS_KEY = os.environ.get("59bf733b612098e892e648c38a8b0862")
SECRET_KEY = os.environ.get("ca2975889267e08cbddb5b4133bf947709f9abea840286c45460d866cecaa20b")
BUCKET_NAME = os.environ.get("civitai-model")
LOCAL_DIR = "/comfyui/models"  # ComfyUI 모델 경로

print(f"--- [R2 Sync Config] ---")
print(f"Endpoint: {ENDPOINT_URL}")
print(f"Bucket: {BUCKET_NAME}")
print(f"Target Dir: {LOCAL_DIR}")
# ACCESS_KEY와 SECRET_KEY는 보안상 일부만 출력하거나 출력하지 않습니다.
print(f"Access Key provided: {'Yes' if ACCESS_KEY else 'No'}")
print(f"Secret Key provided: {'Yes' if SECRET_KEY else 'No'}")
print("------------------------")

if not all([ENDPOINT_URL, ACCESS_KEY, SECRET_KEY, BUCKET_NAME]):
    print("ERROR: Missing required environment variables for R2 sync.")
    # 필수 변수가 없으면 스크립트 종료 (원한다면 exit(1)로 컨테이너를 실패시킬 수도 있음)
    exit(1) 

# 2. Boto3 클라이언트 설정
s3 = boto3.client(
    's3',
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    config=Config(signature_version='s3v4'),
    region_name='auto'  # Cloudflare R2는 보통 'auto'를 사용
)

# 3. 다운로드 함수 정의
def download_dir(bucket_name, local_path):
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket_name):
        if 'Contents' not in page:
            continue
        for obj in page['Contents']:
            s3_key = obj['Key']
            local_file_path = os.path.join(local_path, s3_key)
            local_file_dir = os.path.dirname(local_file_path)

            # 로컬 디렉토리가 없으면 생성
            if not os.path.exists(local_file_dir):
                os.makedirs(local_file_dir)

            # 파일이 이미 존재하고 크기가 같으면 스킵 (간단한 동기화 로직)
            if os.path.exists(local_file_path):
                if os.path.getsize(local_file_path) == obj['Size']:
                    print(f"Skipping (already exists): {s3_key}")
                    continue

            print(f"Downloading: {s3_key} -> {local_file_path}")
            try:
                s3.download_file(bucket_name, s3_key, local_file_path)
            except Exception as e:
                print(f"ERROR downloading {s3_key}: {e}")

# 4. 실행
print("Starting R2 sync...")
try:
    download_dir(BUCKET_NAME, LOCAL_DIR)
    print("R2 sync finished successfully.")
except Exception as e:
    print(f"FATAL ERROR during R2 sync: {e}")
    # 필요시 exit(1) 추가
