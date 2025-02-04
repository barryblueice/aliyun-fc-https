import subprocess
import logging
import time

logger = logging.getLogger(__name__)

def certbot_update(domain: str):
    command = f"certbot certonly --force-renewal --manual -d '*.{domain}' --preferred-challenges dns --server https://acme-v02.api.letsencrypt.org/directory --key-type rsa"

    time.sleep(1)

    try:
        subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
    except:
        pass

    logger.info("Update SSL Complete")
