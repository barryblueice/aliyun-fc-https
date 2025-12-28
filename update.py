import os,sys
import ujson as json
from loguru import logger
from dotenv import load_dotenv
from api.aliyun import Aliyun_Credential,Aliyun_Domain,Aliyun_SSL,Aliyun_FC
from api import db,certbot,cert_rsa_api
import time
from datetime import datetime
import pytz

# This python script needs superuser(root) permission to run!

def updating_main_process():

    _equal = True

    env_file = os.path.join(os.getcwd(),'.env')

    if not os.path.exists(env_file):
        with open(env_file, 'w',encoding='utf-8') as f:
            f.write('AccessKey_ID=\n')
            f.write('AccessKey_Secret=\n')
            f.write('User_ID=\n')
            f.write('\nEndpoint=\n')
            f.write('Domain=\n')
            f.write('Record=\n')
            f.write('Record_Value=\n')
            f.write('\nKey_Path=\n')
            f.write('Cert_Id=\n')
            f.write('\nFC-Update=0')
            f.write('\n\n# Endpoint 请参考 https://api.aliyun.com/product/Alidns\n\n')
        logger.success(f"{env_file} was created and new credentials were added. Please restart the script after editing!")
        sys.exit(0)
        
    else:

        if os.path.exists(os.path.join(os.getcwd(),'db.json')):
            logger.info(f'db.json already exists...')
            try:
                with open(os.path.join(os.getcwd(),'db.json'), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    expired_date_str = data['expired-date']
                    if expired_date_str:
                        expired_date = datetime.fromisoformat(expired_date_str).astimezone(pytz.UTC)
                        current_time = datetime.now(pytz.UTC)
                        if current_time >= expired_date:
                            logger.warning("The current time is equal to or later than the expired-date, need to update...")
                        else:
                            logger.info("Too early to update SSL, exiting updating process...")
                            return
                    else:
                        logger.error(f'expired-date not found! The db.json need to re-create!')
            except Exception as e:
                logger.error(f'Error: {e}, the db.json need to re-create!')

        load_dotenv(env_file)

        access_key_id = os.getenv('AccessKey_ID')
        access_key_secret = os.getenv('AccessKey_Secret')
        user_id = os.getenv('User_ID')
        endpoint = os.getenv('Endpoint')
        domain =  os.getenv('Domain')
        record = os.getenv('Record')
        record_value = os.getenv('Record_Value')
        key_path = os.getenv('Key_Path')
        cert_id = os.getenv('Cert_Id')
        fc_update = os.getenv('FC-Update')

        time.sleep(1)

        logger.info("Updating SSL...")

        time.sleep(1)

        try:

            # Record_Value 不再必需，hook 脚本会自动处理
            if not access_key_id or not access_key_secret or not endpoint or not domain or not record or not key_path or not cert_id or not fc_update or not user_id:
                logger.error("Environment file is illegal, please check!")
                sys.exit(0)
            else:
                logger.info(f"AccessKey ID: {access_key_id}")
                logger.info(f"AccessKey Secret: {access_key_secret}")
                logger.info(f"User ID: {user_id}")
                logger.info(f"Endpoint: {endpoint}")
                logger.info(f"Domain: {domain}")
                logger.info(f"Record: {record}")
                if record_value:
                    logger.info(f"Record Value: {record_value} (hook 脚本会自动更新)")
                logger.info(f"Key Path: {key_path}")
                logger.info(f"Cert ID: {cert_id}")
                logger.info(f"FC-Updating? : {fc_update}")

                # 自动修正 Key_Path：如果配置的路径不存在，尝试使用基于域名的标准路径
                if not os.path.exists(os.path.join(key_path, 'fullchain.pem')):
                    standard_path = f"/etc/letsencrypt/live/{domain}"
                    if os.path.exists(os.path.join(standard_path, 'fullchain.pem')):
                        logger.warning(f"Configured Key_Path '{key_path}' invalid. Found certs at '{standard_path}'. Using it.")
                        key_path = standard_path
                    else:
                        logger.warning(f"Certificate not found at {key_path} or {standard_path}. Certbot might generate it later.")

                time.sleep(1)

                domain_list = Aliyun_Domain.get_record(
                    access_key_id = access_key_id,
                    access_key_secret = access_key_secret,
                    endpoint = endpoint,
                    domain_name = domain
                    )
                
                record_check = False

                for record_item in domain_list["body"]["DomainRecords"]['Record']:
                    if record_item["RR"] == record:
                        if record_item["Status"] == "ENABLE":
                            record_check = True
                            break

                # 注意：DNS 记录现在由 certbot hook 脚本自动创建/更新
                # 这里只做检查，不预先创建
                if record_check == False:
                    logger.info("DNS record not found, will be created automatically by certbot hook")
                    
                logger.info("Updating SSL by CertBot (fully automated)")

                time.sleep(1)

                # 添加重试机制
                max_retries = 3
                last_error = None
                for attempt in range(max_retries):
                    try:
                        certbot.certbot_update(domain=domain)
                        break  # 成功则退出循环
                    except Exception as e:
                        last_error = e
                        if attempt < max_retries - 1:
                            logger.warning(f"Certbot update failed (attempt {attempt + 1}/{max_retries}): {e}")
                            logger.info("Retrying in 10 seconds...")
                            time.sleep(10)
                        else:
                            logger.error(f"Certbot update failed after {max_retries} attempts")
                            logger.error(f"Last error details: {last_error}")
                            # 输出完整的错误信息，包括 traceback
                            import traceback
                            logger.error(f"Full traceback:\n{traceback.format_exc()}")
                            raise e  # 最后一次失败则抛出异常

                db.update_expire_date(keypath=key_path)

                with open(os.path.join(os.getcwd(),"db.json"),"r",encoding='utf-8') as f:
                    expiration_date = (json.load(f))["expired-date"]
                logger.info(f"Cert Expired Date: {expiration_date}")

                time.sleep(1)

                SSL_info = Aliyun_SSL.Get_SSL(
                    access_key_id = access_key_id,
                    access_key_secret = access_key_secret,
                    cert_id=str(cert_id)
                )

                time.sleep(1)

                with open(os.path.join(key_path,'fullchain.pem'),'r', encoding="utf-8") as f:
                    local_cert = f.read()
                local_rsa_key = cert_rsa_api.main_convert_main(key_path=key_path)

                if SSL_info[0] == True:
                    online_cert = SSL_info[1]['body']["Cert"]
                    online_rsa_key = SSL_info[1]['body']["Key"]
                    ssl_name = SSL_info[1]['body']["Name"]

                    _equal = cert_rsa_api.compare_detail(
                        online_cert=online_cert,
                        online_rsa_key=online_rsa_key,
                        local_cert=local_cert,

                        local_rsa_key=local_rsa_key
                    )

                else:
                    logger.warning(f'Error: {SSL_info[1]}! The cert needs re-updating!')
                    time.sleep(1)

                if SSL_info[0] == True:

                    Aliyun_SSL.Delete_SSL(
                        access_key_id=access_key_id,
                        access_key_secret=access_key_secret,
                        cert_id=str(cert_id)
                    )
                    _equal = False
                    ssl_name = domain.replace('.','-')

                    with open(env_file, "r", encoding="utf-8") as file:
                        lines = file.readlines()

                    filtered_lines = [line for line in lines if not line.startswith("Cert_Id")]

                    with open(env_file, "w", encoding="utf-8") as file:
                        file.writelines(filtered_lines)

                if not _equal:
                    res = Aliyun_SSL.Upload_SSL(
                        access_key_id=access_key_id,
                        access_key_secret=access_key_secret,
                        cert=local_cert,
                        key=local_rsa_key,
                        name=ssl_name,
                        cert_id=str(cert_id)
                    )

                    CertId = res["body"]["CertId"]

                    with open(env_file, "a", encoding="utf-8") as file:
                        file.write(f"Cert_Id={CertId}")

                time.sleep(1)
                
                logger.success('SSL Updating Complete!')

                if fc_update == "1":
                    fc_domain_list = Aliyun_FC.GetFCDomain(
                        
                        access_key_id=access_key_id,
                        access_key_secret=access_key_secret,
                        user_id=user_id,
                        endpoint=endpoint

                    )

                    fc_domain_list_target = []

                    for i in fc_domain_list["body"]["customDomains"]:
                        if str(i["domainName"]).endswith(domain):
                            fc_domain_list_target.append(i["domainName"])

                    logger_message = "\n\nThese FC-Domains' Certification need to be updated:\n"
                    for i in fc_domain_list_target:
                        logger_message += f'\n  - {i}'
                    logger_message += '\n'
                    logger.info(logger_message)

                    for i in fc_domain_list_target:
                        try:
                            response = Aliyun_FC.UpdateFCCert(
                                access_key_id=access_key_id,
                                access_key_secret=access_key_secret,
                                user_id=user_id,
                                endpoint=endpoint,
                                cert=local_cert,
                                rsa=local_rsa_key,
                                domain=i,
                                cert_name=domain.replace('.','-')
                            )
                            if response.get("statusCode") == 200:
                                logger.success(f"Domain {i}'s Certification Updating Complete!")
                            else:
                                logger.error(f"Domain {i} Update Failed: {response}")
                        except Exception as e:
                            logger.error(f"Failed to update domain {i}: {e}")
                            # 继续处理下一个域名，不要退出
                            continue

        except Exception as e:

            logger.error(f'Error: {e}')
            sys.exit(1)
