<div align="center">

# ✨ AstrBot Plugin - MCStatus ✨
*一款功能强大且可爱的 Minecraft 服务器状态查询插件*

**当前版本**: `v2.1.0` | **Author**: 清蒸云鸭

[![AstrBot Support](https://img.shields.io/badge/AstrBot-Support-blue)](https://astrbot.app)

</div>

## 🎨 功能预览  
✅ **精美渲染**：支持服务器图标渲染、彩色 MOTD 渲染、延迟颜色自适应、进度条展示。  
✅ **多功能查询**：支持查询当前在线人数、最大人数、协议版本。  
✅ **快捷存储**：支持常用服务器的添加、删除、查看、列表展示。  
✅ **灵活配置**：支持分群/全局数据隔离，自动缓存管理，自定义背景与字体。  

![](https://free.picui.cn/free/2025/12/29/69528c2c45858.png)  

---

## 🛠️ 安装方法  

### 🔹 方式一：自动安装（推荐）
在 AstrBot 控制面板的插件市场搜索 `mcstatus` ，点击安装即可。

### 🔹 方式二：手动安装
1. 点击右上角 `<>Code` -> `Download Zip` 下载源码压缩包。
2. 将解压后的文件夹重命名为 `astrbot_plugin_mcstatus`。
3. 移动至 `Astrbot/data/plugins/` 目录下。
4. 重启 AstrBot 即可生效。

### 🔹 方式三：Git Clone 
确保系统已安装 Git，在 `Astrbot/data/plugins/` 目录下打开终端，执行以下命令：
```bash
# 全球/海外/港澳台
git clone https://github.com/WhiteCloudOL/astrbot_plugin_mcstatus.git  

# 大陆地区镜像
git clone https://gh-proxy.com/https://github.com/WhiteCloudOL/astrbot_plugin_mcstatus.git
```
完成后重启 AstrBot 即可载入插件。

---

## ⚙️ 配置文件说明 (`_conf_schema.json`)

在 AstrBot 面板的插件设置中，你可以根据需求自定义以下配置：

### 1. 基础个性化设置
- **字体 (`font`)**: 设置绘图使用的字体。
  - 默认值: `cute_font.ttf`
  - *提示：如果需要自定义字体，请将 `.ttf` 字体文件放入插件的 `assets/` 目录下，并在此填写文件名。*
- **背景 (`bg`)**: 设置卡片渲染的背景图片。
  - 默认值: `bg.jpg`
  - *提示：可自定义 `.jpg` 或 `.png` 格式的背景图放入 `assets/` 目录，并在此填写文件名。*
- **缓存管理 (`max_temp`)**: 生成的最大临时图片缓存数量。
  - 默认值: `5`
  - *提示：生成的查询图片会缓存在插件的 `data/` 目录下，超过该数量会自动清理最旧的图片，以节省空间。*

### 2. 数据分群控制 (`divide_group`)
这里用于控制插件存储数据的方式和指令响应范围：
- **启用分群存储 (`divide_data`)**:
  - `false` (默认)：全局模式。所有群聊和私聊共用一份“常用服务器”列表。
  - `true`：隔离模式。每个群聊保存自己的“常用服务器”列表，私聊则保存个人的“常用服务器”列表。
- **阻止模式 (`block_method`)**:
  - `blacklist` (默认)：黑名单模式。填在下方列表中的群号**将无法**使用该插件。
  - `whitelist`：白名单模式。**只有**填在下方列表中的群号才可以使用该插件。
- **名单列表 (`control_list`)**:
  - 填写具体的群号（例如 `123456789`）。结合上方的阻止模式使用。

---

## ⌨️ 插件命令

插件主命令为 `/mcstatus`。  
支持别名缩写：`/mc状态`、`/MC状态`、`/mcs`。  

### 可用指令列表
| 指令 | 示例用法 | 描述 |
| :--- | :--- | :--- |
| **help** | `/mcs help` | 获取带排版的精美帮助菜单 |
| **motd** | `/mcs motd mc.example.com` | 获取指定 IP 的服务器状态和延迟 |
| **look** | `/mcs look 我的世界` | 快捷查询已保存的服务器状态 |
| **list** | `/mcs list` | 展示当前（群组/全局）已保存的服务器列表 |
| **add** | `/mcs add 我的世界 mc.example.com` | 添加一个常用服务器到列表 |
| **set** | `/mcs set 我的世界 mc.new.com` | 更新已存服务器的 IP 地址 |
| **del** | `/mcs del 我的世界` | 从保存列表中删除指定服务器 |
| **clear** | `/mcs clear` | 清空当前范围下的所有保存记录 (*仅限管理员*) |
| **players**| `/mcs players mc.example.com` | 同 `motd`（功能整合优化中） |

*(提示：所有带有地址的命令支持域名、IP，甚至附带端口，如 `127.0.0.1:25566`)*

---

## 📝 TODO List
- [x] 分群存储数据机制
- [x] 多线程网络请求异常处理增强
- [x] 动态独立图片生成及滚动缓存清理机制
- [ ] List 列表的分页查询功能

---

## 📞 支持
如果你喜欢这个插件，欢迎去 Github 给个 ⭐ 噢！  
相关框架问题请访问：[AstrBot 帮助文档](https://astrbot.app)
