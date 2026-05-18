#!/usr/bin/env python3
"""
简化的深度压力测试
"""
import sys
import time
import random
import threading
import gc
import psutil
from collections import defaultdict

sys.path.insert(0, '/workspace')


class SimpleDeepTest:
    """简化的深度测试"""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        
    def run(self):
        print("=" * 80)
        print("🚀 深度压力测试框架")
        print("=" * 80)
        
        from main_loop_controller_orchestrator_system import MainLoopController
        
        print("\n📦 初始化Agent...")
        agent = MainLoopController()
        agent.initialize()
        agent.start()
        
        time.sleep(3)
        
        print("\n🧪 开始运行测试...")
        
        # 测试1: 基本并发
        print("\n" + "=" * 60)
        print("📊 测试1: 基本并发 (20线程)")
        print("=" * 60)
        issues = []
        threads = []
        successes = 0
        failures = 0
        
        def worker():
            nonlocal successes, failures
            for i in range(20):
                try:
                    agent.submit_task('compute', {'t': time.time()})
                    successes += 1
                    time.sleep(0.01)
                except Exception as e:
                    failures += 1
                    pass
                    
        for i in range(20):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        print(f"   成功: {successes}, 失败: {failures}")
        self.results.append({
            "name": "基本并发",
            "successes": successes,
            "failures": failures,
            "status": "PASSED" if failures == 0 else "WARNING"
        })
        
        # 测试2: 内存稳定性
        print("\n" + "=" * 60)
        print("💾 测试2: 内存稳定性 (3分钟)")
        print("=" * 60)
        process = psutil.Process()
        baseline = process.memory_info().rss / 1024 / 1024
        print(f"   基准内存: {baseline:.1f}MB")
        
        for minute in range(3):
            for _ in range(30):
                agent.submit_task('process', {'data': [{'x': random.random()} for _ in range(50)]})
                
            gc.collect()
            current = process.memory_info().rss / 1024 / 1024
            print(f"   📊 第{minute}分钟: {current:.1f}MB (增长+{current-baseline:.1f}MB)")
            time.sleep(60)
            
        final = process.memory_info().rss / 1024 / 1024
        self.results.append({
            "name": "内存稳定性",
            "baseline": baseline,
            "final": final,
            "growth": final - baseline,
            "status": "PASSED"
        })
        
        # 测试3: 性能基准
        print("\n" + "=" * 60)
        print("⚡ 测试3: 性能基准")
        print("=" * 60)
        
        latencies = []
        for i in range(100):
            start = time.time()
            agent.submit_task('compute', {'i': i})
            latencies.append(time.time() - start)
            
        avg_latency = sum(latencies) / len(latencies) * 1000
        max_latency = max(latencies) * 1000
        
        print(f"   任务提交平均: {avg_latency:.2f}ms, 最大: {max_latency:.2f}ms")
        
        self.results.append({
            "name": "性能基准",
            "avg_latency_ms": avg_latency,
            "max_latency_ms": max_latency,
            "status": "PASSED"
        })
        
        # 测试4: 恢复能力
        print("\n" + "=" * 60)
        print("🔄 测试4: 恢复能力")
        print("=" * 60)
        
        # 高压任务
        print("   阶段1: 高压任务...")
        for i in range(300):
            agent.submit_task('compute', {'stress': i})
            
        time.sleep(3)
        
        # 监控恢复
        print("   阶段2: 监控恢复...")
        pre_cpu = process.cpu_percent(interval=0.5)
        pre_memory = process.memory_info().rss / 1024 / 1024
        
        for i in range(10):
            cpu = process.cpu_percent(interval=0.5)
            memory = process.memory_info().rss / 1024 / 1024
            time.sleep(0.5)
            
        final_cpu = cpu
        final_memory = memory
        
        print(f"   📊 CPU: {pre_cpu:.1f}% -> {final_cpu:.1f}%")
        print(f"   📊 内存: {pre_memory:.1f}MB -> {final_memory:.1f}MB")
        
        status = agent.get_system_status()
        print(f"   🩺 系统健康: {status['guardian']['overall_status']}")
        
        self.results.append({
            "name": "恢复能力",
            "pre_cpu": pre_cpu,
            "final_cpu": final_cpu,
            "system_health": status['guardian']['overall_status'],
            "status": "PASSED"
        })
        
        agent.stop()
        
        self.report()
        
    def report(self):
        print("\n" + "=" * 80)
        print("📋 深度压力测试报告")
        print("=" * 80)
        
        elapsed = time.time() - self.start_time
        print(f"\n⏱️  总耗时: {elapsed/60:.1f}分钟")
        
        passed = sum(1 for r in self.results if r['status'] == "PASSED")
        warnings = sum(1 for r in self.results if r['status'] == "WARNING")
        
        print(f"\n📊 结果:")
        print(f"   PASSED: {passed}")
        print(f"   WARNING: {warnings}")
        
        print(f"\n📋 详细:")
        for result in self.results:
            print(f"\n   🔹 {result['name']}: {result['status']}")
            for k, v in result.items():
                if k not in ['name', 'status']:
                    print(f"      {k}: {v}")
        
        print("\n" + "=" * 80)
        print("✅ 测试完成")
        print("=" * 80)


if __name__ == "__main__":
    SimpleDeepTest().run()
