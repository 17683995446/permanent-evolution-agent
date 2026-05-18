#!/usr/bin/env python3
"""快速验证测试 - 检查系统基本功能"""
import sys
import time
import traceback

sys.path.insert(0, '/workspace')

print("=" * 80)
print("🧪 快速验证测试")
print("=" * 80)

try:
    from main_loop_controller_orchestrator_system import MainLoopController
    
    print("\n📦 初始化Agent...")
    agent = MainLoopController()
    agent.initialize()
    agent.start()
    
    print("✅ Agent初始化和启动成功")
    
    time.sleep(2)
    
    print("\n📝 测试任务提交...")
    task_ids = []
    for i in range(5):
        task_id = agent.submit_task(
            'compute',
            {'test': i, 'data': [1, 2, 3, 4, 5]}
        )
        task_ids.append(task_id)
        print(f"   提交任务 {i+1}: {task_id}")
    
    print("✅ 任务提交成功")
    
    time.sleep(3)
    
    print("\n📊 获取系统状态...")
    status = agent.get_system_status()
    print(f"   运行状态: {status['running']}")
    print(f"   Guardian健康: {status['guardian']['overall_status']}")
    print(f"   运行任务: {status['execution']['running_tasks']}")
    print(f"   完成任务: {status['execution']['completed_tasks']}")
    
    print("\n🛑 停止Agent...")
    agent.stop()
    print("✅ Agent停止成功")
    
    print("\n" + "=" * 80)
    print("🎉 快速验证测试通过!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ 测试失败: {str(e)}")
    print(traceback.format_exc())
    sys.exit(1)
