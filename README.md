# **Aliyun FC Https**

基于certbot的阿里云函数计算https自动续期脚本。


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
