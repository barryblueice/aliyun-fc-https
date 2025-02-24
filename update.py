import os,sys
import ujson as json
from loguru import logger
from dotenv import load_dotenv
from api.aliyun import Aliyun_Credential,Aliyun_Domain,Aliyun_SSL
from api import db,certbot,cert_rsa_api
import time
from datetime import datetime
import pytz

# This python script needs superuser(root) permission to run!

def updating_main_process():

    env_file = os.path.join(os.getcwd(),'.env')

    if not os.path.exists(env_file):
        with open(env_file, 'w',encoding='utf-8') as f:
            f.write('AccessKey_ID=\n')
            f.write('AccessKey_Secret=\n')
            f.write('\nEndpoint=\n')
            f.write('Domain=\n')
            f.write('Record=\n')
            f.write('Record_Value=\n')
            f.write('\nKey_Path=\n')
            f.write('Cert_Id=\n')
            f.write('\n# Endpoint 请参考 https://api.aliyun.com/product/Alidns\n\n')
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
        endpoint = os.getenv('Endpoint')
        domain =  os.getenv('Domain')
        record = os.getenv('Record')
        record_value = os.getenv('Record_Value')
        key_path = os.getenv('Key_Path')
        cert_id = os.getenv('Cert_Id')

        time.sleep(1)

        logger.info("Updating SSL...")

        time.sleep(1)

        try:

            if not access_key_id or not access_key_secret or not endpoint or not domain or not record or not record_value or not key_path or not cert_id:
                logger.error("Environment file is illegal, please check!")
                sys.exit(0)
            else:
                logger.info(f"AccessKey ID: {access_key_id}")
                logger.info(f"AccessKey Secret: {access_key_secret}")
                logger.info(f"Endpoint: {endpoint}")
                logger.info(f"Domain: {domain}")
                logger.info(f"Record: {record}")
                logger.info(f"Record Value: {record_value}")
                logger.info(f"Key Path: {key_path}")
                logger.info(f"Cert ID: {cert_id}")

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

                if record_check == False:
                    logger.warning("Record Not Found, Updating……")
                    domain_list = Aliyun_Domain.new_record(
                        access_key_id = access_key_id,
                        access_key_secret = access_key_secret,
                        endpoint = endpoint,
                        domain_name = domain,
                        record = record,
                        record_value = record_value
                        )
                    
                logger.info("Updating SSL by CertBot")

                time.sleep(1)

                certbot.certbot_update(domain=domain)
                db.update_expire_date(keypath=key_path)

                with open(os.path.join(os.getcwd(),"db.json"),"r",encoding='utf-8') as f:
                    expiration_date = (json.load(f))["expired-date"]
                logger.info(f"Cert Expired Date: {expiration_date}")

                time.sleep(1)

                SSL_info = Aliyun_SSL.Get_SSL(
                    access_key_id = access_key_id,
                    access_key_secret = access_key_secret,
                    cert_id=int(cert_id)
                )

                time.sleep(1)

                with open(os.path.join(key_path,'fullchain.pem'),'r') as f:
                    local_cert = f.read()
                local_rsa_key = cert_rsa_api.main_convert_main(key_path=key_path)

                _equal = True

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
                        cert_id=cert_id
                    )
                    _equal = False
                    ssl_name = domain.replace('.','-')

                    with open(env_file, "r") as file:
                        lines = file.readlines()

                    filtered_lines = [line for line in lines if not line.startswith("Cert_Id")]

                    with open(env_file, "w") as file:
                        file.writelines(filtered_lines)


                if not _equal:
                    res = Aliyun_SSL.Upload_SSL(
                        access_key_id=access_key_id,
                        access_key_secret=access_key_secret,
                        cert=local_cert,
                        key=local_rsa_key,
                        name=ssl_name,
                        cert_id=int(cert_id)
                    )

                    CertId = res["body"]["CertId"]

                    with open(env_file, "a") as file:
                        file.write(f"Cert_Id={CertId}")

                time.sleep(1)
                
                logger.success('SSL Updating Complete!')

        except Exception as e:

            logger.error(f'Error: {e}')
            sys.exit(e.errno)
