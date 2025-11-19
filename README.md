# Astrbot Plugin MCStatus
v1.0.6
AstrBot Plugin - MCStatus  
Author: WhiteCloudCN  

# 安装  
### 自动安装
Astrbot插件市场搜索 mcstatus 即可自动下载  

### 手动安装
1. 方式一：直接下载：  
点击右上角`<>Code`->`Download Zip`下载压缩包  
打开`Astrbot/data/plugins/`下载本仓库文件，创建`astrbot_plugins_mcstatus`目录，解压所有文件到此目录即可  
2. 方式二：Git Clone方法  
请确保系统已经安装git  
打开目录`Astrbot/data/plugins/`，在此目录下启动终端执行:  
```bash
# 全球/海外/港澳台
git clone https://github.com/WhiteCloudOL/astrbot_plugin_mcstatus.git  

# 大陆地区#1
git clone https://gh-proxy.com/https://github.com/WhiteCloudOL/astrbot_plugin_mcstatus.git

# 大陆地区#2
git clone https://cdn.gh-proxy.com/https://github.com/WhiteCloudOL/astrbot_plugin_mcstatus.git
```
以上命令任选其一执行即可  

3. 完成后重启Astrbot即可载入插件

# 用法  
`/mcstatus help/motd/list/players/look/add/set/del/clear` 插件主命令  
`/draw [text] `绘制图片  
推荐使用`/mcstatus help`获取帮助  
插件命令别名可用`mc状态` `MC状态` `mcs`  
例如`/mcs motd mc.catyun.cyou`  


# 更新日志  
### v1.0.3  
*（2025/10/09）*  
1. 新增主命令别名：mc状态、MC状态、mcs  
2. 查询结果新增玩家列表  
### v1.0.4  
*(2025/10/10)*  
1. 添加SRV解析支持  
### v1.0.5  
*(2025/10/17)*  
1. 修复：f-String错误导致的插件无法正常  

# TODO
❌分群存储  
❌list分页查询  

# 支持
[Astrbot帮助文档](https://astrbot.app)
