from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

import os

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
    else:
        raise ValueError("The provided key is not an RSA private key.")
    
    return pkcs1_key.decode()

if __name__ == '__main__':
    try:
        with open(os.path.join(os.getcwd(),'privkey.pem'),'r',encoding='utf-8') as f:
            pkcs8_key = f.read()
        pkcs1_key = pkcs8_to_pkcs1(pkcs8_key)
        print(pkcs1_key)
        with open(os.path.join(os.getcwd(),'privkey-new.pem'),'w',encoding='utf-8') as f:
            f.write(pkcs1_key)
        print('''
New key has been updated into privkey-new.pem.
To ensure security, it is recommended to delete all pem files in the working directory after the configuration is complete.''')
    except FileNotFoundError:
        print('privkey.pem not found, please make sure this file is placed in the root working directory!')
    except Exception as e:
        print(f'Error: {e}')