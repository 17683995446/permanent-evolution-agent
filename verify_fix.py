#!/usr/bin/env python3
"""
验证修复效果 - 检查优化后的性能
"""
import sys
import time
import gc
import psutil
import random
from typing import Dict, List, Any

sys.path.insert(0, '/workspace')
from main_loop_controller_orchestrator_system import MainLoopController


def check_cpu_memory():
    """获取当前CPU和内存使用情况"""
    process = psutil.Process()
    return {
        'cpu_percent': process.cpu_percent(interval=0.5),
        'memory_mb': process.memory_info().rss / 1024 / 1024
    }


def run_verification_test():
    """运行验证测试"""
    print("=" * 80)
    print("🔍 验证修复效果 - 检查系统性能优化")
    print("=" * 80)

    # 初始状态检查
    print("\n📊 初始系统状态:")
    initial = check_cpu_memory()
    print(f"  CPU: {initial['cpu_percent']:.1f}%")
    print(f"  Memory: {initial['memory_mb']:.1f} MB")

    print("\n🚀 启动系统...")
    agent = MainLoopController()
    agent.initialize()
    agent.start()

    # 等待系统稳定
    time.sleep(3)

    # 稳定状态检查
    print("\n📊 系统运行中... (10秒采样)")
    samples = []
    for i in range(10):
        sample = check_cpu_memory()
        samples.append(sample)
        print(f"  采样 {i+1}: CPU {sample['cpu_percent']:.1f}%, Memory {sample['memory_mb']:.1f} MB")
        time.sleep(1)

    # 计算统计
    avg_cpu = sum(s['cpu_percent'] for s in samples) / len(samples)
    avg_memory = sum(s['memory_mb'] for s in samples) / len(samples)
    max_cpu = max(s['cpu_percent'] for s in samples)

    print("\n📈 统计结果:")
    print(f"  平均CPU: {avg_cpu:.1f}%")
    print(f"  最高CPU: {max_cpu:.1f}%")
    print(f"  平均内存: {avg_memory:.1f} MB")

    # 评估修复效果
    print("\n✅ 修复评估:")
    passed = True
    if max_cpu > 50:
        print(f"  ❌ CPU仍然偏高 ({max_cpu:.1f}%)，需进一步优化")
        passed = False
    else:
        print(f"  ✅ CPU使用率优化成功 ({max_cpu:.1f}% < 50%)")

    if avg_memory - initial['memory_mb'] > 100:
        print(f"  ⚠️ 内存增长较多: {avg_memory - initial['memory_mb']:.1f} MB")
    else:
        print(f"  ✅ 内存使用稳定: ±{avg_memory - initial['memory_mb']:.1f} MB")

    # 获取系统状态
    status = agent.get_system_status()
    print(f"\n📋 系统状态:")
    print(f"  已完成任务: {status['statistics']['total_tasks']}")
    print(f"  健康状态: {status['guardian']['overall_status']}")
    print(f"  运行任务: {status['execution']['running_tasks']}")

    # 清理
    print("\n🛑 关闭系统...")
    agent.stop()
    gc.collect()

    print("\n" + "=" * 80)
    if passed:
        print("✅ 验证通过！系统修复成功！")
    else:
        print("⚠️ 部分验证未通过，需进一步优化")
    print("=" * 80)

    return passed


if __name__ == "__main__":
    run_verification_test()
