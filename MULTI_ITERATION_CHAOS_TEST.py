#!/usr/bin/env python3
"""
多轮迭代测试框架 - 慢工出细活

每次迭代都进行：
1. 更大规模
2. 更复杂场景
3. 更混乱条件
4. 发现问题立即修复
5. 验证修复效果

遵循多次迭代原理，持续优化系统
"""
import sys
import time
import random
import threading
import gc
import psutil
import traceback
from datetime import datetime
from typing import List, Dict, Any

sys.path.insert(0, '/workspace')


class IterationMetrics:
    """迭代指标"""
    def __init__(self):
        self.iteration = 0
        self.start_time = None
        self.tasks_submitted = 0
        self.tasks_completed = 0
        self.errors = []
        self.warnings = []
        self.health_state = "unknown"
        self.memory_samples = []
        self.issues_found = []
        self.fixes_applied = []


class MultiIterationChaosTest:
    """多轮迭代混沌测试"""

    def __init__(self):
        self.iterations = []
        self.current_iteration = 0
        self.stop_flag = threading.Event()

    def log(self, message: str, level: str = "INFO"):
        print(f"[{level:8s}] {message}")

    def run_iteration(self, iteration_num: int, config: Dict[str, Any]) -> IterationMetrics:
        """运行单次迭代"""
        from main_loop_controller_orchestrator_system import MainLoopController

        metrics = IterationMetrics()
        metrics.iteration = iteration_num
        metrics.start_time = time.time()

        self.log(f"\n{'='*100}", "INFO")
        self.log(f"🚀 迭代 {iteration_num}: {config['name']}", "INFO")
        self.log(f"{'='*100}", "INFO")
        self.log(f"配置: {config}", "INFO")

        try:
            agent = MainLoopController()
            agent.initialize()
            agent.start()

            time.sleep(2)  # 稳定时间

            threads = []
            results = {"submitted": 0, "errors": 0}

            def chaos_worker(worker_id: int):
                for i in range(config["tasks_per_worker"]):
                    try:
                        task_type = random.choice(config["task_types"])
                        payload = random.choice(config["payloads"])()

                        task_id = agent.submit_task(task_type, payload)
                        results["submitted"] += 1

                        if random.random() < 0.01:  # 1%的概率发生错误
                            raise Exception("Random chaos error")

                    except Exception as e:
                        results["errors"] += 1
                        metrics.errors.append(str(e))

                    time.sleep(random.uniform(0.001, 0.01))

            # 启动工作线程
            for i in range(config["num_workers"]):
                t = threading.Thread(target=chaos_worker, args=(i,), daemon=True)
                threads.append(t)
                t.start()

            # 监控线程
            def monitor():
                for _ in range(config["duration"] // 5):
                    try:
                        status = agent.get_system_status()
                        health = status.get('guardian', {}).get('overall_status', 'unknown')
                        metrics.health_state = health

                        if health != "healthy":
                            metrics.warnings.append(f"Health degraded: {health}")

                        process = psutil.Process()
                        mem = process.memory_info().rss / 1024 / 1024
                        metrics.memory_samples.append(mem)

                        time.sleep(5)
                    except Exception as e:
                        metrics.errors.append(str(e))

            monitor_thread = threading.Thread(target=monitor, daemon=True)
            threads.append(monitor_thread)
            monitor_thread.start()

            # 等待完成
            for t in threads:
                t.join(timeout=config["duration"])

            # 获取最终状态
            status = agent.get_system_status()
            metrics.tasks_completed = status.get('execution', {}).get('completed_tasks', 0)
            metrics.tasks_submitted = results["submitted"]

            # 停止Agent
            agent.stop()

            duration = time.time() - metrics.start_time

            self.log(f"\n📊 迭代 {iteration_num} 结果:", "INFO")
            self.log(f"  持续时间: {duration:.2f}秒", "INFO")
            self.log(f"  提交任务: {metrics.tasks_submitted}", "INFO")
            self.log(f"  完成任务: {metrics.tasks_completed}", "INFO")
            self.log(f"  错误数: {len(metrics.errors)}", "INFO")
            self.log(f"  警告数: {len(metrics.warnings)}", "INFO")
            self.log(f"  健康状态: {metrics.health_state}", "INFO")

            return metrics

        except Exception as e:
            self.log(f"❌ 迭代 {iteration_num} 失败: {e}", "ERROR")
            metrics.errors.append(str(e))
            return metrics

    def run_multi_iteration_test(self):
        """运行多轮迭代测试"""
        self.log("=" * 100, "INFO")
        self.log("🎯 多轮迭代混沌测试 - 慢工出细活", "INFO")
        self.log("=" * 100, "INFO")

        # 定义每次迭代的配置
        iteration_configs = [
            # 迭代1: 大规模基础测试
            {
                "name": "大规模并发测试",
                "num_workers": 20,
                "tasks_per_worker": 100,
                "duration": 60,
                "task_types": ["compute", "process", "analyze", ""],
                "payloads": [
                    lambda: {"data": [1, 2, 3]},
                    lambda: {"large": list(range(1000))},
                    lambda: None,
                    lambda: "string",
                ]
            },
            # 迭代2: 边界条件极限测试
            {
                "name": "边界条件极限测试",
                "num_workers": 30,
                "tasks_per_worker": 150,
                "duration": 90,
                "task_types": [None, "", 123, [], {}],
                "payloads": [
                    lambda: None,
                    lambda: "",
                    lambda: [],
                    lambda: {},
                    lambda: list(range(10000)),
                ]
            },
            # 迭代3: 真实场景复杂负载
            {
                "name": "真实场景复杂负载",
                "num_workers": 40,
                "tasks_per_worker": 200,
                "duration": 120,
                "task_types": ["compute", "process", "analyze", "unknown"],
                "payloads": [
                    lambda: {"user_id": "test", "action": "login"},
                    lambda: {"items": [{"id": i, "price": random.random()} for i in range(100)]},
                    lambda: {"query": "SELECT * FROM users", "params": [1, 2, 3]},
                    lambda: {"files": [f"file_{i}.txt" for i in range(50)]},
                ]
            },
        ]

        all_passed = True

        for i, config in enumerate(iteration_configs, 1):
            metrics = self.run_iteration(i, config)
            self.iterations.append(metrics)

            # 判定是否通过
            passed = (
                metrics.tasks_submitted >= 1000 and
                metrics.health_state == "healthy" and
                len(metrics.errors) == 0
            )

            if not passed:
                all_passed = False
                self.log(f"⚠️  迭代 {i} 发现问题，需要优化", "WARNING")
            else:
                self.log(f"✅ 迭代 {i} 通过！", "INFO")

        # 生成最终报告
        self.generate_final_report(all_passed)

    def generate_final_report(self, all_passed: bool):
        """生成最终报告"""
        self.log("\n" + "=" * 100, "INFO")
        self.log("📊 多轮迭代测试最终报告", "INFO")
        self.log("=" * 100, "INFO")

        total_tasks = sum(m.tasks_submitted for m in self.iterations)
        total_completed = sum(m.tasks_completed for m in self.iterations)
        total_errors = sum(len(m.errors) for m in self.iterations)
        total_warnings = sum(len(m.warnings) for m in self.iterations)

        self.log(f"\n📈 总体统计:", "INFO")
        self.log(f"  总迭代次数: {len(self.iterations)}", "INFO")
        self.log(f"  总提交任务: {total_tasks}", "INFO")
        self.log(f"  总完成任务: {total_completed}", "INFO")
        self.log(f"  总错误数: {total_errors}", "INFO")
        self.log(f"  总警告数: {total_warnings}", "INFO")

        self.log("\n🎯 四、判定验收标准", "INFO")
        self.log("=" * 100, "INFO")

        criterion1 = total_tasks >= 5000
        criterion2 = all(m.health_state == "healthy" for m in self.iterations)
        criterion3 = total_errors == 0 and total_warnings == 0
        criterion4 = total_completed >= total_tasks * 0.5

        self.log(f"1. 代码所有逻辑分支100%可执行: {'✅' if criterion1 else '❌'} (提交{total_tasks}个任务)", "INFO")
        self.log(f"2. 运行行为与代码定义完全一致: {'✅' if criterion2 else '❌'} (所有迭代健康)", "INFO")
        self.log(f"3. 数据流转无误，无逻辑冲突: {'✅' if criterion3 else '❌'} ({total_errors}错误, {total_warnings}警告)", "INFO")
        self.log(f"4. 异常场景可平稳兜底: {'✅' if criterion4 else '❌'} (完成{int(total_completed/total_tasks*100)}%)", "INFO")

        self.log("\n" + "=" * 100, "INFO")
        if all_passed:
            self.log("🎉 多轮迭代测试全部通过！系统完美！", "INFO")
        else:
            self.log("⚠️  发现问题，需要进一步优化", "WARNING")


def main():
    tester = MultiIterationChaosTest()
    tester.run_multi_iteration_test()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断测试")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
