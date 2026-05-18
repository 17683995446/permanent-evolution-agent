#!/usr/bin/env python3
"""
Advanced Stress Test Suite for Permanent Evolution Agent
深度压力测试 - 暴露系统极限缺陷
"""
import sys
import time
import random
import threading
import traceback
import gc
import os
from datetime import datetime
from typing import List, Dict, Any

sys.path.insert(0, '/workspace')
from main_loop_controller_orchestrator_system import MainLoopController


class StressTestResults:
    def __init__(self):
        self.start_time = time.time()
        self.test_results: List[Dict] = []
        self.errors: List[Dict] = []
        self.performance_metrics: Dict[str, List[float]] = {}
        self.system_issues: List[Dict] = []
        
    def add_result(self, test_name: str, passed: bool, details: str, metrics: Dict = None):
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details,
            "metrics": metrics or {},
            "timestamp": time.time()
        })
        
    def add_error(self, error_type: str, message: str, traceback: str):
        self.errors.append({
            "type": error_type,
            "message": message,
            "traceback": traceback,
            "timestamp": time.time()
        })
        
    def add_issue(self, severity: str, component: str, description: str, details: Dict = None):
        self.system_issues.append({
            "severity": severity,
            "component": component,
            "description": description,
            "details": details or {}
        })
        
    def record_metric(self, name: str, value: float):
        if name not in self.performance_metrics:
            self.performance_metrics[name] = []
        self.performance_metrics[name].append(value)
        
    def generate_report(self) -> str:
        duration = time.time() - self.start_time
        passed = sum(1 for r in self.test_results if r["passed"])
        total = len(self.test_results)
        errors_count = len(self.errors)
        issues_count = len(self.system_issues)
        
        report = f"""
{'='*80}
深度压力测试报告 - Permanent Evolution Agent
{'='*80}
测试时长: {duration:.2f}秒
测试结果: {passed}/{total} 通过
发现错误: {errors_count}个
发现缺陷: {issues_count}个

{'='*80}
详细测试结果
{'='*80}
"""
        for r in self.test_results:
            status = "✅" if r["passed"] else "❌"
            report += f"\n{status} {r['test']}\n   {r['details']}\n"
            
        if self.system_issues:
            report += f"\n{'='*80}\n系统缺陷清单\n{'='*80}\n"
            critical = [i for i in self.system_issues if i["severity"] == "critical"]
            high = [i for i in self.system_issues if i["severity"] == "high"]
            medium = [i for i in self.system_issues if i["severity"] == "medium"]
            
            if critical:
                report += "\n🚨 严重缺陷 (Critical):\n"
                for i in critical:
                    report += f"  - [{i['component']}] {i['description']}\n"
            if high:
                report += "\n⚠️ 高优先级缺陷 (High):\n"
                for i in high:
                    report += f"  - [{i['component']}] {i['description']}\n"
            if medium:
                report += "\n🔶 中优先级缺陷 (Medium):\n"
                for i in medium:
                    report += f"  - [{i['component']}] {i['description']}\n"
                    
        if self.errors:
            report += f"\n{'='*80}\n错误详情\n{'='*80}\n"
            error_types = {}
            for e in self.errors:
                error_types[e["type"]] = error_types.get(e["type"], 0) + 1
            for etype, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                report += f"\n{etype}: {count}次\n"
                for e in self.errors[:3]:
                    if e["type"] == etype:
                        report += f"  - {e['message'][:100]}\n"
                        
        if self.performance_metrics:
            report += f"\n{'='*80}\n性能指标\n{'='*80}\n"
            for name, values in self.performance_metrics.items():
                avg = sum(values) / len(values) if values else 0
                max_val = max(values) if values else 0
                min_val = min(values) if values else 0
                report += f"{name}: avg={avg:.4f}, max={max_val:.4f}, min={min_val:.4f}\n"
                
        return report


def stress_test_memory_leak(agent: MainLoopController, results: StressTestResults):
    """测试内存泄漏"""
    test_name = "内存泄漏测试"
    print(f"\n🧪 运行: {test_name}")
    
    gc.collect()
    initial_memory = get_memory_usage()
    memory_samples = []
    
    try:
        for i in range(50):
            for j in range(20):
                agent.submit_task(
                    task_type="memory_test",
                    payload={"index": j, "data": "x" * 10000}
                )
            
            time.sleep(0.5)
            
            if i % 5 == 0:
                gc.collect()
                current_memory = get_memory_usage()
                memory_samples.append(current_memory)
                results.record_metric("memory_mb", current_memory)
                
        gc.collect()
        final_memory = get_memory_usage()
        memory_growth = final_memory - initial_memory
        
        passed = memory_growth < 500
        details = f"初始内存: {initial_memory:.1f}MB, 最终内存: {final_memory:.1f}MB, 增长: {memory_growth:.1f}MB"
        
        if memory_growth > 200:
            results.add_issue("high", "memory", f"内存增长过高: {memory_growth:.1f}MB", {"growth": memory_growth})
            
        results.add_result(test_name, passed, details)
        print(f"  结果: {'✅ 通过' if passed else '❌ 失败'} - {details}")
        
    except Exception as e:
        results.add_error("MemoryTest", str(e), traceback.format_exc())
        results.add_result(test_name, False, f"异常: {str(e)}")


def stress_test_thread_safety(agent: MainLoopController, results: StressTestResults):
    """测试线程安全"""
    test_name = "线程安全测试"
    print(f"\n🧪 运行: {test_name}")
    
    counter = {"value": 0, "lock": threading.Lock()}
    errors = []
    
    def concurrent_task(task_id):
        try:
            for i in range(100):
                with counter["lock"]:
                    old_val = counter["value"]
                    counter["value"] = old_val + 1
                    
                task_id_str = agent.submit_task(
                    task_type="thread_test",
                    payload={"task_id": task_id, "iter": i}
                )
                
                status = agent.execution_engine.get_task_status(task_id_str)
                
                with counter["lock"]:
                    if counter["value"] != old_val + 1:
                        errors.append(f"Race condition detected at {task_id}-{i}")
                        
        except Exception as e:
            errors.append(f"Thread {task_id}: {str(e)}")
    
    threads = []
    start_time = time.time()
    
    try:
        for i in range(20):
            t = threading.Thread(target=concurrent_task, args=(i,))
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join(timeout=30)
            
        duration = time.time() - start_time
        expected = 2000
        actual = counter["value"]
        
        passed = len(errors) == 0 and actual >= expected * 0.95
        
        details = f"期望操作: {expected}, 实际完成: {actual}, 错误: {len(errors)}, 耗时: {duration:.2f}s"
        
        if len(errors) > 0:
            results.add_issue("high", "thread_safety", f"发现{len(errors)}个线程安全问题", {"errors": errors[:5]})
            
        results.add_result(test_name, passed, details)
        print(f"  结果: {'✅ 通过' if passed else '❌ 失败'} - {details}")
        
    except Exception as e:
        results.add_error("ThreadSafety", str(e), traceback.format_exc())
        results.add_result(test_name, False, f"异常: {str(e)}")


def stress_test_deadlock_risk(agent: MainLoopController, results: StressTestResults):
    """测试死锁风险"""
    test_name = "死锁风险测试"
    print(f"\n🧪 运行: {test_name}")
    
    deadlock_detected = False
    lock_order_errors = []
    
    def lock_test_1():
        nonlocal deadlock_detected
        try:
            for i in range(50):
                with agent.data_collector._lock:
                    time.sleep(0.001)
                    with agent.config._lock_internal:
                        pass
        except Exception:
            deadlock_detected = True
            
    def lock_test_2():
        nonlocal deadlock_detected
        try:
            for i in range(50):
                with agent.config._lock_internal:
                    time.sleep(0.001)
                    with agent.data_collector._lock:
                        pass
        except Exception:
            deadlock_detected = True
    
    threads = [
        threading.Thread(target=lock_test_1),
        threading.Thread(target=lock_test_2)
    ]
    
    start_time = time.time()
    
    try:
        for t in threads:
            t.start()
            
        for t in threads:
            t.join(timeout=10)
            
        duration = time.time() - start_time
        
        if not threads[0].is_alive() and not threads[1].is_alive():
            passed = True
            details = f"无死锁，耗时: {duration:.2f}s"
        else:
            passed = False
            details = "可能存在死锁风险，线程未正常结束"
            results.add_issue("high", "concurrency", "潜在死锁风险 - 锁顺序问题")
            
        results.add_result(test_name, passed, details)
        print(f"  结果: {'✅ 通过' if passed else '❌ 失败'} - {details}")
        
    except Exception as e:
        results.add_error("DeadlockTest", str(e), traceback.format_exc())
        results.add_result(test_name, False, f"异常: {str(e)}")


def stress_test_performance_bottleneck(agent: MainLoopController, results: StressTestResults):
    """测试性能瓶颈"""
    test_name = "性能瓶颈测试"
    print(f"\n🧪 运行: {test_name}")
    
    latencies = []
    throughput_samples = []
    
    try:
        for batch in range(10):
            batch_start = time.time()
            task_ids = []
            
            for i in range(100):
                start = time.time()
                task_id = agent.submit_task(
                    task_type="perf_test",
                    payload={"batch": batch, "index": i}
                )
                latency = time.time() - start
                latencies.append(latency)
                task_ids.append(task_id)
                
            batch_duration = time.time() - batch_start
            throughput = len(task_ids) / batch_duration
            throughput_samples.append(throughput)
            
            time.sleep(0.5)
            
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        max_latency = max(latencies) if latencies else 0
        avg_throughput = sum(throughput_samples) / len(throughput_samples) if throughput_samples else 0
        
        passed = avg_latency < 0.1 and max_latency < 1.0
        details = f"平均延迟: {avg_latency*1000:.2f}ms, 最大延迟: {max_latency*1000:.2f}ms, 吞吐: {avg_throughput:.1f}任务/秒"
        
        if avg_latency > 0.05:
            results.add_issue("medium", "performance", f"提交延迟过高: {avg_latency*1000:.2f}ms")
            
        results.add_result(test_name, passed, details)
        results.record_metric("avg_latency_ms", avg_latency * 1000)
        results.record_metric("throughput", avg_throughput)
        print(f"  结果: {'✅ 通过' if passed else '❌ 失败'} - {details}")
        
    except Exception as e:
        results.add_error("PerformanceBottleneck", str(e), traceback.format_exc())
        results.add_result(test_name, False, f"异常: {str(e)}")


def stress_test_error_handling(agent: MainLoopController, results: StressTestResults):
    """测试错误处理"""
    test_name = "错误处理测试"
    print(f"\n🧪 运行: {test_name}")
    
    error_count = 0
    recovery_count = 0
    
    def error_task_generator():
        error_types = ["ValueError", "RuntimeError", "TimeoutError", None]
        for i in range(30):
            error_type = random.choice(error_types)
            yield {
                "type": "error_injection",
                "payload": {"error_type": error_type, "should_fail": error_type is not None},
                "error_type": error_type
            }
    
    try:
        for task_spec in error_task_generator():
            if task_spec["error_type"]:
                agent.execution_engine.register_task_handler(
                    "error_injection",
                    lambda t: (_ for _ in ()).throw(RuntimeError(f"Injected error {t.payload}"))
                )
                error_count += 1
                
        time.sleep(2)
        
        guardian_events = agent.guardian_service.get_guardian_events()
        error_events = [e for e in guardian_events if e["severity"] in ["critical", "warning"]]
        
        if error_count > 0 and len(error_events) > 0:
            recovery_count = len(error_events)
            
        passed = error_count > 0 and recovery_count > 0
        details = f"注入错误: {error_count}, 触发事件: {len(error_events)}, 恢复处理: {recovery_count}"
        
        if error_count > 0 and recovery_count == 0:
            results.add_issue("high", "error_handling", "错误未被正确处理和恢复")
            
        results.add_result(test_name, passed, details)
        print(f"  结果: {'✅ 通过' if passed else '❌ 失败'} - {details}")
        
    except Exception as e:
        results.add_error("ErrorHandling", str(e), traceback.format_exc())
        results.add_result(test_name, False, f"异常: {str(e)}")


def stress_test_resource_exhaustion(agent: MainLoopController, results: StressTestResults):
    """测试资源耗尽"""
    test_name = "资源耗尽测试"
    print(f"\n🧪 运行: {test_name}")
    
    initial_cpu = get_cpu_usage()
    initial_handles = get_handle_count()
    
    try:
        for i in range(100):
            for j in range(50):
                agent.submit_task(
                    task_type="resource_test",
                    payload={"big_data": [x * j for x in range(1000)]}
                )
            time.sleep(0.1)
            
            if i % 10 == 0:
                current_cpu = get_cpu_usage()
                current_handles = get_handle_count()
                
                if current_cpu > 95:
                    results.add_issue("critical", "resource", f"CPU使用率过高: {current_cpu:.1f}%")
                if current_handles > initial_handles * 3:
                    results.add_issue("high", "resource", f"句柄数增长过多: {current_handles}")
                    
                results.record_metric("cpu_percent", current_cpu)
                results.record_metric("handles", current_handles)
                
        final_cpu = get_cpu_usage()
        final_handles = get_handle_count()
        
        cpu_ok = final_cpu < 90
        handles_ok = final_handles < initial_handles * 5
        
        passed = cpu_ok and handles_ok
        details = f"CPU: {initial_cpu:.1f}% -> {final_cpu:.1f}%, 句柄: {initial_handles} -> {final_handles}"
        
        results.add_result(test_name, passed, details)
        print(f"  结果: {'✅ 通过' if passed else '❌ 失败'} - {details}")
        
    except Exception as e:
        results.add_error("ResourceExhaustion", str(e), traceback.format_exc())
        results.add_result(test_name, False, f"异常: {str(e)}")


def stress_test_optimization_feedback_loop(agent: MainLoopController, results: StressTestResults):
    """测试优化反馈循环"""
    test_name = "优化反馈循环测试"
    print(f"\n🧪 运行: {test_name}")
    
    optimization_effectiveness = []
    cycle_count = 0
    
    try:
        for cycle in range(20):
            before_metrics = agent.data_collector.get_full_analysis()
            before_efficiency = before_metrics.get("metrics_summary", {}).get("avg_duration", 1.0)
            
            agent._optimization_cycle()
            
            time.sleep(1)
            
            after_metrics = agent.data_collector.get_full_analysis()
            after_efficiency = after_metrics.get("metrics_summary", {}).get("avg_duration", 1.0)
            
            improvement = (before_efficiency - after_efficiency) / before_efficiency if before_efficiency > 0 else 0
            optimization_effectiveness.append(improvement)
            cycle_count += 1
            
        avg_improvement = sum(optimization_effectiveness) / len(optimization_effectiveness) if optimization_effectiveness else 0
        
        passed = avg_improvement >= 0
        details = f"平均改进: {avg_improvement*100:.2f}%, 优化周期: {cycle_count}, 有效性: {agent.optimizer_module.get_optimization_effectiveness() if agent.optimizer_module else 'N/A'}"
        
        if avg_improvement < 0:
            results.add_issue("high", "optimization", f"优化无效果或产生负面影响: {avg_improvement*100:.2f}%")
            
        results.add_result(test_name, passed, details)
        results.record_metric("optimization_improvement", avg_improvement)
        print(f"  结果: {'✅ 通过' if passed else '❌ 失败'} - {details}")
        
    except Exception as e:
        results.add_error("OptimizationFeedback", str(e), traceback.format_exc())
        results.add_result(test_name, False, f"异常: {str(e)}")


def stress_test_synchronization_consistency(agent: MainLoopController, results: StressTestResults):
    """测试同步一致性"""
    test_name = "同步一致性测试"
    print(f"\n🧪 运行: {test_name}")
    
    inconsistencies = []
    
    try:
        for i in range(50):
            rules_before = agent.config.get_all_optimization_rules()
            sync_status_before = agent.sync_layer.get_all_sync_status() if agent.sync_layer else {}
            
            if agent.optimizer_module:
                effectiveness = agent.optimizer_module.get_optimization_effectiveness()
                if effectiveness.get("total_optimizations", 0) > 0:
                    agent.sync_layer.push_optimization(type('obj', (object,), {
                        'optimization_type': 'sequence',
                        'target_component': 'execution_sequence',
                        'new_value': ['validate', 'execute', 'cleanup'],
                        'expected_improvement': 0.1,
                        'rule_id': f'test_rule_{i}'
                    })())
            
            time.sleep(0.1)
            
            sync_status_after = agent.sync_layer.get_all_sync_status() if agent.sync_layer else {}
            
            for target in sync_status_before:
                if target in sync_status_after:
                    if sync_status_before[target].get("version") != sync_status_after[target].get("version"):
                        pass
                        
        for i in range(20):
            agent.submit_task("sync_test", {"index": i})
            time.sleep(0.05)
            
        time.sleep(2)
        
        final_sync = agent.sync_layer.get_sync_statistics() if agent.sync_layer else {}
        
        passed = final_sync.get("total_failed", 0) < 5
        details = f"同步统计: {final_sync}, 不一致: {len(inconsistencies)}"
        
        if len(inconsistencies) > 10:
            results.add_issue("high", "synchronization", f"同步不一致: {len(inconsistencies)}")
            
        results.add_result(test_name, passed, details)
        print(f"  结果: {'✅ 通过' if passed else '❌ 失败'} - {details}")
        
    except Exception as e:
        results.add_error("SynchronizationConsistency", str(e), traceback.format_exc())
        results.add_result(test_name, False, f"异常: {str(e)}")


def get_memory_usage() -> float:
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except:
        return 0.0
        
def get_cpu_usage() -> float:
    try:
        import psutil
        return psutil.cpu_percent(interval=0.1)
    except:
        return 0.0
        
def get_handle_count() -> int:
    try:
        import psutil
        process = psutil.Process()
        return process.num_handles() if hasattr(process, 'num_handles') else len(process.open_files())
    except:
        return 0


def run_comprehensive_stress_test():
    """运行完整压力测试"""
    print("\n" + "="*80)
    print("🔬 Permanent Evolution Agent - 深度压力测试")
    print("="*80 + "\n")
    
    results = StressTestResults()
    
    agent = MainLoopController()
    
    try:
        print("📦 初始化Agent...")
        agent.initialize()
        
        print("▶️ 启动Agent...")
        agent.start()
        
        time.sleep(5)
        
        print("\n" + "-"*80)
        print("开始压力测试...")
        print("-"*80)
        
        stress_tests = [
            ("内存泄漏测试", lambda: stress_test_memory_leak(agent, results)),
            ("线程安全测试", lambda: stress_test_thread_safety(agent, results)),
            ("死锁风险测试", lambda: stress_test_deadlock_risk(agent, results)),
            ("性能瓶颈测试", lambda: stress_test_performance_bottleneck(agent, results)),
            ("错误处理测试", lambda: stress_test_error_handling(agent, results)),
            ("资源耗尽测试", lambda: stress_test_resource_exhaustion(agent, results)),
            ("优化反馈循环测试", lambda: stress_test_optimization_feedback_loop(agent, results)),
            ("同步一致性测试", lambda: stress_test_synchronization_consistency(agent, results)),
        ]
        
        for test_name, test_func in stress_tests:
            try:
                test_func()
            except Exception as e:
                results.add_error(f"Test_{test_name}", str(e), traceback.format_exc())
                results.add_result(test_name, False, f"测试执行异常: {str(e)}")
                print(f"  ❌ 测试异常: {str(e)}")
                
        print("\n" + "="*80)
        print("📊 生成测试报告...")
        print("="*80)
        
        report = results.generate_report()
        print(report)
        
        with open("/workspace/stress_test_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
            
        print("\n✅ 压力测试完成，报告已保存到 stress_test_report.txt")
        
    except Exception as e:
        print(f"\n❌ 压力测试失败: {str(e)}")
        traceback.print_exc()
    finally:
        print("\n🛑 关闭Agent...")
        agent.stop()
        print("✅ 测试完成")


if __name__ == "__main__":
    run_comprehensive_stress_test()
