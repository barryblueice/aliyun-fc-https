from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.hazmat.backends import default_backend

from typing import Union
from loguru import logger

import sys,os

# key_temp_path = os.path.join(os.getcwd(),'key_temp')

def pkcs8_to_pkcs1(pkcs8_key: str) -> str:
    
    private_key = serialization.load_pem_private_key(
        pkcs8_key.encode(), password=None, backend=default_backend()
    )

    if isinstance(private_key, rsa.RSAPrivateKey):
        pkcs1_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        return pkcs1_key
    else:
        raise ValueError("The provided key is not an RSA private key.")
    
def main_convert_main(
    key_path: str
) -> str:
    try:
        key_path = os.path.join(key_path,'privkey.pem')
        with open(key_path,'r') as f:
            pkcs8_key = f.read()
        pkcs1_key = pkcs8_to_pkcs1(pkcs8_key)
        logger.success('''New key has been converted!''')
        return pkcs1_key
    except Exception as e:
        logger.error(f'Error: {e}')
        sys.exit(1)

def compare_detail(
    online_cert: str,
    online_rsa_key: str,
    local_cert: str,
    local_rsa_key: Union[str, bytes]
):
    cert_equal = False
    rsa_key_equal = False

    online_cert = x509.load_pem_x509_certificate(online_cert.encode(), default_backend())
    local_cert = x509.load_pem_x509_certificate(local_cert.encode(), default_backend())

    online_cert_key = online_cert.public_key()
    local_cert_key = local_cert.public_key()

    if online_cert_key.public_numbers() == local_cert_key.public_numbers():
        cert_equal = True

    logger.info(f'Online & Local cert same? {cert_equal}')

    online_rsa_key = serialization.load_pem_private_key(online_rsa_key.encode(), password=None)
    local_rsa_key = serialization.load_pem_private_key(local_rsa_key, password=None)

    # 比较私钥的公钥部分
    online_rsa_key = online_rsa_key.public_key()
    local_rsa_key = local_rsa_key.public_key()

    if online_rsa_key.public_numbers() == local_rsa_key.public_numbers():
        rsa_key_equal = True

    logger.info(f'Online & Local RSA Key same? {rsa_key_equal}')

    if cert_equal == rsa_key_equal:
        if cert_equal == True:
            return True
        return False
    else:
        return False
