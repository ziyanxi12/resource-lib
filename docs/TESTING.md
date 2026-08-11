# 测试体系

## 测试分层

| 层级 | 框架 | 位置 | 运行命令 | 说明 |
|------|------|------|---------|------|
| 前端单元/组件 | Vitest + Testing Library | `lib-resource-ui/src/test/` | `npm run test:unit` | 组件渲染、工具函数、路由 |
| 前端 E2E | Playwright | `lib-resource-ui/e2e/` | `npm run test:e2e` | 浏览器端到端用户流程 |
| 后端 API | pytest + FastAPI TestClient | `lib-resource-service/tests/` | `pytest` | API 端点 CRUD、校验逻辑 |
| CI | GitHub Actions | `.github/workflows/ci.yml` | push/PR 自动触发 | 汇总以上三层 |

---

## 快速运行

### 前端

```bash
cd lib-resource-ui

# 单元测试
npm run test:unit

# E2E 测试（自动启动 dev server）
npm run test:e2e

# 全部
npm test
```

### 后端

```bash
cd lib-resource-service

# 全部测试
pytest

# 单个文件
pytest tests/test_sources.py

# 带覆盖率
pytest --cov=app
```

---

## 前端单元测试（Vitest）

### 配置文件

| 文件 | 说明 |
|------|------|
| `vitest.config.ts` | Vitest 配置，jsdom 环境 |
| `src/test/setup.ts` | 全局 setup：mock localStorage/matchMedia、jest-dom 匹配器 |

### 测试文件

| 文件 | 测试内容 |
|------|---------|
| `src/test/Guide.test.tsx` | slugify 函数、标题 id 生成、锚点点击滚动 |
| `src/test/App.test.tsx` | 路由：`/` → `/home` 重定向、`/overview` 渲染、`/:type` 渲染 |
| `src/test/utils.test.ts` | getUserInfo、isLoggedIn、isWhitelisted、redirectToLogin |

### 环境变量

Vitest 读取 `.env.development`，需确保以下变量存在：

```env
VITE_API_BASE=
VITE_AUTH_AES_KEY=    # 测试用密钥（base64 32 字节）
```

---

## 前端 E2E 测试（Playwright）

### 配置文件

| 文件 | 说明 |
|------|------|
| `playwright.config.ts` | baseURL、webServer 自动启动、chromium |

### 登录态注入

Playwright 通过 `context.addInitScript` 在页面加载前注入 `localStorage.userInfo`，绕过白名单校验：

```ts
await context.addInitScript(() => {
  localStorage.setItem('userInfo', JSON.stringify({
    account: 'admin', nickName: '测试管理员',
    dept: [], deptCode: [], roleID: '1', roles: [],
    uid: 1, userID: '1'
  }))
})
```

### 测试文件

| 文件 | 测试内容 |
|------|---------|
| `e2e/guide.spec.ts` | 首页加载、Markdown 渲染、锚点跳转、路由不被破坏 |
| `e2e/navigation.spec.ts` | 数据总览不跳首页、各导航项路由正确 |

### 运行方式

Playwright 会自动启动 `npm run dev`（配置在 `playwright.config.ts` 的 `webServer`），测试结束后关闭。也可手动启动 dev server 后用 `npx playwright test` 运行。

---

## 后端 API 测试（pytest）

### 配置文件

| 文件 | 说明 |
|------|------|
| `pytest.ini` | testpaths、asyncio_mode |
| `tests/conftest.py` | 提供 `client` fixture：内存 SQLite + create_all + 每测试清表 |

### conftest.py 核心逻辑

```python
@pytest.fixture()
def client():
    # 1. 创建内存 SQLite engine
    # 2. 覆盖 get_db 依赖，返回内存 session
    # 3. Base.metadata.create_all 建表
    # 4. 返回 TestClient(app)
    # 5. yield 后 drop_all 清理
```

使用内存 SQLite（`sqlite://`），不需要真实数据库，每个测试隔离。

### 测试文件

| 文件 | 测试内容 |
|------|---------|
| `tests/test_sources.py` | 来源 CRUD：创建/查询/编辑/删除(回收站)/恢复 |
| `tests/test_groups.py` | 分组 CRUD：创建/查询树/重命名/删除/移动/清空 |
| `tests/test_resources.py` | 资源：列表分页/详情/更新/删除/批量删除 |
| `tests/test_illus_normalize.py` | 搜索日志归一化（已有，已改为 pytest 风格） |

---

## CI（GitHub Actions）

`.github/workflows/ci.yml` 在 push 和 PR 时自动触发：

| Job | 步骤 |
|-----|------|
| frontend | `npm ci` → `tsc --noEmit` → `vitest run` → `npm run build` |
| backend | `pip install -r requirements.txt` → `pytest` |

---

## CDP 手动测试方法

在引入 Playwright 之前，使用 Chrome DevTools Protocol (CDP) 进行手动 E2E 测试。以下为方法记录，已被 Playwright 替代，但在无 Playwright 环境时仍可使用。

### 原理

```
Python 脚本  →  WebSocket  →  Chrome (--remote-debugging-port)  →  页面 DOM
```

### 步骤

1. 启动 Chrome 调试模式：

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9224 \
  --user-data-dir=/tmp/chrome-test \
  --no-first-run \
  --no-default-browser-check \
  "http://localhost:5173/"
```

2. Python 脚本通过 CDP 操作页面：

```python
import json, asyncio, websockets, urllib.request

async def test():
    # 获取页面 WebSocket 地址
    resp = urllib.request.urlopen('http://localhost:9224/json/list')
    page = [p for p in json.loads(resp.read()) if p['type'] == 'page'][0]
    ws_url = page['webSocketDebuggerUrl']

    async with websockets.connect(ws_url) as ws:
        # 注入 localStorage 绕过登录
        await ws.send(json.dumps({
            'id': 1,
            'method': 'Runtime.evaluate',
            'params': {'expression': 'localStorage.setItem("userInfo", JSON.stringify({account:"admin",nickName:"管理员",dept:[],deptCode:[],roleID:"1",roles:[],uid:1,userID:"1"}))'}
        }))
        await ws.recv()

        # 导航到首页
        await ws.send(json.dumps({'id': 2, 'method': 'Page.navigate', 'params': {'url': 'http://localhost:5173/#/home'}}))
        await ws.recv()
        await asyncio.sleep(3)

        # 点击锚点链接
        await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': 'document.querySelector(".guide-body a").click()'}}))
        await ws.recv()
        await asyncio.sleep(1)

        # 验证滚动位置和路由 hash
        await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': 'JSON.stringify({scrollTop: document.querySelector(".guide-body").parentElement.scrollTop, hash: window.location.hash})'}}))
        r = await ws.recv()
        result = json.loads(json.loads(r)['result']['result']['value'])
        print(f"scrollTop={result['scrollTop']}, hash={result['hash']}")

        assert result['scrollTop'] > 0, "页面未滚动"
        assert result['hash'] == '#/home', "路由被破坏"

asyncio.run(test())
```

### 依赖

```bash
pip install websockets
```

### 局限

- 无断言框架，靠 print 判断
- 无自动等待，需手动 `asyncio.sleep`
- JS 报错时返回空值，调试困难
- 不能 CI 自动化（除非用 headless Chrome）
