import os
import shutil
from abc import ABC, abstractmethod
from typing import BinaryIO
from fastapi import HTTPException, status
from loguru import logger

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    ClientError = None

from src.config import settings


class StorageStrategy(ABC):
    @abstractmethod
    async def upload_file(self, file_object: BinaryIO, target_path: str) -> str:
        pass

    @abstractmethod
    async def delete_file(self, target_path: str) -> None:
        pass


class AWSS3Storage(StorageStrategy):
    def __init__(self):
        if not boto3:
            raise RuntimeError("boto3 package missing. Run 'uv add boto3'.")
        
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.STORAGE_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.STORAGE_AWS_SECRET_ACCESS_KEY,
            region_name=settings.STORAGE_AWS_REGION,
        )
        self.bucket_name = settings.STORAGE_BUCKET_NAME

    async def upload_file(self, file_object: BinaryIO, target_path: str) -> str:
        try:
            file_object.seek(0)
            self.s3_client.upload_fileobj(
                file_object,
                self.bucket_name,
                target_path
            )
            return target_path
        except ClientError as e:
            logger.error(f"AWS S3 Upload Failure for path {target_path}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cloud storage driver rejected file payload upload pipeline."
            )

    async def delete_file(self, target_path: str) -> None:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=target_path)
        except ClientError as e:
            logger.error(f"AWS S3 Deletion Failure for path {target_path}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cloud storage driver rejected file eviction lifecycle event."
            )


class DigitalOceanSpacesStorage(StorageStrategy):
    def __init__(self):
        if not boto3:
            raise RuntimeError("boto3 package missing. Run 'uv add boto3'.")
        
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=f"https://{settings.STORAGE_DO_REGION}.digitaloceanspaces.com",
            aws_access_key_id=settings.STORAGE_DO_ACCESS_KEY_ID,
            aws_secret_access_key=settings.STORAGE_DO_SECRET_ACCESS_KEY,
            region_name=settings.STORAGE_DO_REGION,
        )
        self.bucket_name = settings.STORAGE_BUCKET_NAME

    async def upload_file(self, file_object: BinaryIO, target_path: str) -> str:
        try:
            file_object.seek(0)
            self.s3_client.upload_fileobj(
                file_object,
                self.bucket_name,
                target_path,
                ExtraArgs={"ACL": "private"}
            )
            return target_path
        except ClientError as e:
            logger.error(f"DigitalOcean Spaces Upload Failure for path {target_path}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cloud storage space provider rejected payload injection."
            )

    async def delete_file(self, target_path: str) -> None:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=target_path)
        except ClientError as e:
            logger.error(f"DigitalOcean Spaces Deletion Failure for path {target_path}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cloud storage space provider rejected file eviction tracking."
            )


class LocalStorage(StorageStrategy):
    def __init__(self):
        self.base_dir = settings.STORAGE_LOCAL_BASE_DIR or "storage_vault"
        os.makedirs(self.base_dir, exist_ok=True)

    async def upload_file(self, file_object: BinaryIO, target_path: str) -> str:
        try:
            full_destination_path = os.path.join(self.base_dir, target_path)
            os.makedirs(os.path.dirname(full_destination_path), exist_ok=True)
            
            file_object.seek(0)
            with open(full_destination_path, "wb") as buffer:
                shutil.copyfileobj(file_object, buffer)
                
            return target_path
        except Exception as e:
            logger.error(f"Local Storage Write Failure for path {target_path}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="On-premise file allocation pipeline encountered a hardware/write exception."
            )

    async def delete_file(self, target_path: str) -> None:
        try:
            full_destination_path = os.path.join(self.base_dir, target_path)
            if os.path.exists(full_destination_path):
                os.remove(full_destination_path)
        except Exception as e:
            logger.error(f"Local Storage Deletion Failure for path {target_path}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="On-premise file eviction lifecycle encountered a filesystem lock violation."
            )


class StorageService:
    def __init__(self):
        self.provider = settings.STORAGE_PROVIDER.lower()
        
        if self.provider == "aws":
            self._strategy = AWSS3Storage()
        elif self.provider == "digitalocean":
            self._strategy = DigitalOceanSpacesStorage()
        elif self.provider == "local":
            self._strategy = LocalStorage()
        else:
            raise ValueError(
                f"Unsupported STORAGE_PROVIDER parameter string '{self.provider}' supplied in env configs."
            )
        logger.info(f"Storage Service runtime initialized using driver provider strategy: {self.provider.upper()}")

    async def upload_file(self, file_object: BinaryIO, target_path: str) -> str:
        return await self._strategy.upload_file(file_object, target_path)

    async def delete_file(self, target_path: str) -> None:
        await self._strategy.delete_file(target_path)


storage_service = StorageService()
