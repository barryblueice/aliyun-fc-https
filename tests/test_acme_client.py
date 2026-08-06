import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import ANY, patch

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import rsa

from api.acme_client import (
    _AliDnsChallenge,
    _create_csr,
    _load_or_create_rsa_key,
    issue_wildcard_certificate,
)
from update import _covered_by_wildcard, _supports_https, _update_fc_domains


class KeyAndCsrTests(unittest.TestCase):
    def test_wildcard_matches_exactly_one_label(self) -> None:
        self.assertTrue(_covered_by_wildcard("www.example.com", "example.com"))
        self.assertFalse(_covered_by_wildcard("example.com", "example.com"))
        self.assertFalse(_covered_by_wildcard("a.b.example.com", "example.com"))
        self.assertFalse(_covered_by_wildcard("notexample.com", "example.com"))

    def test_https_protocol_detection(self) -> None:
        self.assertTrue(_supports_https("HTTPS"))
        self.assertTrue(_supports_https("HTTP,HTTPS"))
        self.assertTrue(_supports_https("HTTP/HTTPS"))
        self.assertFalse(_supports_https("HTTP"))
        self.assertFalse(_supports_https(""))

    def test_account_key_is_reused_and_csr_contains_wildcard(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            key_path = Path(temporary) / "account.pem"
            first = _load_or_create_rsa_key(key_path, 2048)
            second = _load_or_create_rsa_key(key_path, 2048)
            self.assertEqual(first.private_numbers(), second.private_numbers())

            certificate_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            csr = x509.load_pem_x509_csr(
                _create_csr("example.com", certificate_key)
            )
            names = csr.extensions.get_extension_for_class(
                x509.SubjectAlternativeName
            ).value.get_values_for_type(x509.DNSName)
            self.assertTrue(csr.is_signature_valid)
            self.assertEqual(names, ["*.example.com"])

    def test_custom_acme_directory_is_used(self) -> None:
        custom_directory = "https://acme.example.test/custom-directory"
        with tempfile.TemporaryDirectory() as temporary, patch(
            "api.acme_client.client.ClientV2.get_directory",
            side_effect=RuntimeError("stop after directory discovery"),
        ) as get_directory:
            with self.assertRaisesRegex(RuntimeError, "directory discovery"):
                issue_wildcard_certificate(
                    access_key_id="id",
                    access_key_secret="secret",
                    endpoint="alidns.example.test",
                    domain="example.com",
                    record="_acme-challenge",
                    key_path=Path(temporary),
                    email="admin@example.com",
                    directory_url=custom_directory,
                    propagation_seconds=0,
                )

        get_directory.assert_called_once_with(custom_directory, ANY)


class AliDnsChallengeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.challenge = _AliDnsChallenge(
            access_key_id="id",
            access_key_secret="secret",
            endpoint="alidns.example.test",
            domain="example.com",
            record="_acme-challenge",
        )

    @patch("api.acme_client.Aliyun_Domain")
    def test_existing_record_is_restored(self, domain_api) -> None:
        domain_api.get_record.return_value = {
            "body": {
                "DomainRecords": {
                    "Record": [
                        {
                            "RR": "_acme-challenge",
                            "Type": "TXT",
                            "RecordId": "record-1",
                            "Value": "original",
                        }
                    ]
                }
            }
        }

        change = self.challenge.set("validation")
        self.challenge.restore(change)

        self.assertEqual(domain_api.update_record.call_count, 2)
        self.assertEqual(
            domain_api.update_record.call_args_list[0].kwargs["record_value"],
            "validation",
        )
        self.assertEqual(
            domain_api.update_record.call_args_list[1].kwargs["record_value"],
            "original",
        )
        domain_api.delete_record.assert_not_called()

    @patch("api.acme_client.Aliyun_Domain")
    def test_new_record_is_deleted(self, domain_api) -> None:
        domain_api.get_record.return_value = {
            "body": {"DomainRecords": {"Record": []}}
        }
        domain_api.new_record.return_value = {"body": {"RecordId": "record-2"}}

        change = self.challenge.set("validation")
        self.challenge.restore(change)

        domain_api.delete_record.assert_called_once_with(
            access_key_id="id",
            access_key_secret="secret",
            endpoint="alidns.example.test",
            record_id="record-2",
        )


class FunctionComputeTests(unittest.TestCase):
    @patch("update.Aliyun_FC.UpdateFCCert")
    @patch("update.Aliyun_FC.GetFCDomain")
    def test_only_https_domains_are_updated_with_protocol(
        self,
        get_domains,
        update_certificate,
    ) -> None:
        get_domains.return_value = {
            "body": {
                "customDomains": [
                    {"domainName": "http.example.com", "protocol": "HTTP"},
                    {"domainName": "https.example.com", "protocol": "HTTPS"},
                    {
                        "domainName": "both.example.com",
                        "protocol": "HTTP,HTTPS",
                    },
                    {"domainName": "a.b.example.com", "protocol": "HTTPS"},
                ]
            }
        }
        update_certificate.return_value = {"statusCode": 200}
        config = SimpleNamespace(
            fc_update=True,
            access_key_id="id",
            access_key_secret="secret",
            user_id="account",
            endpoint="alidns.cn-hangzhou.aliyuncs.com",
            domain="example.com",
        )

        _update_fc_domains(config, "certificate", "private-key")

        self.assertEqual(update_certificate.call_count, 2)
        calls = {call.kwargs["domain"]: call.kwargs for call in update_certificate.call_args_list}
        self.assertEqual(calls["https.example.com"]["protocol"], "HTTPS")
        self.assertEqual(calls["both.example.com"]["protocol"], "HTTP,HTTPS")
        self.assertNotIn("http.example.com", calls)


if __name__ == "__main__":
    unittest.main()
