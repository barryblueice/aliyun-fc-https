import subprocess
import time
from loguru import logger

def certbot_update(domain: str):
    command = f"certbot certonly --force-renewal --manual -d '*.{domain}' --preferred-challenges dns --server https://acme-v02.api.letsencrypt.org/directory --key-type rsa"
    
    # command = f"screenfetch"

    time.sleep(1)

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
            capture_output=True,
            encoding="utf-8",
        )

        logger.info("Certbot Updating process finished！Output：\n{}", result.stdout)

    except subprocess.CalledProcessError as e:
        logger.error(
            "Certbot Updating process fail, Error Code: {}\nError Output:\n{}\nStandard Output:\n{}",
            e.returncode,
            e.stderr,
            e.stdout,
        )
        raise 

    except Exception as e:
        logger.error("Unknown Error: {}", e)
        raise

    else:
        logger.info("Update SSL Complete!")
        return