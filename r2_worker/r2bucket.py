import os
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()

class R2Bucket:
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        account_id = os.getenv("R2_ACCOUNT_ID")
        access_key = os.getenv("R2_ACCESS_KEY_ID")
        secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
        if not all([account_id, access_key, secret_key]):
            raise ValueError("Missing R2 credentials in environment variables")
        
        self.s3 = boto3.client(
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
            region_name="auto"
        )

    def upload_file(self, file_path, key_name):
        self.s3.upload_file(file_path, self.bucket_name, key_name)
        print(f"Uploaded {file_path} as {key_name}")

    def delete_file(self, key_name):
        self.s3.delete_object(
            Bucket=self.bucket_name,
            Key=key_name
        )
        print(f"Deleted {key_name} from {self.bucket_name}")


    def generate_presigned_url(self, key_name, expiration=3600):
        try:
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key_name},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None
        
    def generete_download_url(self, key_name, expiration=3600):

        filename = key_name.split("/")[-1]
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

        try:
            url = self.s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": key_name,
                    "ResponseContentDisposition": f'attachment; filename="{filename}"'
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None

