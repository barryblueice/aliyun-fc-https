"""证书续期、阿里云证书上传及函数计算域名更新流程。"""

from __future__ import annotations

import datetime as dt
import os
import time
from dataclasses import dataclass
from pathlib import Path

from cryptography import x509
from dotenv import load_dotenv
from loguru import logger

from api import cert_rsa_api
from api.acme_client import LETSENCRYPT_DIRECTORY, issue_wildcard_certificate
from api.aliyun import Aliyun_FC, Aliyun_SSL


PROJECT_ROOT = Path(__file__).resolve().parent
ENV_FILE = PROJECT_ROOT / ".env"
ENV_SAMPLE_FILE = PROJECT_ROOT / ".env.sample"


class ConfigurationRequired(RuntimeError):
    """首次运行已创建配置文件，需要用户填写。"""


@dataclass(frozen=True)
class Config:
    access_key_id: str
    access_key_secret: str
    user_id: str
    endpoint: str
    domain: str
    record: str
    key_path: Path
    cert_id: str
    fc_update: bool
    acme_email: str
    acme_directory_url: str
    dns_propagation_seconds: int
    rsa_key_size: int
    renew_before_days: int


def _create_env_file() -> None:
    ENV_FILE.write_text(ENV_SAMPLE_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        os.chmod(ENV_FILE, 0o600)
    except OSError:
        pass
    logger.success(f"Created {ENV_FILE}; fill it in and run the program again")


def _read_int(name: str, default: int, minimum: int = 0) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer") from error
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


def _load_config() -> Config:
    if not ENV_FILE.exists():
        _create_env_file()
        raise ConfigurationRequired(str(ENV_FILE))

    load_dotenv(ENV_FILE, override=True)
    values = {
        "AccessKey_ID": os.getenv("AccessKey_ID", "").strip(),
        "AccessKey_Secret": os.getenv("AccessKey_Secret", "").strip(),
        "Endpoint": os.getenv("Endpoint", "").strip(),
        "Domain": os.getenv("Domain", "").strip().lower().removeprefix("*."),
    }
    missing = [name for name, value in values.items() if not value or value.startswith("<")]
    if missing:
        raise ValueError(f"Missing required .env values: {', '.join(missing)}")

    domain = values["Domain"].rstrip(".")
    user_id = os.getenv("User_ID", "").strip()
    fc_update = os.getenv("FC-Update", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if fc_update and not user_id:
        raise ValueError("User_ID is required when FC-Update=1")

    raw_key_path = os.getenv("Key_Path", "").strip()
    key_path = Path(raw_key_path) if raw_key_path else Path("certs") / domain
    if not key_path.is_absolute():
        key_path = PROJECT_ROOT / key_path

    email = os.getenv("ACME_Email", "").strip() or f"admin@{domain}"
    directory_url = (
        os.getenv("ACME_Directory_URL", "").strip() or LETSENCRYPT_DIRECTORY
    )

    return Config(
        access_key_id=values["AccessKey_ID"],
        access_key_secret=values["AccessKey_Secret"],
        user_id=user_id,
        endpoint=values["Endpoint"],
        domain=domain,
        record=os.getenv("Record", "_acme-challenge").strip() or "_acme-challenge",
        key_path=key_path.resolve(),
        cert_id=os.getenv("Cert_Id", "").strip(),
        fc_update=fc_update,
        acme_email=email,
        acme_directory_url=directory_url,
        dns_propagation_seconds=_read_int("DNS_Propagation_Seconds", 30),
        rsa_key_size=_read_int("RSA_Key_Size", 2048, minimum=2048),
        renew_before_days=_read_int("Renew_Before_Days", 30, minimum=1),
    )


def _certificate_needs_renewal(config: Config, force: bool) -> bool:
    if force:
        logger.warning("Forced renewal requested")
        return True

    fullchain = config.key_path / "fullchain.pem"
    if not fullchain.exists():
        logger.info("No local certificate found; a certificate will be issued")
        return True

    try:
        certificate = x509.load_pem_x509_certificate(fullchain.read_bytes())
    except (OSError, ValueError) as error:
        logger.warning(f"Local certificate is unreadable and will be replaced: {error}")
        return True

    renew_at = certificate.not_valid_after_utc - dt.timedelta(
        days=config.renew_before_days
    )
    now = dt.datetime.now(dt.timezone.utc)
    if now >= renew_at:
        logger.info(f"Certificate has entered its renewal window: {renew_at.isoformat()}")
        return True

    logger.info(
        "Certificate is still valid; next renewal window begins at "
        f"{renew_at.isoformat()}"
    )
    return False


def _set_env_value(name: str, value: str) -> None:
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    replacement = f"{name}={value}"
    for index, line in enumerate(lines):
        if line.startswith(f"{name}="):
            lines[index] = replacement
            break
    else:
        lines.append(replacement)

    temporary = ENV_FILE.with_name(".env.tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        os.chmod(temporary, 0o600)
    except OSError:
        pass
    os.replace(temporary, ENV_FILE)


def _issue_certificate(config: Config) -> None:
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            issue_wildcard_certificate(
                access_key_id=config.access_key_id,
                access_key_secret=config.access_key_secret,
                endpoint=config.endpoint,
                domain=config.domain,
                record=config.record,
                key_path=config.key_path,
                email=config.acme_email,
                directory_url=config.acme_directory_url,
                propagation_seconds=config.dns_propagation_seconds,
                key_size=config.rsa_key_size,
            )
            return
        except Exception:
            if attempt == max_attempts:
                raise
            logger.exception(
                f"ACME issuance attempt {attempt}/{max_attempts} failed; retrying in 10 seconds"
            )
            time.sleep(10)


def _read_local_certificate(config: Config) -> tuple[str, str]:
    certificate = (config.key_path / "fullchain.pem").read_text(encoding="ascii")
    stored_key = (config.key_path / "privkey.pem").read_text(encoding="ascii")
    # 兼容原 Certbot 目录中的 PKCS#8 私钥；阿里云上传统一使用 PKCS#1。
    private_key = cert_rsa_api.pkcs8_to_pkcs1(stored_key).decode("ascii")
    return certificate, private_key


def _covered_by_wildcard(hostname: str, domain: str) -> bool:
    hostname = hostname.lower().rstrip(".")
    suffix = f".{domain.lower().rstrip('.')}"
    if not hostname.endswith(suffix):
        return False
    label = hostname[: -len(suffix)]
    return bool(label) and "." not in label


def _update_fc_domains(config: Config, certificate: str, private_key: str) -> None:
    if not config.fc_update:
        return

    response = Aliyun_FC.GetFCDomain(
        access_key_id=config.access_key_id,
        access_key_secret=config.access_key_secret,
        user_id=config.user_id,
        endpoint=config.endpoint,
    )
    domains = [
        item["domainName"]
        for item in response.get("body", {}).get("customDomains", [])
        if _covered_by_wildcard(item.get("domainName", ""), config.domain)
    ]
    logger.info(f"Updating {len(domains)} Function Compute custom domain(s)")

    for domain in domains:
        result = Aliyun_FC.UpdateFCCert(
            access_key_id=config.access_key_id,
            access_key_secret=config.access_key_secret,
            user_id=config.user_id,
            endpoint=config.endpoint,
            cert=certificate,
            rsa=private_key,
            domain=domain,
            cert_name=config.domain.replace(".", "-"),
        )
        if result.get("statusCode") != 200:
            raise RuntimeError(f"Failed to update FC domain {domain}: {result}")
        logger.success(f"Updated FC domain certificate: {domain}")


def _upload_to_aliyun(config: Config, certificate: str, private_key: str) -> bool:
    old_cert_id = config.cert_id
    if old_cert_id:
        online = Aliyun_SSL.Get_SSL(
            access_key_id=config.access_key_id,
            access_key_secret=config.access_key_secret,
            cert_id=old_cert_id,
        )
        if online[0]:
            details = online[1]["body"]
            if cert_rsa_api.compare_detail(
                online_cert=details["Cert"],
                online_rsa_key=details["Key"],
                local_cert=certificate,
                local_rsa_key=private_key.encode("ascii"),
            ):
                logger.info("The newly issued certificate is already uploaded to Aliyun")
                return False

    suffix = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M%S")
    result = Aliyun_SSL.Upload_SSL(
        access_key_id=config.access_key_id,
        access_key_secret=config.access_key_secret,
        cert=certificate,
        key=private_key,
        name=f"{config.domain.replace('.', '-')}-{suffix}",
        cert_id=old_cert_id,
    )
    if not result or not result.get("body", {}).get("CertId"):
        raise RuntimeError("Aliyun did not return a CertId after certificate upload")

    new_cert_id = str(result["body"]["CertId"])
    try:
        _update_fc_domains(config, certificate, private_key)
    except Exception:
        try:
            Aliyun_SSL.Delete_SSL(
                access_key_id=config.access_key_id,
                access_key_secret=config.access_key_secret,
                cert_id=new_cert_id,
            )
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up the new Aliyun certificate: {cleanup_error}")
        raise

    _set_env_value("Cert_Id", new_cert_id)

    if old_cert_id and old_cert_id != new_cert_id:
        try:
            Aliyun_SSL.Delete_SSL(
                access_key_id=config.access_key_id,
                access_key_secret=config.access_key_secret,
                cert_id=old_cert_id,
            )
        except Exception as error:
            logger.warning(f"New certificate is active, but old certificate cleanup failed: {error}")
    return True


def updating_main_process(force: bool = False) -> bool:
    """按需签发和部署证书；发生续期返回 True。"""

    config = _load_config()
    logger.info(f"Domain: *.{config.domain}")
    logger.info(f"ACME directory: {config.acme_directory_url}")
    logger.info(f"Certificate path: {config.key_path}")

    renewed = _certificate_needs_renewal(config, force)
    if renewed:
        _issue_certificate(config)

    certificate, private_key = _read_local_certificate(config)
    deployed = _upload_to_aliyun(config, certificate, private_key)
    if renewed or deployed:
        logger.success("SSL certificate renewal and deployment completed")
    else:
        logger.info("Certificate and Aliyun deployment are already up to date")
    return renewed
