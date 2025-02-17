import os,sys
import ujson as json

from loguru import logger
from cryptography import x509
from cryptography.hazmat.backends import default_backend

def update_expire_date(keypath: str):

    try:
        with open(os.path.join(keypath,'fullchain.pem'),"rb") as f:
            cert_data = f.read()

        cert = x509.load_pem_x509_certificate(cert_data, default_backend())


        expiration_date = cert.not_valid_after_utc

        # logger.info(f"Expired Date: {expiration_date}")

        with open(os.path.join(os.getcwd(),"db.json"),"w",encoding='utf-8') as f:
            json.dump({"expired-date":str(expiration_date)},f,indent=4,ensure_ascii=False)

        logger.success(f'Cert Expired Date updated Complete: {expiration_date}')
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(e.errno)
