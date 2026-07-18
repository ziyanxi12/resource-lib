#!/usr/bin/env python3
"""
向量搜索接口通用压测脚本
支持：远程压测、并发梯度测试、响应模式对比、自动熔断

使用方式：
  python3 benchmark_remote.py --url http://your-server:8009
  python3 benchmark_remote.py --url http://your-server:8009 --concurrency 100 150 200
"""

import asyncio
import argparse
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import statistics
import httpx
import sys


class BenchmarkConfig:
    """压测配置"""
    
    # 熔断阈值
    MAX_ERROR_RATE = 0.30      # 错误率超过 30% 停止
    MAX_AVG_LATENCY = 5.0      # 平均延迟超过 5 秒停止
    REQUEST_TIMEOUT = 30       # 单请求超时 30 秒
    
    # 默认压测场景
    DEFAULT_CONCURRENCY = [100, 150, 200]
    DEFAULT_REQUESTS = [2000, 3000, 5000]


class BenchmarkResult:
    """压测结果"""
    
    def __init__(self, name: str, test_type: str = "concurrent"):
        self.name = name
        self.test_type = test_type
        self.total_requests = 0
        self.success_requests = 0
        self.failed_requests = 0
        self.timeout_requests = 0
        self.response_times: List[float] = []
        self.status_codes: Dict[int, int] = {}
        self.errors: List[str] = []
        self.start_time = 0
        self.end_time = 0
    
    def add_result(self, response_time: float, status_code: int, error: str = None, is_timeout: bool = False):
        self.total_requests += 1
        if is_timeout:
            self.timeout_requests += 1
            self.failed_requests += 1
            if error:
                self.errors.append(error)
        elif error:
            self.failed_requests += 1
            self.errors.append(error)
        else:
            self.success_requests += 1
            self.response_times.append(response_time)
        
        self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time
    
    @property
    def qps(self) -> float:
        return self.success_requests / self.duration if self.duration > 0 else 0
    
    @property
    def avg_latency(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0
    
    @property
    def min_latency(self) -> float:
        return min(self.response_times) if self.response_times else 0
    
    @property
    def max_latency(self) -> float:
        return max(self.response_times) if self.response_times else 0
    
    @property
    def p50(self) -> float:
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        return sorted_times[int(len(sorted_times) * 0.5)]
    
    @property
    def p90(self) -> float:
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        return sorted_times[int(len(sorted_times) * 0.9)]
    
    @property
    def p95(self) -> float:
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        return sorted_times[int(len(sorted_times) * 0.95)]
    
    @property
    def p99(self) -> float:
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        return sorted_times[int(len(sorted_times) * 0.99)]
    
    @property
    def p999(self) -> float:
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        return sorted_times[int(len(sorted_times) * 0.999)]
    
    @property
    def error_rate(self) -> float:
        return self.failed_requests / self.total_requests if self.total_requests > 0 else 0
    
    def should_stop(self) -> bool:
        """检查是否需要熔断"""
        if self.total_requests < 50:
            return False
        
        if self.error_rate > BenchmarkConfig.MAX_ERROR_RATE:
            return True
        
        if self.avg_latency > BenchmarkConfig.MAX_AVG_LATENCY:
            return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "test_type": self.test_type,
            "total_requests": self.total_requests,
            "success_requests": self.success_requests,
            "failed_requests": self.failed_requests,
            "timeout_requests": self.timeout_requests,
            "success_rate": f"{self.success_requests / self.total_requests * 100:.2f}%" if self.total_requests > 0 else "0%",
            "error_rate": f"{self.error_rate * 100:.2f}%",
            "duration_sec": round(self.duration, 2),
            "qps": round(self.qps, 2),
            "avg_latency_ms": round(self.avg_latency * 1000, 2),
            "min_latency_ms": round(self.min_latency * 1000, 2),
            "max_latency_ms": round(self.max_latency * 1000, 2),
            "p50_ms": round(self.p50 * 1000, 2),
            "p90_ms": round(self.p90 * 1000, 2),
            "p95_ms": round(self.p95 * 1000, 2),
            "p99_ms": round(self.p99 * 1000, 2),
            "p999_ms": round(self.p999 * 1000, 2),
            "status_codes": self.status_codes,
            "errors": self.errors[:10] if self.errors else []
        }


async def single_request(client: httpx.AsyncClient, url: str, payload: dict) -> tuple:
    """单次请求"""
    start = time.time()
    try:
        resp = await client.post(url, json=payload, timeout=BenchmarkConfig.REQUEST_TIMEOUT)
        elapsed = time.time() - start
        return elapsed, resp.status_code, None, False
    except asyncio.TimeoutError:
        elapsed = time.time() - start
        return elapsed, 0, f"Timeout after {BenchmarkConfig.REQUEST_TIMEOUT}s", True
    except Exception as e:
        elapsed = time.time() - start
        return elapsed, 0, str(e), False


async def run_benchmark(
    name: str,
    url: str,
    payload: dict,
    total_requests: int,
    concurrency: int
) -> BenchmarkResult:
    """执行压测"""
    result = BenchmarkResult(name, "concurrent")
    result.start_time = time.time()
    
    semaphore = asyncio.Semaphore(concurrency)
    completed = 0
    
    async def limited_request(client: httpx.AsyncClient):
        nonlocal completed
        async with semaphore:
            elapsed, status, error, is_timeout = await single_request(client, url, payload)
            result.add_result(elapsed, status, error, is_timeout)
            completed += 1
    
    print(f"\n开始: {name}")
    print(f"  配置: {total_requests} 请求 / {concurrency} 并发")
    
    async with httpx.AsyncClient() as client:
        tasks = [limited_request(client) for _ in range(total_requests)]
        
        for coro in asyncio.as_completed(tasks):
            await coro
            
            if completed % 100 == 0 and completed > 0:
                current_qps = result.success_requests / (time.time() - result.start_time)
                print(f"  进度: {completed}/{total_requests} - QPS: {current_qps:.1f}")
            
            if result.should_stop():
                print(f"  ⚠️ 触发熔断，停止测试")
                break
    
    result.end_time = time.time()
    
    data = result.to_dict()
    print(f"完成:")
    print(f"  成功: {data['success_requests']} | 失败: {data['failed_requests']} | 超时: {data['timeout_requests']}")
    print(f"  QPS: {data['qps']} | 平均延迟: {data['avg_latency_ms']}ms | P99: {data['p99_ms']}ms")
    
    return result


async def run_concurrent_tests(base_url: str, concurrencies: List[int], requests_list: List[int]) -> List[BenchmarkResult]:
    """并发梯度测试"""
    results = []
    search_url = f"{base_url}/api/vector/search"
    payload = {
        "type": "template",
        "queries": ["按钮"],
        "top_k": 10,
        "response_mode": "basic"
    }
    
    for i, concurrency in enumerate(concurrencies):
        requests = requests_list[i] if i < len(requests_list) else concurrency * 20
        name = f"并发测试 - {concurrency}并发"
        
        result = await run_benchmark(name, search_url, payload, requests, concurrency)
        results.append(result)
        
        if result.should_stop():
            print(f"\n达到熔断条件，停止后续测试")
            break
        
        await asyncio.sleep(2)
    
    return results


async def run_mode_tests(base_url: str) -> List[BenchmarkResult]:
    """响应模式对比测试"""
    results = []
    search_url = f"{base_url}/api/vector/search"
    
    modes = [
        ("basic", "基础模式 - 仅返回 id/vector_text/score"),
        ("normal", "普通模式 - 返回 id/vector_text/score/raw_data"),
        ("complete", "完整模式 - 返回全量数据")
    ]
    
    for mode, desc in modes:
        name = f"响应模式测试 - {mode}"
        payload = {
            "type": "template",
            "queries": ["按钮"],
            "top_k": 10,
            "response_mode": mode
        }
        
        result = await run_benchmark(name, search_url, payload, 1000, 100)
        results.append(result)
        
        await asyncio.sleep(1)
    
    return results


def generate_report(results: List[BenchmarkResult], base_url: str) -> str:
    """生成压测报告"""
    lines = []
    
    lines.append("# 向量搜索接口压测报告")
    lines.append("")
    lines.append(f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**测试接口**: POST {base_url}/api/vector/search")
    lines.append(f"**服务地址**: {base_url}")
    lines.append("")
    
    total_requests = sum(r.total_requests for r in results)
    total_success = sum(r.success_requests for r in results)
    total_failed = sum(r.failed_requests for r in results)
    total_timeout = sum(r.timeout_requests for r in results)
    
    lines.append("## 1. 测试概览")
    lines.append("")
    lines.append(f"- **总请求数**: {total_requests}")
    lines.append(f"- **成功请求**: {total_success} ({total_success/total_requests*100:.2f}%)")
    lines.append(f"- **失败请求**: {total_failed} ({total_failed/total_requests*100:.2f}%)")
    lines.append(f"- **超时请求**: {total_timeout}")
    lines.append("")
    
    concurrent_results = [r for r in results if "并发测试" in r.name]
    mode_results = [r for r in results if "响应模式" in r.name]
    
    if concurrent_results:
        lines.append("## 2. 并发梯度测试")
        lines.append("")
        
        lines.append("### 2.1 测试结果")
        lines.append("")
        lines.append("| 并发数 | 总请求 | 成功 | 失败 | 超时 | QPS | 平均延迟(ms) | P50(ms) | P90(ms) | P99(ms) | 成功率 |")
        lines.append("|--------|--------|------|------|------|-----|-------------|---------|---------|---------|--------|")
        
        for r in concurrent_results:
            d = r.to_dict()
            concurrency = d['name'].split('-')[1].replace('并发', '').strip()
            lines.append(
                f"| {concurrency} | {d['total_requests']} | {d['success_requests']} | "
                f"{d['failed_requests']} | {d['timeout_requests']} | {d['qps']} | "
                f"{d['avg_latency_ms']} | {d['p50_ms']} | {d['p90_ms']} | {d['p99_ms']} | {d['success_rate']} |"
            )
        
        lines.append("")
        
        lines.append("### 2.2 性能分析")
        lines.append("")
        
        if concurrent_results:
            valid_results = [r for r in concurrent_results if r.qps > 0]
            if valid_results:
                max_qps = max(r.qps for r in valid_results)
                max_qps_name = max(valid_results, key=lambda r: r.qps).name
                
                lines.append(f"- **峰值 QPS**: {max_qps:.2f}")
                lines.append(f"- **峰值场景**: {max_qps_name}")
                lines.append("")
                
                lines.append("**并发与性能关系**:")
                lines.append("")
                lines.append("| 并发数 | QPS | 平均延迟(ms) | P99(ms) |")
                lines.append("|--------|-----|-------------|---------|")
                
                for r in concurrent_results:
                    d = r.to_dict()
                    concurrency = d['name'].split('-')[1].replace('并发', '').strip()
                    lines.append(f"| {concurrency} | {d['qps']} | {d['avg_latency_ms']} | {d['p99_ms']} |")
                
                lines.append("")
                
                safe_results = [r for r in concurrent_results if r.error_rate < 0.05]
                if safe_results:
                    best = max(safe_results, key=lambda r: r.qps)
                    best_concurrency = best.name.split('-')[1].replace('并发', '').strip()
                    lines.append(f"- **推荐并发数**: {best_concurrency}（错误率 < 5%）")
                else:
                    lines.append("- **警告**: 所有测试场景错误率均超过 5%")
        
        lines.append("")
    
    if mode_results:
        lines.append("## 3. 响应模式对比")
        lines.append("")
        
        lines.append("| 响应模式 | 总请求 | 成功 | QPS | 平均延迟(ms) | P99(ms) |")
        lines.append("|----------|--------|------|-----|-------------|---------|")
        
        for r in mode_results:
            d = r.to_dict()
            mode = d['name'].split('-')[1].strip()
            lines.append(
                f"| {mode} | {d['total_requests']} | {d['success_requests']} | "
                f"{d['qps']} | {d['avg_latency_ms']} | {d['p99_ms']} |"
            )
        
        lines.append("")
        
        lines.append("**分析**:")
        lines.append("")
        if len(mode_results) >= 2:
            basic = next((r for r in mode_results if "basic" in r.name), None)
            complete = next((r for r in mode_results if "complete" in r.name), None)
            if basic and complete and basic.avg_latency > 0 and complete.avg_latency > 0:
                ratio = complete.avg_latency / basic.avg_latency
                lines.append(f"- complete 模式延迟是 basic 模式的 {ratio:.2f} 倍")
        
        lines.append("")
    
    lines.append("## 4. 性能评估")
    lines.append("")
    
    all_valid = [r for r in results if r.qps > 0]
    if all_valid:
        avg_qps = statistics.mean([r.qps for r in all_valid])
        avg_latency = statistics.mean([r.avg_latency for r in all_valid if r.avg_latency > 0])
        
        lines.append(f"- **平均 QPS**: {avg_qps:.2f}")
        lines.append(f"- **平均延迟**: {avg_latency*1000:.2f}ms")
        lines.append("")
        
        max_qps = max(r.qps for r in all_valid)
        if max_qps > 150:
            lines.append("- **性能等级**: ⭐⭐⭐⭐ 优秀 (QPS > 150)")
        elif max_qps > 100:
            lines.append("- **性能等级**: ⭐⭐⭐ 良好 (QPS > 100)")
        elif max_qps > 50:
            lines.append("- **性能等级**: ⭐⭐ 一般 (QPS > 50)")
        else:
            lines.append("- **性能等级**: ⭐ 需优化 (QPS < 50)")
    
    lines.append("")
    
    lines.append("## 5. 容量规划建议")
    lines.append("")
    
    if concurrent_results and safe_results:
        best = max(safe_results, key=lambda r: r.qps)
        lines.append(f"### 5.1 单实例容量")
        lines.append("")
        lines.append(f"- **安全 QPS**: {best.qps * 0.8:.0f} (预留 20% 余量)")
        lines.append(f"- **极限 QPS**: {best.qps:.0f}")
        lines.append("")
        
        lines.append(f"### 5.2 多实例部署")
        lines.append("")
        lines.append("| 目标 QPS | 推荐实例数 | 说明 |")
        lines.append("|----------|-----------|------|")
        lines.append(f"| 100 | {max(1, int(100 / best.qps * 1.5))} | 预留 50% 余量 |")
        lines.append(f"| 500 | {max(1, int(500 / best.qps * 1.5))} | 预留 50% 余量 |")
        lines.append(f"| 1000 | {max(1, int(1000 / best.qps * 1.5))} | 预留 50% 余量 |")
        lines.append("")
    
    lines.append("## 6. 优化建议")
    lines.append("")
    lines.append("### 6.1 短期优化（1-2周）")
    lines.append("")
    lines.append("1. **连接池配置**")
    lines.append("   - 增加数据库连接池大小")
    lines.append("   - 优化 HTTP 客户端连接池")
    lines.append("")
    lines.append("2. **超时配置**")
    lines.append("   - 设置合理的请求超时（建议 10-30 秒）")
    lines.append("   - 配置熔断机制")
    lines.append("")
    
    lines.append("### 6.2 中期优化（1-2月）")
    lines.append("")
    lines.append("1. **缓存层引入**")
    lines.append("   - 对高频搜索词增加 Redis 缓存")
    lines.append("   - 向量结果缓存")
    lines.append("")
    lines.append("2. **数据库优化**")
    lines.append("   - 从 SQLite 迁移到 MySQL")
    lines.append("   - 配置主从读写分离")
    lines.append("")
    
    lines.append("### 6.3 长期优化（3-6月）")
    lines.append("")
    lines.append("1. **服务拆分**")
    lines.append("   - 搜索服务独立部署")
    lines.append("   - 向量服务独立扩容")
    lines.append("")
    lines.append("2. **分布式部署**")
    lines.append("   - 多节点负载均衡")
    lines.append("   - 向量库分片")
    lines.append("")
    
    errors = []
    for r in results:
        if r.errors:
            errors.extend([f"{r.name}: {e}" for e in r.errors[:5]])
    
    if errors:
        lines.append("## 7. 错误信息")
        lines.append("")
        for err in errors[:20]:
            lines.append(f"- {err}")
        lines.append("")
    
    lines.append("---")
    lines.append(f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    return "\n".join(lines)


async def main():
    parser = argparse.ArgumentParser(description="向量搜索接口压测脚本")
    parser.add_argument("--url", required=True, help="目标服务 URL，例如 http://localhost:8009")
    parser.add_argument("--concurrency", nargs='+', type=int, default=BenchmarkConfig.DEFAULT_CONCURRENCY,
                        help=f"并发梯度列表，默认: {BenchmarkConfig.DEFAULT_CONCURRENCY}")
    parser.add_argument("--requests", nargs='+', type=int, default=BenchmarkConfig.DEFAULT_REQUESTS,
                        help=f"请求数列表，默认: {BenchmarkConfig.DEFAULT_REQUESTS}")
    parser.add_argument("--output", default="benchmark_report.md", help="报告输出路径，默认: benchmark_report.md")
    parser.add_argument("--skip-mode-test", action="store_true", help="跳过响应模式对比测试")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("向量搜索接口压测")
    print("=" * 60)
    print(f"目标服务: {args.url}")
    print(f"并发梯度: {args.concurrency}")
    print(f"请求数: {args.requests}")
    print("")
    
    try:
        async with httpx.AsyncClient() as client:
            test_url = f"{args.url}/api/resources/categories"
            resp = await client.get(test_url, timeout=5)
            print(f"服务状态: 正常 (HTTP {resp.status_code})")
    except Exception as e:
        print(f"❌ 服务状态: 异常 - {e}")
        print(f"请确认服务地址是否正确: {args.url}")
        sys.exit(1)
    
    print("")
    print("=" * 60)
    print("Phase 1: 并发梯度测试")
    print("=" * 60)
    
    concurrent_results = await run_concurrent_tests(args.url, args.concurrency, args.requests)
    
    mode_results = []
    if not args.skip_mode_test:
        print("")
        print("=" * 60)
        print("Phase 2: 响应模式对比测试")
        print("=" * 60)
        mode_results = await run_mode_tests(args.url)
    
    print("")
    print("=" * 60)
    print("生成报告")
    print("=" * 60)
    
    all_results = concurrent_results + mode_results
    report = generate_report(all_results, args.url)
    
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n✅ 报告已生成: {args.output}")
    print("\n" + "=" * 60)
    print(report)


if __name__ == "__main__":
    asyncio.run(main())