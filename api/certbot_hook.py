#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Certbot DNS-01 Challenge Hook Script
用于自动创建/更新 DNS TXT 记录以完成 Let's Encrypt 验证
"""
import os
import sys

# Debug output to verify script version
print(f"DEBUG: Hook script started. cwd={os.getcwd()}, file={__file__}", file=sys.stderr)

# 在导入 api 模块之前，先将项目根目录添加到 sys.path
# 获取当前脚本所在目录的父目录（即项目根目录）
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"DEBUG: Added {project_root} to sys.path", file=sys.stderr)

from dotenv import load_dotenv
from loguru import logger
from api.aliyun import Aliyun_Domain

def main():
    # Certbot 会传递以下环境变量
    certbot_domain = os.environ.get('CERTBOT_DOMAIN', '')
    certbot_validation = os.environ.get('CERTBOT_VALIDATION', '')
    
    if not certbot_domain or not certbot_validation:
        logger.error("Missing CERTBOT_DOMAIN or CERTBOT_VALIDATION environment variables")
        sys.exit(1)
    
    # 加载环境变量
    env_file = os.path.join(project_root, '.env')
    load_dotenv(env_file)
    
    access_key_id = os.getenv('AccessKey_ID')
    access_key_secret = os.getenv('AccessKey_Secret')
    endpoint = os.getenv('Endpoint')
    domain = os.getenv('Domain')
    record = os.getenv('Record', '_acme-challenge')
    
    if not all([access_key_id, access_key_secret, endpoint, domain]):
        logger.error("Missing required environment variables in .env file")
        sys.exit(1)
    
    logger.info(f"Processing DNS challenge for domain: {certbot_domain}")
    logger.info(f"Validation value: {certbot_validation[:20]}...")
    
    try:
        # 获取现有记录
        domain_list = Aliyun_Domain.get_record(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            endpoint=endpoint,
            domain_name=domain
        )
        
        record_id = None
        record_found = False
        
        # 查找是否已存在该记录
        for record_item in domain_list["body"]["DomainRecords"]['Record']:
            if record_item["RR"] == record and record_item["Type"] == "TXT":
                record_id = record_item["RecordId"]
                record_found = True
                break
        
        if record_found and record_id:
            # 更新现有记录
            logger.info(f"Updating existing DNS record (ID: {record_id})")
            Aliyun_Domain.update_record(
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                endpoint=endpoint,
                record_id=record_id,
                record=record,
                record_value=certbot_validation
            )
        else:
            # 创建新记录
            logger.info("Creating new DNS record")
            Aliyun_Domain.new_record(
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                endpoint=endpoint,
                domain_name=domain,
                record=record,
                record_value=certbot_validation
            )
        
        logger.success(f"DNS TXT record for {record}.{domain} has been set")
        logger.info("Waiting 15 seconds for DNS propagation...")
        
        import time
        time.sleep(15)  # 等待 DNS 传播
        
    except Exception as e:
        logger.error(f"Failed to update DNS record: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
