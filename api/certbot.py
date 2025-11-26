import subprocess
import time
import os
from loguru import logger

def certbot_update(domain: str):
    # 获取 hook 脚本路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    hook_script = os.path.join(script_dir, 'certbot_hook.py')
    
    # 使用 python 直接执行 hook 脚本，避免 shebang 换行符问题
    hook_command = f"python3 {hook_script}"
    
    # 使用 manual-auth-hook 自动创建/更新 DNS 记录
    # --non-interactive 自动同意，不需要手动确认
    command = (
        f"certbot certonly --force-renewal --manual "
        f"--manual-auth-hook '{hook_command}' "
        f"--preferred-challenges dns "
        f"-d '*.{domain}' "
        f"--server https://acme-v02.api.letsencrypt.org/directory "
        f"--key-type rsa "
        f"--non-interactive "
        f"--agree-tos "
        f"--email admin@{domain}"
    )

    time.sleep(1)

    try:
        logger.info("Certbot 正在自动运行，DNS 记录将自动创建/更新...")
        logger.info("使用 hook 脚本自动处理 DNS 验证，无需手动操作")
        
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
            capture_output=True,
            encoding="utf-8",
        )

        logger.info("Certbot Updating process finished！")
        if result.stdout:
            logger.debug(f"Certbot output: {result.stdout}")

    except subprocess.CalledProcessError as e:
        error_msg = f"Certbot Updating process fail, Error Code: {e.returncode}"
        if hasattr(e, 'stderr') and e.stderr:
            error_msg += f"\nError Output:\n{e.stderr}"
        if hasattr(e, 'stdout') and e.stdout:
            error_msg += f"\nStandard Output:\n{e.stdout}"
        logger.error(error_msg)
        raise 

    except Exception as e:
        logger.error("Unknown Error: {}", e)
        raise

    else:
        logger.info("Update SSL Complete!")
        return