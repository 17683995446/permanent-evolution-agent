#!/usr/bin/env python3
"""
深度持续压力测试 - 模拟真实复杂场景，持续发现问题（优化版）
"""
import sys
import time
import random
import threading
import traceback
import gc
import os
import psutil
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import deque

sys.path.insert(0, '/workspace')


class DeepBugTracker:
    """深度Bug追踪器"""
    
    def __init__(self):
        self.bugs: List[Dict] = []
        self.metrics: Dict[str, deque] = {
            'cpu': deque(maxlen=100),
            'memory': deque(maxlen=100),
            'errors': deque(maxlen=500),
            'latency': deque(maxlen=100)
        }
        self._lock = threading.Lock()
        self._bug_counts = {}
        
    def record(self, bug_type: str, severity: str, msg: str, details: Any = None):
        with self._lock:
            bug = {
                'id': len(self.bugs) + 1,
                'type': bug_type,
                'severity': severity,
                'message': msg,
                'details': details,
                'time': time.time()
            }
            self.bugs.append(bug)
            
            # 计数
            if bug_type not in self._bug_counts:
                self._bug_counts[bug_type] = 0
            self._bug_counts[bug_type] += 1
            
            # 只打印前5个同类型bug
            if self._bug_counts[bug_type] <= 5:
                print(f"\n🔴 [BUG #{bug['id']}] {severity.upper()}: {bug_type}")
                print(f"   {msg}")
                if details:
                    print(f"   Details: {str(details)[:100]}")
            return bug
    
    def track(self, name: str, value: float):
        if name in self.metrics:
            self.metrics[name].append({'time': time.time(), 'value': value})


class ComplexScenarioRunner:
    """复杂场景运行器（优化版）"""
    
    def __init__(self, agent, tracker: DeepBugTracker):
        self.agent = agent
        self.tracker = tracker
        self.running = False
        self.scenarios = []
        self._lock = threading.Lock()
        
    def add_scenario(self, name: str, func, weight: int = 1):
        self.scenarios.append({'name': name, 'func': func, 'weight': weight})
        
    def start(self):
        self.running = True
        threads = []
        for _ in range(2):  # 减少到2个并发场景
            t = threading.Thread(target=self._run_loop, daemon=True)
            threads.append(t)
            t.start()
        return threads
    
    def _run_loop(self):
        while self.running:
            scenario = random.choices(self.scenarios, weights=[s['weight'] for s in self.scenarios])[0]
            try:
                scenario['func']()
            except Exception as e:
                self.tracker.record('scenario_error', 'critical', f"Scenario {scenario['name']} failed", str(e))
            time.sleep(random.uniform(0.1, 1.0))  # 增加间隔


def main():
    print("=" * 80)
    print("🚀 深度持续压力测试 - 10分钟+ 真实场景模拟")
    print("=" * 80)
    
    tracker = DeepBugTracker()
    
    # 导入并启动Agent
    from main_loop_controller_orchestrator_system import MainLoopController
    
    print("\n📦 初始化Agent...")
    agent = MainLoopController()
    agent.initialize()
    agent.start()
    
    # 创建复杂场景（优化）
    runner = ComplexScenarioRunner(agent, tracker)
    
    # 场景1: 适度任务提交
    def scenario_low_freq():
        for _ in range(3):  # 减少到3个
            agent.submit_task('compute', {'data': 'x' * 100})
            
    # 场景2: 小批量任务
    def scenario_batch():
        tasks = [{'type': random.choice(['compute', 'process', 'analyze']), 
                  'payload': {'id': i}} for i in range(10)]  # 减少到10个
        agent.submit_batch_tasks(tasks)
        
    # 场景3: 低并发压力
    def scenario_concurrent():
        threads = []
        for i in range(3):  # 减少到3个线程
            def worker():
                for _ in range(2):  # 每个线程只提交2个任务
                    agent.submit_task('compute', {'worker': i})
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
            
    # 场景4: 适度内存压力
    def scenario_memory():
        big_data = [{'key': f'value_{j}'} for j in range(100)]
        for _ in range(3):  # 减少到3个
            agent.submit_task('process', {'data': big_data})
            
    # 场景5: 混合负载
    def scenario_mixed():
        ops = [
            lambda: agent.submit_task('compute', {'op': 'calc'}),
            lambda: agent.submit_task('analyze', {'op': 'analyze'}),
            lambda: agent.submit_task('process', {'op': 'process'}),
        ]
        random.choice(ops)()
        
    runner.add_scenario('low_freq', scenario_low_freq, weight=5)
    runner.add_scenario('batch', scenario_batch, weight=2)
    runner.add_scenario('concurrent', scenario_concurrent, weight=2)
    runner.add_scenario('memory', scenario_memory, weight=1)
    runner.add_scenario('mixed', scenario_mixed, weight=5)
    
    # 启动场景
    print("📊 启动监控线程...")
    threads = runner.start()
    
    # 系统监控线程
    monitor_thread = threading.Thread(target=lambda: monitor_system(agent, tracker), daemon=True)
    monitor_thread.start()
    
    # 长时间运行
    duration = 600  # 10分钟
    start_time = time.time()
    last_report = 0
    
    print(f"\n⏱️  开始测试 (持续 {duration} 秒)...")
    print("    Ctrl+C 可提前停止\n")
    
    try:
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            
            # 每分钟报告
            if elapsed - last_report >= 60:
                last_report = elapsed
                minutes = int(elapsed // 60)
                
                status = agent.get_system_status()
                cpu = tracker.metrics['cpu'][-1]['value'] if tracker.metrics['cpu'] else 0
                memory = tracker.metrics['memory'][-1]['value'] if tracker.metrics['memory'] else 0
                
                print(f"\n{'='*60}")
                print(f"📈 第 {minutes} 分钟报告")
                print(f"{'='*60}")
                print(f"  CPU: {cpu:.1f}%")
                print(f"  Memory: {memory:.1f}MB")
                print(f"  Tasks: {status['statistics']['total_tasks']}")
                print(f"  Bugs: {len(tracker.bugs)}")
                print(f"  Health: {status['guardian']['overall_status']}")
                
                # 分析最近的问题
                recent_bugs = [b for b in tracker.bugs if time.time() - b['time'] < 60]
                if recent_bugs:
                    print(f"\n  最近1分钟发现 {len(recent_bugs)} 个问题:")
                    for bug in recent_bugs[-3:]:
                        print(f"    - [{bug['severity']}] {bug['type']}: {bug['message'][:50]}")
                print()
                
                # GC
                gc.collect()
                
    except KeyboardInterrupt:
        print("\n\n⏹️  测试中断...")
    finally:
        print("\n🛑 停止测试...")
        runner.running = False
        agent.stop()
        
    # 生成报告
    generate_report(tracker, agent, time.time() - start_time)


def monitor_system(agent, tracker):
    """系统监控"""
    while True:
        try:
            process = psutil.Process()
            cpu = process.cpu_percent(interval=0.1)
            memory = process.memory_info().rss / 1024 / 1024
            
            tracker.track('cpu', cpu)
            tracker.track('memory', memory)
            
            # 阈值检测（更严格的阈值）
            if cpu > 80:
                tracker.record('high_cpu', 'high', f'CPU使用率过高: {cpu:.1f}%')
            if memory > 200:
                tracker.record('high_memory', 'medium', f'内存使用过高: {memory:.1f}MB')
                
            time.sleep(1)
        except:
            pass


def generate_report(tracker: DeepBugTracker, agent, duration: float):
    """生成测试报告"""
    print("\n" + "=" * 80)
    print("📋 深度压力测试报告")
    print("=" * 80)
    
    print(f"\n⏱️  测试时长: {duration:.0f}秒 ({duration/60:.1f}分钟)")
    print(f"🔴 发现Bug总数: {len(tracker.bugs)}")
    
    # 按类型统计
    bug_types = {}
    for bug in tracker.bugs:
        t = bug['type']
        bug_types[t] = bug_types.get(t, 0) + 1
        
    print(f"\n📊 Bug类型分布:")
    for t, count in sorted(bug_types.items(), key=lambda x: x[1], reverse=True):
        print(f"   {t}: {count}")
        
    # 按严重性统计
    severity = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    for bug in tracker.bugs:
        s = bug['severity']
        if s in severity:
            severity[s] += 1
            
    print(f"\n⚠️  严重性分布:")
    for s, count in severity.items():
        if count > 0:
            print(f"   {s}: {count}")
            
    # 性能统计
    if tracker.metrics['cpu']:
        avg_cpu = sum(m['value'] for m in tracker.metrics['cpu']) / len(tracker.metrics['cpu'])
        max_cpu = max(m['value'] for m in tracker.metrics['cpu'])
        print(f"\n💻 CPU统计:")
        print(f"   平均: {avg_cpu:.1f}%")
        print(f"   最大: {max_cpu:.1f}%")
        
    if tracker.metrics['memory']:
        avg_mem = sum(m['value'] for m in tracker.metrics['memory']) / len(tracker.metrics['memory'])
        max_mem = max(m['value'] for m in tracker.metrics['memory'])
        print(f"\n💾 内存统计:")
        print(f"   平均: {avg_mem:.1f}MB")
        print(f"   最大: {max_mem:.1f}MB")
        
    # 系统状态
    status = agent.get_system_status()
    print(f"\n🏥 系统状态:")
    print(f"   Guardian: {status['guardian']['overall_status']}")
    print(f"   完成任务: {status['statistics']['total_tasks']}")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
