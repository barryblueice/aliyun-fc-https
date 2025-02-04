# **Aliyun FC Https**

基于certbot的阿里云函数计算https自动续期脚本。

> [!CAUTION]\
> 脚本仅支持Linux系统。

# **如何部署**

1. 根据这两篇教程部署网站+SSL证书：
 - [笔记：如何使用阿里云函数计算部署静态网页](https://www.bilibili.com/opus/1024609365265481753)
 - [笔记：给阿里云函数计算网站添加SSL证书](https://www.bilibili.com/opus/1029687408197632003)

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

***

AccessKey_ID和AccessKey_Secret需要去[阿里云Access Key](https://ram.console.aliyun.com/profile/access-keys)**创建云账号AccessKey**后获取。

Endpoint根据你函数计算所使用的地域填写，比如我函数计算使用的是华东1杭州，那么Endpoint地址为alidns.cn-hangzhou.aliyuncs.com。[Endpoint参考可以看这里](https://api.aliyun.com/product/Alidns)。

Record和Record_Value是在certbot初始化配置阶段仅出现一次的参数：

```bash
Please deploy a DNS TXT record under the name:

_acme-challenge.example.com # 这里需要设置域名解析，需要到域名后台填写信息（Record）

with the following value:

xxxxxxxxxxxxxxxxxxx # 这里是域名解析的内容（Record_Value）
```

***

Key_path为SSL证书的保存目录，默认为/etc/letsencrypt/live。

> [!CAUTION]\
> 如果使用certbot默认的保存目录，则脚本需要在root环境下运行。

***

Cert_Id从阿里云-数字证书管理服务控制台-SSL证书管理获取，你原本上传的证书下CertIdentifier开头那8位数字就是：

![image](https://github.com/user-attachments/assets/16ca3c94-be76-463c-8958-e96778d35bbb)

~~其实脚本默认有提供一个SSL自动生成方案，当没有检测到符合要求的SSL证书后会自动生成并上传。</br>感觉这样有点画蛇添足的意味，但是这个功能并没有删除。~~
