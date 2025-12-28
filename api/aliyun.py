# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import os
import sys

from typing import List
from loguru import logger

from alibabacloud_alidns20150109.client import Client as Alidns20150109Client
from alibabacloud_alidns20150109 import models as alidns_20150109_models

from alibabacloud_cas20200407.client import Client as Alidns20200407Client
from alibabacloud_cas20200407 import models as alidns_20200407_models

from alibabacloud_fc_open20210406.client import Client as Alidns20210406Client
from alibabacloud_fc_open20210406 import models as alidns_20210406_models

from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient
from alibabacloud_credentials.client import Client as CredentialClient

class Aliyun_Credential:
    def __init__(self):
        pass

    @staticmethod
    def _20150109_create_client(

        access_key_id: str,
        access_key_secret: str,
        endpoint: str

    ) -> Alidns20150109Client:

        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret
        )
        config.endpoint = endpoint
        return Alidns20150109Client(config)
    
    @staticmethod
    def _20200407_create_client(

        access_key_id: str,
        access_key_secret: str,
        endpoint: str

    ) -> Alidns20200407Client:

        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret
        )
        config.endpoint = endpoint
        return Alidns20200407Client(config)
    
    @staticmethod
    def _20210406_create_client(

        access_key_id: str,
        access_key_secret: str,
        user_id: str,
        endpoint: str

    ) ->Alidns20210406Client:
        # credential = CredentialClient()
        # config = open_api_models.Config(
        #     credential=credential
        # )
        # config.endpoint = endpoint.replace('alidns',user_id,1).replace('aliyuncs.com','fc.aliyuncs.com',1)
        # return Alidns20210406Client(config)
        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret
        )
        config.endpoint = endpoint.replace('alidns',user_id,1).replace('aliyuncs.com','fc.aliyuncs.com',1)
        return Alidns20210406Client(config)

class Aliyun_Domain:

    """
    20150109
    """

    def __init__(self):
        pass

    @staticmethod
    def get_record(

        access_key_id: str,
        access_key_secret: str,
        endpoint: str,
        domain_name: str

    ) -> None:
        client = Aliyun_Credential._20150109_create_client(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            endpoint=endpoint
        )
        describe_domain_records_request = alidns_20150109_models.DescribeDomainRecordsRequest(
            domain_name = domain_name
        )
        runtime = util_models.RuntimeOptions()
        try:
            res = client.describe_domain_records_with_options(describe_domain_records_request, runtime).to_map()
            return res
        except Exception as error:
            logger.error(f"Aliyun API Error: {error.message}")
            if hasattr(error, 'data') and error.data:
                logger.error(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)
            sys.exit(error.errno if hasattr(error, 'errno') else 1)

    @staticmethod
    def new_record(
        
        access_key_id: str,
        access_key_secret: str,
        endpoint: str,
        domain_name: str,
        record: str,
        record_value: str

    ) -> None:
        client = Aliyun_Credential._20150109_create_client(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            endpoint=endpoint
        )
        add_domain_record_request = alidns_20150109_models.AddDomainRecordRequest(
            domain_name = domain_name,
            rr = record,
            type = 'TXT',
            value = record_value
        )
        runtime = util_models.RuntimeOptions()
        try:
            client.add_domain_record_with_options(add_domain_record_request, runtime)
            logger.success('Record has been successfully initiated')
        except Exception as error:
            logger.error(f"Aliyun API Error: {error.message}")
            if hasattr(error, 'data') and error.data:
                logger.error(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)
            sys.exit(error.errno if hasattr(error, 'errno') else 1)

    @staticmethod
    def update_record(
        
        access_key_id: str,
        access_key_secret: str,
        endpoint: str,
        record_id: str,
        record: str,
        record_value: str

    ) -> None:
        client = Aliyun_Credential._20150109_create_client(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            endpoint=endpoint
        )
        update_domain_record_request = alidns_20150109_models.UpdateDomainRecordRequest(
            record_id = record_id,
            rr = record,
            type = 'TXT',
            value = record_value
        )
        runtime = util_models.RuntimeOptions()
        try:
            client.update_domain_record_with_options(update_domain_record_request, runtime)
            logger.success('Record has been successfully updated')
        except Exception as error:
            logger.error(f"Aliyun API Error: {error.message}")
            if hasattr(error, 'data') and error.data:
                logger.error(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)
            sys.exit(error.errno if hasattr(error, 'errno') else 1)

    @staticmethod
    def delete_record(
        
        access_key_id: str,
        access_key_secret: str,
        endpoint: str,
        record_id: str

    ) -> None:
        client = Aliyun_Credential._20150109_create_client(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            endpoint=endpoint
        )
        delete_domain_record_request = alidns_20150109_models.DeleteDomainRecordRequest(
            record_id = record_id
        )
        runtime = util_models.RuntimeOptions()
        try:
            client.delete_domain_record_with_options(delete_domain_record_request, runtime)
            logger.success('Record has been successfully deleted')
        except Exception as error:
            logger.error(f"Aliyun API Error: {error.message}")
            if hasattr(error, 'data') and error.data:
                logger.error(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)
            sys.exit(error.errno if hasattr(error, 'errno') else 1)

class Aliyun_SSL:

    """
    20200407
    """

    def __init__(self):
        pass

    @staticmethod
    def Upload_SSL(

        access_key_id: str,
        access_key_secret: str,
        cert: str,
        key: str,
        name: str,
        cert_id: int,
        endpoint = f'cas.aliyuncs.com'

    ) -> None:
        client = Aliyun_Credential._20200407_create_client(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            endpoint=endpoint
        )
        upload_user_certificate_request = alidns_20200407_models.UploadUserCertificateRequest(
            cert=cert,
            key=key,
            name=name
        )
        runtime = util_models.RuntimeOptions()
        try:
            res = client.upload_user_certificate_with_options(upload_user_certificate_request, runtime).to_map()
            logger.success("SSL has been updated sucessfully!")
            return res
        except Exception as error:
            logger.error(error.message)
            logger.error(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)

    @staticmethod
    def Delete_SSL(
        
        cert_id: int,
        access_key_id: str,
        access_key_secret: str,
        endpoint = f'cas.aliyuncs.com'

    ) -> None:
        client = Aliyun_Credential._20200407_create_client(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            endpoint=endpoint
        )
        delete_user_certificate_request = alidns_20200407_models.DeleteUserCertificateRequest(
            cert_id=cert_id
        )
        runtime = util_models.RuntimeOptions()
        try:
            logger.warning("SSL has been deleted sucessfully!")
            client.delete_user_certificate_with_options(delete_user_certificate_request, runtime)
        except Exception as error:
            logger.error(error.message)
            logger.error(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)

    @staticmethod
    def Get_SSL(

        cert_id: int,
        access_key_id: str,
        access_key_secret: str,
        endpoint = f'cas.aliyuncs.com'

    ) -> None:
        client = Aliyun_Credential._20200407_create_client(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            endpoint=endpoint
        )
        get_user_certificate_detail_request = alidns_20200407_models.GetUserCertificateDetailRequest(
            cert_id=cert_id
        )
        runtime = util_models.RuntimeOptions()
        try:
            res = client.get_user_certificate_detail_with_options(get_user_certificate_detail_request, runtime).to_map()
            return [True,res]
        except Exception as error:
            logger.error(error.message)
            logger.error(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)
            return [False,str(error.message)]

class Aliyun_FC:
    def __init__(self):
        pass

    @staticmethod
    def GetFCDomain(

        access_key_id: str,
        access_key_secret: str,
        user_id: str,
        endpoint: str

    ) -> list:
        client = Aliyun_Credential._20210406_create_client(
            
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            user_id=user_id,
            endpoint=endpoint
        )
        list_custom_domains_headers = alidns_20210406_models.ListCustomDomainsHeaders()
        list_custom_domains_request = alidns_20210406_models.ListCustomDomainsRequest()
        runtime = util_models.RuntimeOptions()
        # 设置更长的超时时间（30秒）
        runtime.read_timeout = 30000  # 毫秒
        runtime.connect_timeout = 10000  # 毫秒
        # try:
        res = client.list_custom_domains_with_options(list_custom_domains_request, list_custom_domains_headers, runtime).to_map()
        return res
        # except Exception as error:
        #     logger.error(error.message)
        #     logger.error(error.data.get("Recommend"))
        #     UtilClient.assert_as_string(error.message)

    def UpdateFCCert(
        
        access_key_id: str,
        access_key_secret: str,
        user_id: str,
        endpoint: str,
        cert: str,
        rsa: str,
        domain: str,
        cert_name: str

    ) -> None:
        client = Aliyun_Credential._20210406_create_client(

            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            user_id=user_id,
            endpoint=endpoint
        )
        update_custom_domain_headers = alidns_20210406_models.UpdateCustomDomainHeaders()
        cert_config = alidns_20210406_models.CertConfig(
            cert_name=cert_name,
            certificate=cert,
            private_key=rsa
        )
        update_custom_domain_request = alidns_20210406_models.UpdateCustomDomainRequest(
            cert_config=cert_config
        )
        runtime = util_models.RuntimeOptions()
        # 设置更长的超时时间（30秒）
        runtime.read_timeout = 30000  # 毫秒
        runtime.connect_timeout = 10000  # 毫秒
        # try:
        return (client.update_custom_domain_with_options(domain, update_custom_domain_request, update_custom_domain_headers, runtime).to_map())
        # except Exception as error:
        #     logger.error(error.message)
        #     logger.error(error.data.get("Recommend"))
        #     UtilClient.assert_as_string(error.message)