#!/usr/bin/env python3
"""
实用深度测试框架 - 渐进式压力测试
"""
import sys
import time
import random
import threading
import gc
import os
import psutil
from collections import deque, defaultdict
from dataclasses import dataclass

sys.path.insert(0, '/workspace')


@dataclass
class TestResult:
    name: str
    status: str
    issues: list
    metrics: dict


class SimpleDeepTest:
    """简化的深度测试框架"""
    
    def __init__(self):
        self.results = []
        self.metrics = defaultdict(deque)
        self.start_time = time.time()
        
    def run(self):
        print("=" * 80)
        print("🚀 实用深度压力测试框架")
        print("=" * 80)
        
        from main_loop_controller_orchestrator_system import MainLoopController
        
        print("\n📦 初始化Agent...")
        agent = MainLoopController()
        agent.initialize()
        agent.start()
        
        time.sleep(3)
        
        tests = [
            ("渐进式并发", self.test_gradual_concurrency, agent),
            ("内存稳定性", self.test_memory_stability, agent),
            ("性能基准", self.test_performance, agent),
            ("恢复能力", self.test_recovery, agent),
        ]
        
        print("\n🧪 开始运行深度测试...")
        
        for name, test_func, agent_arg in tests:
            try:
                result = test_func(agent_arg)
                self.results.append(result)
                print(f"\n✅ {name} 完成: {result.status}")
            except Exception as e:
                print(f"\n❌ {name} 失败: {str(e)[:100]}")
                self.results.append(TestResult(name, "FAILED", [str(e)], {}))
                
            time.sleep(2)
            
        agent.stop()
        self.report()
        
    def test_gradual_concurrency(self, agent):
        """渐进式并发测试"""
        print(f"\n{'='*60}")
        print(f"🧪 渐进式并发测试")
        print(f"{'='*60}")
        
        issues = []
        metrics = {}
        
        for thread_count in [5, 10, 20, 50]:
            print(f"\n   ▶️  {thread_count}线程测试...")
            start = time.time()
            threads = []
            success = 0
            failures = 0
            
            def worker():
                nonlocal success, failures
                for i in range(30):
                    try:
                        agent.submit_task('compute', {'t': time.time()})
                        success += 1
                        time.sleep(0.001)
                    except:
                        failures += 1
                        
            for i in range(thread_count):
                t = threading.Thread(target=worker)
                threads.append(t)
                t.start()
                
            for t in threads:
                t.join()
                
            elapsed = time.time() - start
            throughput = success / elapsed if elapsed > 0 else 0
            
            print(f"      成功: {success}, 失败: {failures}")
            print(f"      耗时: {elapsed:.1f}秒, 吞吐: {throughput:.1f}任务/秒")
            
            metrics[f'thread_{thread_count}'] = {
                'throughput': throughput, 'success': success, 'elapsed': elapsed
            }
            
            if failures > 0:
                issues.append(f"{thread_count}线程有{failures}个失败")
                
        return TestResult("渐进式并发", "PASSED" if not issues else "WARNING", issues, metrics)
        
    def test_memory_stability(self, agent):
        """内存稳定性测试"""
        print(f"\n{'='*60}")
        print(f"💾 内存稳定性测试 - 5分钟")
        print(f"{'='*60}")
        
        issues = []
        process = psutil.Process()
        baseline = process.memory_info().rss / 1024 / 1024
        start = time.time()
        
        print(f"   基准内存: {baseline:.1f}MB")
        
        for minute in range(5):
            for _ in range(30):
                agent.submit_task('process', {'data': [{'x': random.random()} for _ in range(50)]})
                
            gc.collect()
            current = process.memory_info().rss / 1024 / 1024
            growth = current - baseline
            self.metrics[f'memory_min{minute}'].append(current)
            
            print(f"   📊 第{minute}分钟: {current:.1f}MB (增长+{growth:.1f}MB)")
            
            if growth > 20:
                issues.append(f"内存增长过大: +{growth:.1f}MB")
                
            time.sleep(60)
            
        final = process.memory_info().rss / 1024 / 1024
        total_growth = final - baseline
        
        metrics = {
            'baseline': baseline,
            'final': final,
            'total_growth': total_growth
        }
        
        return TestResult("内存稳定性", "PASSED" if not issues else "WARNING", issues, metrics)
        
    def test_performance(self, agent):
        """性能基准测试"""
        print(f"\n{'='*60}")
        print(f"⚡ 性能基准测试")
        print(f"{'='*60}")
        
        issues = []
        metrics = {}
        
        # 任务提交延迟
        latencies = []
        for i in range(100):
            start = time.time()
            agent.submit_task('compute', {'i': i})
            latencies.append(time.time() - start)
            
        avg_latency = sum(latencies) / len(latencies) * 1000
        max_latency = max(latencies) * 1000
        
        print(f"   任务提交:")
        print(f"      平均: {avg_latency:.2f}ms, 最大: {max_latency:.2f}ms")
        
        metrics['task_submit'] = {'avg_ms': avg_latency, 'max_ms': max_latency}
        
        # 系统状态查询
        status_latencies = []
        for i in range(20):
            start = time.time()
            agent.get_system_status()
            status_latencies.append(time.time() - start)
            
        avg_status = sum(status_latencies) / len(status_latencies) * 1000
        print(f"   状态查询:")
        print(f"      平均: {avg_status:.2f}ms")
        
        metrics['status_query'] = {'avg_ms': avg_status}
        
        if avg_latency > 10:
            issues.append(f"任务提交延迟过高: {avg_latency:.2f}ms")
            
        return TestResult("性能基准", "PASSED" if not issues else "WARNING", issues, metrics)
        
    def test_recovery(self, agent):
        """恢复能力测试"""
        print(f"\n{'='*60}")
        print(f"🔄 压力后恢复能力")
        print(f"{'='*60}")
        
        issues = []
        process = psutil.Process()
        
        # 施加压力
        print("   阶段1: 高压任务...")
        for i in range(300):
            agent.submit_task('compute', {'stress': i})
            
        time.sleep(3)
        
        # 监控恢复
        print("   阶段2: 监控恢复...")
        
        pre_stress_cpu = process.cpu_percent(interval=0.5)
        pre_stress_memory = process.memory_info().rss / 1024 / 1024
        
        recovery_data = []
        for i in range(10):
            cpu = process.cpu_percent(interval=0.5)
            memory = process.memory_info().rss / 1024 / 1024
            recovery_data.append({'cpu': cpu, 'memory': memory})
            time.sleep(0.5)
            
        final_cpu = recovery_data[-1]['cpu']
        final_memory = recovery_data[-1]['memory']
        
        print(f"   📊 CPU: {pre_stress_cpu:.1f}% -> {final_cpu:.1f}%")
        print(f"   📊 内存: {pre_stress_memory:.1f}MB -> {final_memory:.1f}MB")
        
        if final_cpu > 30:
            issues.append(f"CPU未充分恢复: {final_cpu:.1f}%")
            
        metrics = {
            'pre_stress': {'cpu': pre_stress_cpu, 'memory': pre_stress_memory},
            'final': {'cpu': final_cpu, 'memory': final_memory}
        }
        
        status = agent.get_system_status()
        print(f"   🩺 系统健康: {status['guardian']['overall_status']}")
        
        if status['guardian']['overall_status'] != 'healthy':
            issues.append("系统未完全恢复")
            
        return TestResult("恢复能力", "PASSED" if not issues else "WARNING", issues, metrics)
        
    def report(self):
        """生成测试报告"""
        print("\n" + "=" * 80)
        print("📋 深度压力测试报告")
        print("=" * 80)
        
        elapsed = time.time() - self.start_time
        print(f"\n⏱️  总耗时: {elapsed/60:.1f}分钟")
        
        passed = sum(1 for r in self.results if r.status == "PASSED")
        warnings = sum(1 for r in self.results if r.status == "WARNING")
        failed = sum(1 for r in self.results if r.status == "FAILED")
        
        print(f"\n📊 结果:")
        print(f"   PASSED: {passed}")
        print(f"   WARNING: {warnings}")
        print(f"   FAILED: {failed}")
        
        if self.results:
            print(f"\n📋 详细结果:")
            for result in self.results:
                print(f"\n   🔹 {result.name}: {result.status}")
                if result.issues:
                    for issue in result.issues[:3]:
                        print(f"      ⚠️  {issue}")
                        
        print("\n" + "=" * 80)
        print("✅ 测试完成")
        print("=" * 80)


if __name__ == "__main__":
    SimpleDeepTest().run()
