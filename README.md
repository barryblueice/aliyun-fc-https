# **Aliyun FC Https**

基于certbot的阿里云函数计算https自动续期脚本。

> [!CAUTION]\
> 脚本需要在root环境下运行。

# **如何部署**

1. 根据这两篇教程部署网站：
 - [笔记：如何使用阿里云函数计算部署静态网页](https://www.bilibili.com/opus/1024609365265481753)
 - [笔记：给阿里云函数计算网站添加SSL证书（可选）](https://www.bilibili.com/opus/1029687408197632003)

2. 通过poetry安装依赖：

```bash
poetry install
```

3. 第一次运行后，编辑.env文件：

```bash
poetry run python main.py
vim ./.env
```

4. 编辑完成后重新运行脚本，后续可自动续期：

```bash
poetry run python main.py
```

### .env文件范例如下：

```bash
AccessKey_ID=<accesskey_id>
AccessKey_Secret=<accesskey_secret>
Endpoint=alidns.cn-hangzhou.aliyuncs.com

Domain=barryblueice.cn
Record=_acme-challenge
Record_Value=<record_value>

Key_Path=/etc/letsencrypt/live/example.com
Cert_Id=00000000

# Endpoint 请参考 https://api.aliyun.com/product/Alidns
```
