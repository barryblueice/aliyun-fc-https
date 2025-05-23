# **Aliyun FC Https**

~~基于certbot的阿里云函数计算https自动续期脚本。~~</br>
基于certbot的阿里云https自动续期脚本，可用于函数计算、异地主机域名SSL等服务。

初衷是为了给部署在阿里云函数计算FC的轻量静态网页添加Let's Encrpypt免费证书，同时做一个脚本更新SSL。

> [!CAUTION]
> 脚本仅支持Linux系统。</br>脚本仅支持Python 3.9.2及以上版本。</br>更新时间为证书到期的前一个月。

# **如何部署**

1. 根据这两篇教程部署网站+SSL证书：
 - [笔记：如何使用阿里云函数计算部署静态网页（如果只是更新证书可以不看）](https://www.bilibili.com/opus/1024609365265481753)
 - [笔记：给阿里云函数计算网站添加SSL证书（必看）](https://www.bilibili.com/opus/1029687408197632003)

2. clone本项目并cd：
```python
git clone https://github.com/barryblueice/aliyun-fc-https.git
cd aliyun-fc-https
``` 

3. 通过poetry安装依赖：

```bash
poetry install
```

4. 第一次运行后，编辑.env文件：

```bash
poetry run python main.py
vim ./.env
```

5. 编辑完成后重新运行脚本，后续可自动续期：

```bash
poetry run python main.py
```

### .env文件范例如下：

```bash
AccessKey_ID=<accesskey_id>
AccessKey_Secret=<accesskey_secret>
User_ID=

Endpoint=alidns.cn-hangzhou.aliyuncs.com
Domain=example.com
Record=_acme-challenge
Record_Value=<record_value>

Key_Path=/etc/letsencrypt/live/example.com
Cert_Id=00000000

FC-Update=0

# Endpoint 请参考 https://api.aliyun.com/product/Alidns
```

***

AccessKey_ID和AccessKey_Secret需要去[阿里云Access Key](https://ram.console.aliyun.com/profile/access-keys)**创建云账号AccessKey**后获取。

User_ID是你的阿里云账号ID，在阿里云官网右上角的用户信息中可以获取：![image](https://github.com/user-attachments/assets/9f0f04f5-f4c6-49d7-aa04-e695d4e03c3e)

![image](https://github.com/user-attachments/assets/51f1238c-be85-450b-9764-ef63e1f16411)

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

> [!CAUTION]
> 如果使用certbot默认的保存目录，则脚本需要在root环境下运行。

***

Cert_Id从阿里云-数字证书管理服务控制台-SSL证书管理获取，你原本上传的证书下CertIdentifier开头那8位数字就是：

![image](https://github.com/user-attachments/assets/3f20f4d0-bb03-4fc3-bd6d-30cb9fe655a7)

~~其实脚本默认有提供一个解析新增+SSL自动生成方案：</br>当没有检测到对应的TXT域名解析，以及符合要求的SSL证书后，脚本会自动添加一个TXT记录并自动添加SSL证书。</br>虽然这样会有点画蛇添足的意味，但是这些功能并没有删除。~~

FC-Update为是否更新函数计算下的所有已绑定域名。默认为0，即不更新；若参数为1，则每次更新SSL证书后都会同步更新函数计算下的所有已绑定域名。

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
