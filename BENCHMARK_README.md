# 向量搜索接口压测工具

用于测试向量搜索接口性能的压测工具，支持并发梯度测试、响应模式对比、自动熔断保护。

---

## 快速开始

### 1. 环境准备

```bash
# Python 版本要求
Python 3.7+

# 安装依赖
pip install httpx
```

### 2. 服务端监控（可选）

在目标服务器上运行监控脚本：

```bash
# 赋予执行权限
chmod +x monitor.sh

# 实时监控
./monitor.sh

# 或后台运行并保存日志
./monitor.sh > monitor.log 2>&1 &
```

### 3. 执行压测

```bash
# 基础用法 - 压测指定服务
python3 benchmark_remote.py --url http://your-server:8009

# 自定义并发梯度
python3 benchmark_remote.py \
  --url http://your-server:8009 \
  --concurrency 50 100 150 200

# 自定义请求数
python3 benchmark_remote.py \
  --url http://your-server:8009 \
  --concurrency 100 150 200 \
  --requests 1000 2000 3000

# 指定报告输出路径
python3 benchmark_remote.py \
  --url http://your-server:8009 \
  --output my_report.md

# 跳过响应模式对比测试
python3 benchmark_remote.py \
  --url http://your-server:8009 \
  --skip-mode-test
```

### 4. 查看报告

```bash
# 查看报告
cat benchmark_report.md

# 或在浏览器中打开（如果有 Markdown 渲染）
open benchmark_report.md
```

---

## 参数说明

### benchmark_remote.py

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--url` | ✅ | - | 目标服务 URL，例如 `http://localhost:8009` |
| `--concurrency` | ❌ | `100 150 200` | 并发梯度列表 |
| `--requests` | ❌ | `2000 3000 5000` | 请求数列表 |
| `--output` | ❌ | `benchmark_report.md` | 报告输出路径 |
| `--skip-mode-test` | ❌ | - | 跳过响应模式对比测试 |

### monitor.sh

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `interval` | `1` | 刷新间隔（秒） |
| `count` | `0` | 刷新次数（0=无限） |

```bash
# 示例
./monitor.sh              # 1秒刷新，无限次
./monitor.sh 5            # 5秒刷新，无限次
./monitor.sh 1 100        # 1秒刷新，100次后停止
```

---

## 压测场景

### 场景 A：并发梯度测试

测试不同并发下的性能表现：

| 轮次 | 并发 | 请求数 | 目的 |
|------|------|--------|------|
| A1 | 100 | 2000 | 基准性能 |
| A2 | 150 | 3000 | 性能衰减 |
| A3 | 200 | 5000 | 压力测试 |

### 场景 B：响应模式对比

测试不同响应模式的性能：

| 模式 | 并发 | 请求数 | 说明 |
|------|------|--------|------|
| basic | 100 | 1000 | 仅返回 id/text/score |
| normal | 100 | 1000 | 返回含 raw_data |
| complete | 100 | 1000 | 返回全量数据 |

---

## 熔断保护

为避免压垮服务，脚本内置熔断机制：

| 条件 | 阈值 | 说明 |
|------|------|------|
| 错误率 | 30% | 错误率超过 30% 自动停止 |
| 平均延迟 | 5秒 | 平均延迟超过 5 秒自动停止 |
| 单请求超时 | 30秒 | 单个请求超时 30 秒 |

---

## 报告内容

生成的报告包含：

1. **测试概览** - 总请求数、成功率、失败数
2. **并发梯度测试** - 详细结果、性能分析
3. **响应模式对比** - 三种模式性能对比
4. **性能评估** - 性能等级、峰值 QPS
5. **容量规划建议** - 单实例容量、多实例部署
6. **优化建议** - 短期/中期/长期优化建议

---

## 监控指标

### monitor.sh 监控内容

| 指标 | 说明 |
|------|------|
| CPU 使用率 | 整体 CPU 使用百分比 |
| 内存使用率 | 已用/总内存 |
| Python 进程数 | Python/uvicorn 进程数量 |
| 网络连接数 | 8009 端口的 ESTABLISHED 连接 |
| 磁盘使用率 | 根分区使用情况 |
| 系统负载 | 1分钟/5分钟/15分钟负载 |

---

## 使用示例

### 示例 1：测试本地服务

```bash
# 终端 1：启动服务
cd lib-resource-service
uvicorn app.main:app --port 8009

# 终端 2：启动监控
./monitor.sh

# 终端 3：执行压测
python3 benchmark_remote.py --url http://localhost:8009
```

### 示例 2：测试生产服务

```bash
# 在压测机上执行
python3 benchmark_remote.py \
  --url http://prod-server:8009 \
  --concurrency 100 150 200 \
  --output prod_benchmark.md
```

### 示例 3：CI/CD 集成

```bash
# 在 CI 流水线中执行
python3 benchmark_remote.py \
  --url http://test-server:8009 \
  --concurrency 50 100 \
  --requests 500 1000 \
  --skip-mode-test \
  --output ci_report.md

# 检查报告中的性能指标
grep "峰值 QPS" ci_report.md
```

---

## 注意事项

### ⚠️ 生产环境压测风险

1. **性能影响** - 高并发可能导致服务响应慢，建议在低峰期执行
2. **数据污染** - 压测请求会写入数据库，建议使用测试账号
3. **资源占用** - 压测机会占用 CPU/内存，建议使用独立机器

### ✅ 最佳实践

1. **逐步提升** - 从低并发开始，逐步提升
2. **监控服务** - 压测时同时监控服务端资源
3. **预留余量** - 生产环境按峰值 2-3 倍规划容量
4. **设置熔断** - 错误率超过阈值立即停止

---

## 故障排查

### 问题 1：连接失败

```bash
❌ 服务状态: 异常 - Connection refused
```

**解决方案**：
- 检查服务是否启动：`curl http://server:8009/api/resources/categories`
- 检查防火墙规则：`iptables -L` 或 `ufw status`
- 检查端口监听：`netstat -tlnp | grep 8009`

### 问题 2：依赖缺失

```bash
ModuleNotFoundError: No module named 'httpx'
```

**解决方案**：
```bash
pip install httpx
```

### 问题 3：权限不足

```bash
bash: ./monitor.sh: Permission denied
```

**解决方案**：
```bash
chmod +x monitor.sh
```

---

## 性能参考

基于本地测试的结果：

| 并发 | QPS | 平均延迟 | P99 |
|------|-----|----------|-----|
| 100 | 125 | 778ms | 978ms |
| 150 | 78 | 1828ms | 2287ms |
| 200 | 42 | 4511ms | 5070ms |

**推荐配置**：
- 安全并发：100
- 极限并发：150（需监控）
- 目标 QPS：100-150

---

## 更新日志

- **2026-07-17**: 初始版本
  - 支持并发梯度测试
  - 支持响应模式对比
  - 支持自动熔断
  - 支持服务端监控

---

## 相关文件

- `benchmark_remote.py` - 通用压测脚本
- `monitor.sh` - 服务端监控脚本
- `benchmark_report.md` - 基础压测报告
- `benchmark_extreme_report.md` - 极限压测报告