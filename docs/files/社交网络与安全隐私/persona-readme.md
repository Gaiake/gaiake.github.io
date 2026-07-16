# OSN-Project Persona 模块

本目录提供基于 `playwright` 的浏览器上下文创建与 persona 配置管理，方便模拟不同用户画像访问目标网站。

## 目录结构

- `persona/profiles/`：各 persona 配置目录
- `persona/src/browser_mana.py`：创建 Playwright 浏览器上下文的辅助函数
- `persona/test/test.py`：示例脚本，用于测试浏览器访问与截图

## 目标网站

当前测试目标包括不需要登录的站点：

- `https://www.tiktok.com`
- `https://www.amazon.com`
- `https://www.youtube.com`

## Persona 配置说明

`persona/profiles/<id>_<name>/persona.json` 示例：

```json
{
  "persona_name": "elderly",
  "profile": {
    "age": 68,
    "gender": "female",
    "location": "Taiwan"
  },
  "interests": [
    "health",
    "news",
    "gardening"
  ],
  "behavior_patterns": {
    "scroll_speed": "slow",
    "reading_time": "long",
    "click_delay_ms": 3000,
    "impulsive_score": 0.2
  },
  "shopping_preferences": {
    "likes_discount": true,
    "high_price_tolerance": false
  },
  "browser_fingerprint": {
    "resolution": "1366x768",
    "timezone": "Asia/Taipei",
    "language": "zh-TW"
  }
}
```

字段说明：

- `behavior_patterns.scroll_speed`：页面滚动速度
- `behavior_patterns.reading_time`：停留/阅读时长
- `behavior_patterns.click_delay_ms`：点击前的延迟
- `behavior_patterns.impulsive_score`：冲动点击概率
- `browser_fingerprint.resolution`：浏览器视口分辨率
- `browser_fingerprint.timezone`：时区
- `browser_fingerprint.language`：页面语言环境

## 浏览器上下文创建

`persona/src/browser_mana.py` 提供 `create_context_for_persona(persona_file)`：

- 从指定 persona 配置文件读取参数
- 在同级目录下创建 `states/` 子目录
- 根据目录前缀生成状态文件名，例如 `01_elderly` -> `01_state.json`
- 如果已有状态文件，则自动加载 `storage_state`
- 默认使用 headless 模式运行，适合没有图形界面的服务器环境

使用示例：

```python
from persona.src.browser_mana import create_context_for_persona

persona_file = "persona/profiles/01_elderly/persona.json"
p, browser, context, persona, state_file = create_context_for_persona(persona_file)
```

## 运行示例

在仓库根目录运行：

```bash
cd /home/jishuifeiyun/OSN-Project
python3 ./persona/test/test.py
```

当前示例脚本会：

- 打开 TikTok 页面
- 滚动页面 5 次
- 每次滚动后保存屏幕截图
- 将浏览器状态存储到对应 `states/` 子目录中

## 看见浏览器窗口

如果你希望看到浏览器窗口，请在支持显示的环境中运行：

```bash
PLAYWRIGHT_HEADLESS=false python3 ./persona/test/test.py
```

如果当前虚拟机没有图形显示环境，请使用 `xvfb-run`：

```bash
xvfb-run python3 ./persona/test/test.py
```



## 注意事项

- 目录名称中的前缀会用于状态文件命名，例如 `01_elderly` -> `01_state.json`
- 如果你在 VS Code Remote 环境中运行时出现 `Missing X server`，说明远程环境没有可用显示，需要使用 `xvfb-run` 或 X11 转发
- 如果你希望截图保存到专用子目录，可以修改 `persona/test/test.py` 的 `screenshot_path`


