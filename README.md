# **Aliyun FC Https**

~~基于certbot的阿里云函数计算https自动续期脚本。~~</br>
~~基于certbot的阿里云https自动续期脚本，可用于函数计算、异地主机域名SSL等服务。~~</br>
基于ACME的阿里云https自动续期脚本，可用于函数计算、异地主机域名SSL等服务。

初衷是为了给部署在阿里云函数计算FC的轻量静态网页添加Let's Encrpypt免费证书，同时做一个脚本更新SSL。

> [!CAUTION]
> 脚本仅支持Python 3.9.2及以上版本。
>

## 工作流程

1. 直接连接配置的ACME Directory创建订单。
2. 通过AliDNS API创建或更新`_acme-challenge` TXT记录。
3. 完成DNS-01验证并保存证书、私钥和ACME账户密钥。
4. 上传新证书到阿里云数字证书管理服务。
5. `FC-Update=1` 时更新匹配的函数计算自定义域名。
6. 删除临时TXT记录；若原来已有同名TXT记录，则恢复原值。


# **如何部署**

1. clone本项目并cd：
```python
git clone https://github.com/barryblueice/aliyun-fc-https.git
cd aliyun-fc-https
```

2. 通过poetry安装依赖：

```bash
poetry install
```

3. 第一次运行后，编辑.env文件：

```bash
poetry run python main.py
```

4. 填写 `.env` 后，再执行一次即可签发和部署首张证书：

```bash
poetry run python main.py --once
```

5. 常驻运行时，程序启动后会立即检查，之后每 12 小时检查一次：

```bash
poetry run python main.py
```

6. 忽略续期窗口并立即重签一次：

```bash
poetry run python main.py --once --force
```

强制续期会向CA创建新订单，请避免频繁使用，以免触发CA的频率限制。

## 配置

```dotenv
AccessKey_ID=<accesskey_id>
AccessKey_Secret=<accesskey_secret>
User_ID=

Endpoint=alidns.cn-hangzhou.aliyuncs.com
Domain=example.com
Record=_acme-challenge

Key_Path=./certs/example.com
ACME_Email=admin@example.com
ACME_Directory_URL=https://acme-v02.api.letsencrypt.org/directory
DNS_Propagation_Seconds=30
RSA_Key_Size=2048
Renew_Before_Days=30

Cert_Id=
FC-Update=0
```

- `AccessKey_ID` / `AccessKey_Secret`：用于AliDNS、数字证书管理服务以及可选的FC更新。建议使用权限最小化的RAM用户。
- `User_ID`：阿里云账号ID。
- `Endpoint`：AliDNS地域Endpoint，默认为`alidns.cn-hangzhou.aliyuncs.com`。
- `Domain`：根域名，不要填写`*.`；当前签发的证书只包含`*.Domain`，不包含根域名本身。
- `Record`：DNS-01 使用的相对记录名，通常保持`_acme-challenge`。
- `Key_Path`：证书保存目录。相对路径以项目根目录为基准，Windows和Unix路径均可。
- `ACME_Email`：ACME 账户联系邮箱；留空时使用 `admin@Domain`。
- `ACME_Directory_URL`：自定义ACME Directory地址，默认为Let’s Encrypt，并兼容其他ACME v2 / RFC 8555证书服务商。
- `DNS_Propagation_Seconds`：提交验证前等待DNS生效的秒数。如果解析生效较慢，可适当增大。
- `RSA_Key_Size`：RSA 私钥位数，最小为2048。
- `Renew_Before_Days`：距到期多少天时开始续期。
- `Cert_Id`：已有阿里云证书ID。首次使用可以留空，上传成功后程序会自动回填。
- `FC-Update`：设为 `1` 时，同步更新当前账号下由通配符证书覆盖的一级子域名；根域名和多级子域名不会被误更新。

***

AccessKey_ID和AccessKey_Secret需要去[阿里云Access Key](https://ram.console.aliyun.com/profile/access-keys)**创建云账号AccessKey**后获取。

User_ID是你的阿里云账号ID，在阿里云官网右上角的用户信息中可以获取：![image](https://github.com/user-attachments/assets/9f0f04f5-f4c6-49d7-aa04-e695d4e03c3e)

![image](https://github.com/user-attachments/assets/51f1238c-be85-450b-9764-ef63e1f16411)

Endpoint根据你函数计算所使用的地域填写，比如我函数计算使用的是华东1杭州，那么Endpoint地址为alidns.cn-hangzhou.aliyuncs.com。[Endpoint参考可以看这里](https://api.aliyun.com/product/Alidns)。

# **持久化运行**：

可以使用[MCSManager](https://github.com/MCSManager/MCSManager)、[1Panel](https://1panel.cn/)、[宝塔面板](https://www.bt.cn/new/index.html)这类WebUI管理工具进行持久化运行，也可通过nohup、screen等Linux命令行工具设置后台运行。

同时也可设置Linux systemd进行后台持久化运行：

```bash
vim /etc/systemd/system/aliyun-fc-https.service

# 按下"i"进行编辑，以下内容复制到编辑器中

[Unit]
Description=Aliyun-FC-HTTPS Daemon
After=network.target

[Service]
WorkingDirectory=/path/to/the/project/directory
ExecStart=/path/to/poetry run python main.py
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s QUIT $MAINPID
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONUNBUFFERED=1"
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=aliyun-fc-https
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target

# 输入":wq!"保存，保存重载系统服务后运行：

systemctl daemon-reload
systemctl enable --now aliyun-fc-https

# 单独运行服务

systemctl start aliyun-fc-https

# 停止服务

systemctl stop aliyun-fc-https

# 重启服务

systemctl restart aliyun-fc-https

# 查看运行情况

systemctl status aliyun-fc-https

# 查看日志

journalctl -u aliyun-fc-https
```

还可以通过init.d设置持久化运行：

```bash

vim /etc/init.d/aliyun-fc-https

# 按下"i"进行编辑，以下内容复制到编辑器中

#!/bin/bash
### BEGIN INIT INFO
# Provides:          aliyun-fc-https
# Required-Start:    $network
# Required-Stop:     $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Aliyun FC HTTPS Daemon
# Description:       Aliyun FC HTTPS Daemon

NAME="aliyun-fc-https"
PYTHON_BIN="/path/to/poetry"
WORKDIR="/path/to/the/project/directory"
SCRIPT="main.py"
PIDFILE="/var/run/$NAME.pid"
LOGFILE="/var/log/$NAME.log"

start() {
    echo "Starting $NAME..."
    if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
        echo "$NAME is already running."
        return 1
    fi

    cd $WORKDIR
    $PYTHON_BIN run python $SCRIPT >> "$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    echo "$NAME started."
}

stop() {
    echo "Stopping $NAME..."
    if [ ! -f "$PIDFILE" ] || ! kill -0 $(cat "$PIDFILE") 2>/dev/null; then
        echo "$NAME is not running."
        return 1
    fi

    kill -QUIT $(cat "$PIDFILE") && rm -f "$PIDFILE"
    echo "$NAME stopped."
}

reload() {
    echo "Reloading $NAME..."
    if [ ! -f "$PIDFILE" ] || ! kill -0 $(cat "$PIDFILE") 2>/dev/null; then
        echo "$NAME is not running, cannot reload."
        return 1
    fi

    kill -HUP $(cat "$PIDFILE")
    echo "$NAME reloaded."
}

status() {
    if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
        echo "$NAME is running with PID $(cat "$PIDFILE")."
    else
        echo "$NAME is not running."
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    reload)
        reload
        ;;
    restart)
        stop
        start
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|stop|reload|restart|status}"
        exit 1
        ;;
esac

chmod +x /etc/init.d/aliyun-fc-https

# 输入":wq!"保存，保存重载系统服务后运行：

chmod +x /etc/init.d/aliyun-fc-https
update-rc.d aliyun-fc-https defaults

# 单独运行服务

service aliyun-fc-https start

# 停止服务

service aliyun-fc-https stop

# 重启服务

service aliyun-fc-https restart

# 查看运行情况

service aliyun-fc-https status
```
