# 图片语义生成 — 接入文档

「图片语义生成」是详情侧边栏里的功能：点击预览图下方的按钮，系统对该资源的预览图调用图片理解模块，生成一段中文语义描述，用户可将其一键填入描述字段并保存。

本文档说明如何把真实的 `understand_image` 模块接入系统。

---

## 一、整体调用链

```
前端「图片语义生成」按钮
  SemanticUnderstand 组件（lib-resource-ui/src/components/SemanticUnderstand.tsx）
        │  POST /api/resources/{id}/understand
        ▼
routers/resources.py :: understand_resource        # 路由入口（def 同步函数，FastAPI 自动放入线程池）
        ▼
services/image_service.py :: understand_image      # 查库、校验、解析预览图绝对路径
        ▼
clients/external.py :: understand_image            # USE_MOCK 开关在这里
        ▼
clients/image_understanding.py :: understand_image # ★ 真实模块（当前为占位文件）
```

系统已完成除最后一环之外的全部逻辑。**接入方只需要提供最后一环。**

---

## 二、接入步骤（模块提供方）

### 1. 替换占位文件

用真实实现整体替换 `app/clients/image_understanding.py`，保持函数签名不变：

```python
def understand_image(image_path: str) -> str:
    """
    入参:  image_path — 图片文件的绝对路径（本机磁盘上可直接 open 的路径）
    返回:  图片的中文语义描述文本
    失败:  抛出任意异常即可，上层统一捕获并转为 HTTP 502
    """
```

约定：

| 项 | 约定 |
|---|---|
| 入参 | 图片的**绝对路径**，路径解析由系统负责，模块不需要关心资源类型和存储结构 |
| 返回 | 纯文本中文描述（`str`），不要包 JSON、不要混入错误信息 |
| 失败 | 直接抛异常，异常信息会透传给前端提示，建议写成人类可读的中文 |
| 执行方式 | **同步阻塞**即可，单张 10~30 秒可接受；路由层已用线程池承载，不会阻塞其他请求 |
| 图片格式 | 至少支持 png / jpg；系统会传预览图（png 为主）和用户上传的原图 |

### 2. 依赖与配置

- 新增的 Python 依赖 → 追加到 `requirements.txt`
- 需要 API key、服务地址等配置 → 在 `app/config.py` 的 `Settings` 里加属性（从环境变量读取），并在 `.env.example` 补一行说明，模块内 `from app.config import settings` 读取。**不要把密钥写死在代码里。**

### 3. 打开真实调用

`.env` 中：

```env
USE_MOCK=false
```

`USE_MOCK=true` 时走 Mock（sleep 2 秒后返回固定假描述），不会触碰真实模块——本地前端联调用这个模式即可，无需等真实模块就绪。

---

## 三、系统侧行为（已实现，无需改动）

### 取图规则

`services/image_service.py :: understand_image`：

| 资源类型 | 用哪张图 |
|---|---|
| 图片（resource_type=5） | 优先原图 `file_path`，无则用 `thumbnail_path` |
| 组件集 / 模版 / SVG / 插画 | 预览图 `thumbnail_path` |

相对路径统一按 `FILE_ROOT_DIR + 相对路径` 解析为绝对路径后传给模块。

### 接口定义

```
POST /api/resources/{resource_id}/understand
```

无请求体。响应：

```json
{ "id": 89, "description": "画面主体是……" }
```

错误响应（`{"detail": "..."}`）：

| 状态码 | 场景 |
|---|---|
| 404 | 资源不存在 / 已软删除；预览图文件在磁盘上不存在 |
| 400 | 资源没有 `thumbnail_path`（图片类型则连 `file_path` 也没有） |
| 502 | 理解模块抛异常，`detail` 为 `图片语义生成失败: <异常信息>` |

### 前端行为

- 五类资源的详情侧边栏共用 `SemanticUnderstand` 组件，点击后按钮进入 loading（提示“生成中，预计需 10~30 秒”）并禁用防重复提交
- 结果展示在按钮下方，点「追加到描述」把生成文本换行追加到描述输入框末尾（不覆盖原描述，用户可自行增删），再点「保存」才落库；**生成结果本身不自动落库**
- 切换资源 / 关闭抽屉会清空上次结果，迟到的响应会被丢弃

---

## 四、验证

```bash
cd lib-resource-service && venv/bin/uvicorn app.main:app --port 8009
```

```bash
# 正常场景（换成库里真实存在且有预览图的资源 id）
curl -X POST http://localhost:8009/api/resources/89/understand
# 期望: {"id":89,"description":"..."}

# 异常场景
curl -X POST http://localhost:8009/api/resources/999999/understand   # 404 资源不存在
```

接入真实模块后建议依次确认：

1. `USE_MOCK=true` 时上述 curl 返回 Mock 描述（说明链路通）
2. `USE_MOCK=false` 时返回真实描述，且耗时在预期内
3. 故意传一张损坏/超大的图片，确认返回 502 且 `detail` 可读
4. 前端五个管理页（组件/模版/SVG/插画/图片）各点一次按钮走通

---

## 五、后续待定项

- **结果落库**：目前生成结果只在前端展示，由用户确认后经「保存」写入 `description`。若真实调用成本高，可考虑生成后自动缓存到数据库，二次打开直接展示（改动点：`understand_resource` 路由内生成后调 `resource_service.update_resource`）。
- **异步化**：若实测单张经常超过 1 分钟，需改为「提交任务返回 task_id + 前端轮询」模式；当前同步方案下前端 fetch 无显式超时，浏览器默认上限约 300 秒。
