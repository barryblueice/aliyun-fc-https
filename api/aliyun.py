# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import os
import sys

from typing import List
from loguru import logger

from alibabacloud_alidns20150109.client import Client as Alidns20150109Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_alidns20150109 import models as alidns_20150109_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

from alibabacloud_cas20200407.client import Client as Alidns20200407Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_cas20200407 import models as alidns_20200407_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

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
            logger.error(error.message)
            logger.error(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)
            sys.exit(error.errno)

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
            logger.error(error.message)
            logger.error(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)
            sys.exit(error.errno)

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
