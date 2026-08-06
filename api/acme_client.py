"""无需 Certbot 的 ACME DNS-01 证书签发器。"""

from __future__ import annotations

import datetime as dt
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from acme import challenges, client, errors, messages
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from josepy import JWKRSA
from loguru import logger

from api.aliyun import Aliyun_Domain


LETSENCRYPT_DIRECTORY = "https://acme-v02.api.letsencrypt.org/directory"


@dataclass(frozen=True)
class CertificatePaths:
    fullchain: Path
    certificate: Path
    chain: Path
    private_key: Path
    account_key: Path


@dataclass(frozen=True)
class _DnsChange:
    record_id: str
    previous_value: Optional[str]
    created: bool


def _atomic_write(path: Path, data: bytes, private: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(data)
    if private:
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            # Windows ACL 不使用 POSIX 权限位。
            pass
    os.replace(temporary, path)


def _load_or_create_rsa_key(path: Path, key_size: int) -> rsa.RSAPrivateKey:
    if path.exists():
        key = serialization.load_pem_private_key(path.read_bytes(), password=None)
        if not isinstance(key, rsa.RSAPrivateKey):
            raise ValueError(f"{path} 不是 RSA 私钥")
        return key

    logger.info(f"Generating RSA private key: {path}")
    key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    _atomic_write(path, pem, private=True)
    return key


def _create_csr(domain: str, key: rsa.RSAPrivateKey) -> bytes:
    wildcard = f"*.{domain}"
    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, wildcard)]))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName(wildcard)]), critical=False)
        .sign(key, hashes.SHA256())
    )
    return csr.public_bytes(serialization.Encoding.PEM)


def _find_txt_record(records: dict, record: str) -> Optional[dict]:
    for item in records.get("body", {}).get("DomainRecords", {}).get("Record", []):
        if item.get("RR") == record and item.get("Type") == "TXT":
            return item
    return None


class _AliDnsChallenge:
    def __init__(
        self,
        *,
        access_key_id: str,
        access_key_secret: str,
        endpoint: str,
        domain: str,
        record: str,
    ) -> None:
        self._credentials = {
            "access_key_id": access_key_id,
            "access_key_secret": access_key_secret,
            "endpoint": endpoint,
        }
        self.domain = domain
        self.record = record

    def set(self, value: str) -> _DnsChange:
        records = Aliyun_Domain.get_record(
            **self._credentials,
            domain_name=self.domain,
            record=self.record,
        )
        existing = _find_txt_record(records, self.record)

        if existing:
            Aliyun_Domain.update_record(
                **self._credentials,
                record_id=existing["RecordId"],
                record=self.record,
                record_value=value,
            )
            return _DnsChange(
                record_id=existing["RecordId"],
                previous_value=existing.get("Value", ""),
                created=False,
            )

        response = Aliyun_Domain.new_record(
            **self._credentials,
            domain_name=self.domain,
            record=self.record,
            record_value=value,
        )
        record_id = str(response.get("body", {}).get("RecordId", ""))
        if not record_id:
            records = Aliyun_Domain.get_record(
                **self._credentials,
                domain_name=self.domain,
                record=self.record,
            )
            created = _find_txt_record(records, self.record)
            if not created:
                raise RuntimeError("AliDNS 已创建 TXT 记录，但未能取得 RecordId")
            record_id = str(created["RecordId"])
        return _DnsChange(record_id=record_id, previous_value=None, created=True)

    def restore(self, change: _DnsChange) -> None:
        if change.created:
            Aliyun_Domain.delete_record(
                **self._credentials,
                record_id=change.record_id,
            )
            return

        Aliyun_Domain.update_record(
            **self._credentials,
            record_id=change.record_id,
            record=self.record,
            record_value=change.previous_value or "",
        )


def _register_account(
    acme_client: client.ClientV2,
    network: client.ClientNetwork,
    email: str,
) -> None:
    registration = messages.NewRegistration.from_data(
        email=email,
        terms_of_service_agreed=True,
    )
    try:
        acme_client.new_account(registration)
        logger.success("ACME account registered")
    except errors.ConflictError as conflict:
        # 同一账户密钥已经注册时，CA 会返回已有账户 URL。
        network.account = messages.RegistrationResource(
            body=messages.Registration.from_data(email=email),
            uri=conflict.location,
        )
        logger.info("Using existing ACME account")


def issue_wildcard_certificate(
    *,
    access_key_id: str,
    access_key_secret: str,
    endpoint: str,
    domain: str,
    record: str,
    key_path: Path,
    email: str,
    directory_url: str = LETSENCRYPT_DIRECTORY,
    propagation_seconds: int = 30,
    key_size: int = 2048,
) -> CertificatePaths:
    """签发 ``*.domain`` 并将证书和私钥保存到 ``key_path``。"""

    domain = domain.strip().lower().removeprefix("*.").rstrip(".")
    if not domain or "." not in domain:
        raise ValueError(f"Invalid domain: {domain!r}")
    if key_size < 2048:
        raise ValueError("RSA_Key_Size must be at least 2048")
    if propagation_seconds < 0:
        raise ValueError("DNS_Propagation_Seconds cannot be negative")

    paths = CertificatePaths(
        fullchain=key_path / "fullchain.pem",
        certificate=key_path / "cert.pem",
        chain=key_path / "chain.pem",
        private_key=key_path / "privkey.pem",
        account_key=key_path / "account.pem",
    )
    account_private_key = _load_or_create_rsa_key(paths.account_key, key_size)
    certificate_private_key = _load_or_create_rsa_key(paths.private_key, key_size)
    account_key = JWKRSA(key=account_private_key)

    network = client.ClientNetwork(
        account_key,
        user_agent="aliyun-fc-https (direct ACME client)",
    )
    directory = client.ClientV2.get_directory(directory_url, network)
    acme_client = client.ClientV2(directory, network)
    _register_account(acme_client, network, email)

    wildcard = f"*.{domain}"
    logger.info(f"Creating ACME order for {wildcard}")
    order = acme_client.new_order(_create_csr(domain, certificate_private_key))
    dns = _AliDnsChallenge(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        endpoint=endpoint,
        domain=domain,
        record=record,
    )
    changes: list[_DnsChange] = []

    try:
        for authorization in order.authorizations:
            challenge_body = next(
                (
                    item
                    for item in authorization.body.challenges
                    if isinstance(item.chall, challenges.DNS01)
                ),
                None,
            )
            if challenge_body is None:
                raise RuntimeError("ACME server did not offer a DNS-01 challenge")

            validation = challenge_body.chall.validation(account_key)
            logger.info(f"Setting AliDNS TXT record: {record}.{domain}")
            changes.append(dns.set(validation))

            if propagation_seconds:
                logger.info(
                    f"Waiting {propagation_seconds} seconds for DNS propagation"
                )
                time.sleep(propagation_seconds)

            response = challenge_body.chall.response(account_key)
            acme_client.answer_challenge(challenge_body, response)

        deadline = dt.datetime.now() + dt.timedelta(minutes=5)
        finalized = acme_client.poll_and_finalize(order, deadline=deadline)
        fullchain_pem = finalized.fullchain_pem.encode("ascii")
        certificates = x509.load_pem_x509_certificates(fullchain_pem)
        if not certificates:
            raise RuntimeError("ACME server returned an empty certificate chain")

        leaf_pem = certificates[0].public_bytes(serialization.Encoding.PEM)
        chain_pem = b"".join(
            certificate.public_bytes(serialization.Encoding.PEM)
            for certificate in certificates[1:]
        )
        _atomic_write(paths.fullchain, fullchain_pem)
        _atomic_write(paths.certificate, leaf_pem)
        _atomic_write(paths.chain, chain_pem)
        logger.success(f"Certificate saved to {paths.fullchain}")
        return paths
    finally:
        for change in reversed(changes):
            try:
                dns.restore(change)
                logger.info("AliDNS challenge record restored")
            except Exception as cleanup_error:
                logger.warning(f"Failed to restore AliDNS challenge record: {cleanup_error}")
