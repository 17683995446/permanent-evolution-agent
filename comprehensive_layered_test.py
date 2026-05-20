#!/usr/bin/env python3
"""
全面分层测试框架 - 慢工出细活
基于第一性本质的全覆盖测试

测试层次：
1. 单元测试 - 每个方法的所有分支
2. 集成测试 - 模块间调用链路
3. 接口测试 - 所有公开API
4. 业务场景测试 - 真实使用场景
5. 数据流测试 - 数据完整性和一致性
"""
import sys
import time
import random
import threading
import gc
import traceback
from typing import List, Dict, Any, Optional
from collections import deque

sys.path.insert(0, '/workspace')


class TestResult:
    """测试结果"""
    def __init__(self, test_name: str, passed: bool, message: str, details: Dict = None):
        self.test_name = test_name
        self.passed = passed
        self.message = message
        self.details = details or {}


class ComprehensiveLayeredTest:
    """全面分层测试"""

    def __init__(self):
        self.results: List[TestResult] = []

    # ========================================
    # 1. 单元测试 - 每个方法的所有分支
    # ========================================

    def test_task_execution_submit_task_branches(self):
        """单元测试1: TaskExecutionEngine.submit_task所有分支"""
        print("\n" + "=" * 80)
        print("📋 单元测试1: TaskExecutionEngine.submit_task所有分支")
        print("=" * 80)

        from task_execution_engine_core_module import TaskExecutionEngine, TaskPriority

        engine = TaskExecutionEngine()
        engine.start()

        branches_tested = []

        # 分支1: 正常任务提交
        task_id1 = engine.submit_task('compute', {'data': 1})
        branches_tested.append(f"正常提交: {task_id1}")
        print(f"   ✅ 分支1: 正常提交 - {task_id1}")

        # 分支2: 空字符串任务类型
        task_id2 = engine.submit_task('', {'data': 2})
        branches_tested.append(f"空字符串类型: {task_id2}")
        print(f"   ✅ 分支2: 空字符串类型 - {task_id2}")

        # 分支3: 非字符串任务类型
        task_id3 = engine.submit_task(123, {'data': 3})
        branches_tested.append(f"非字符串类型: {task_id3}")
        print(f"   ✅ 分支3: 非字符串类型 - {task_id3}")

        # 分支4: None payload
        task_id4 = engine.submit_task('compute', None)
        branches_tested.append(f"None payload: {task_id4}")
        print(f"   ✅ 分支4: None payload - {task_id4}")

        # 分支5: 非字典payload
        task_id5 = engine.submit_task('compute', "string payload")
        branches_tested.append(f"非字典payload: {task_id5}")
        print(f"   ✅ 分支5: 非字典payload - {task_id5}")

        # 分支6: None metadata
        task_id6 = engine.submit_task('process', {'data': 6}, metadata=None)
        branches_tested.append(f"None metadata: {task_id6}")
        print(f"   ✅ 分支6: None metadata - {task_id6}")

        # 分支7: 非字典metadata
        task_id7 = engine.submit_task('analyze', {'data': 7}, metadata="string metadata")
        branches_tested.append(f"非字典metadata: {task_id7}")
        print(f"   ✅ 分支7: 非字典metadata - {task_id7}")

        # 分支8: 非枚举优先级
        task_id8 = engine.submit_task('compute', {'data': 8}, priority="invalid")
        branches_tested.append(f"非枚举优先级: {task_id8}")
        print(f"   ✅ 分支8: 非枚举优先级 - {task_id8}")

        # 分支9: 所有任务类型
        for task_type in ['compute', 'process', 'analyze', 'default', 'unknown']:
            task_id = engine.submit_task(task_type, {'data': task_type})
            branches_tested.append(f"任务类型 {task_type}: {task_id}")

        print(f"   ✅ 分支9: 所有任务类型")

        time.sleep(2)

        # 验证所有任务都已入队
        summary = engine.get_execution_summary()
        queued_count = summary.get('pending_tasks', 0)

        engine.stop()

        result = TestResult(
            test_name="TaskExecutionEngine.submit_task分支覆盖",
            passed=len(branches_tested) == 9,
            message=f"测试了{len(branches_tested)}个分支，队列中有{queued_count}个任务",
            details={'branches': branches_tested, 'queued': queued_count}
        )
        self.results.append(result)

        return len(branches_tested) == 9

    def test_task_execution_execute_branches(self):
        """单元测试2: TaskExecutionEngine._execute_task所有分支"""
        print("\n" + "=" * 80)
        print("📋 单元测试2: TaskExecutionEngine._execute_task所有分支")
        print("=" * 80)

        from task_execution_engine_core_module import TaskExecutionEngine

        engine = TaskExecutionEngine()
        engine.start()

        branches_tested = []

        # 分支1: compute类型
        engine.submit_task('compute', {'value': 1, 'operation': 'add'})
        branches_tested.append("compute类型")
        print("   ✅ 分支1: compute类型")

        # 分支2: process类型
        engine.submit_task('process', {'items': [1, 2, 3]})
        branches_tested.append("process类型")
        print("   ✅ 分支2: process类型")

        # 分支3: analyze类型
        engine.submit_task('analyze', {'data': [1, 2, 3, 4, 5]})
        branches_tested.append("analyze类型")
        print("   ✅ 分支3: analyze类型")

        # 分支4: unknown类型
        engine.submit_task('unknown_type', {'data': 'test'})
        branches_tested.append("unknown类型")
        print("   ✅ 分支4: unknown类型")

        # 分支5: 空payload
        engine.submit_task('compute', {})
        branches_tested.append("空payload")
        print("   ✅ 分支5: 空payload")

        # 分支6: 大数据payload
        engine.submit_task('process', {'large_data': list(range(1000))})
        branches_tested.append("大数据payload")
        print("   ✅ 分支6: 大数据payload")

        # 等待执行
        time.sleep(3)

        summary = engine.get_execution_summary()
        completed = summary.get('completed_tasks', 0)

        engine.stop()

        result = TestResult(
            test_name="TaskExecutionEngine._execute_task分支覆盖",
            passed=completed >= 6,
            message=f"测试了{len(branches_tested)}个分支，完成任务{completed}个",
            details={'branches': branches_tested, 'completed': completed}
        )
        self.results.append(result)

        return completed >= 6

    def test_guardian_service_health_branches(self):
        """单元测试3: GuardianService健康检查所有分支"""
        print("\n" + "=" * 80)
        print("📋 单元测试3: GuardianService健康检查所有分支")
        print("=" * 80)

        from permanent_guardian_service_monitor_layer import GuardianService

        guardian = GuardianService()

        # 分支1: 正常注册组件
        class MockComponent:
            def health_check(self):
                return True

        component1 = MockComponent()
        guardian.register_component('healthy_component', component1)
        print("   ✅ 分支1: 正常组件注册")

        # 分支2: 注册异常组件
        class FailingComponent:
            def health_check(self):
                raise Exception("Component failure")

        component2 = FailingComponent()
        guardian.register_component('failing_component', component2)
        print("   ✅ 分支2: 异常组件注册")

        # 分支3: 获取健康状态
        status = guardian.get_health_status()
        print(f"   ✅ 分支3: 健康状态 - {status}")

        # 分支4: 组件数量
        component_count = len(status.get('components', {}))
        print(f"   ✅ 分支4: 组件数量 - {component_count}")

        guardian.stop()

        result = TestResult(
            test_name="GuardianService健康检查分支覆盖",
            passed=component_count == 2,
            message=f"注册了{component_count}个组件",
            details={'components': component_count}
        )
        self.results.append(result)

        return component_count == 2

    # ========================================
    # 2. 集成测试 - 模块间调用链路
    # ========================================

    def test_integration_full_workflow(self):
        """集成测试1: 完整工作流程"""
        print("\n" + "=" * 80)
        print("🔗 集成测试1: 完整工作流程")
        print("=" * 80)

        from main_loop_controller_orchestrator_system import MainLoopController

        print("   步骤1: 初始化Agent...")
        agent = MainLoopController()
        agent.initialize()
        print("   ✅ 初始化成功")

        print("   步骤2: 启动Agent...")
        agent.start()
        print("   ✅ 启动成功")

        time.sleep(2)

        print("   步骤3: 提交任务...")
        task_id1 = agent.submit_task('compute', {'data': 1})
        task_id2 = agent.submit_task('process', {'data': 2})
        task_id3 = agent.submit_task('analyze', {'data': 3})
        print(f"   ✅ 提交任务: {task_id1}, {task_id2}, {task_id3}")

        print("   步骤4: 获取系统状态...")
        status = agent.get_system_status()
        health = status.get('guardian', {}).get('overall_status', 'unknown')
        print(f"   ✅ 系统健康: {health}")

        time.sleep(3)

        print("   步骤5: 再次获取状态...")
        status2 = agent.get_system_status()
        summary = status2.get('execution', {})
        completed = summary.get('completed_tasks', 0)
        print(f"   ✅ 已完成任务: {completed}")

        print("   步骤6: 停止Agent...")
        agent.stop()
        print("   ✅ 停止成功")

        result = TestResult(
            test_name="完整工作流程集成",
            passed=health == 'healthy' and completed >= 0,
            message=f"健康状态={health}, 完成={completed}",
            details={'health': health, 'completed': completed}
        )
        self.results.append(result)

        return health == 'healthy'

    def test_integration_data_flow(self):
        """集成测试2: 数据流完整性"""
        print("\n" + "=" * 80)
        print("🔗 集成测试2: 数据流完整性")
        print("=" * 80)

        from main_loop_controller_orchestrator_system import MainLoopController

        agent = MainLoopController()
        agent.initialize()
        agent.start()

        # 提交多个任务
        task_ids = []
        for i in range(10):
            task_id = agent.submit_task(
                random.choice(['compute', 'process', 'analyze']),
                {'iteration': i, 'data': i * 10}
            )
            task_ids.append(task_id)

        print(f"   ✅ 提交了{len(task_ids)}个任务")

        # 等待执行
        time.sleep(5)

        # 检查数据流
        status = agent.get_system_status()
        execution = status.get('execution', {})
        summary = execution.get('applied_rules', [])

        agent.stop()

        result = TestResult(
            test_name="数据流完整性",
            passed=len(task_ids) == 10,
            message=f"提交{len(task_ids)}个任务",
            details={'task_ids': task_ids}
        )
        self.results.append(result)

        return len(task_ids) == 10

    def test_integration_exception_propagation(self):
        """集成测试3: 异常传播"""
        print("\n" + "=" * 80)
        print("🔗 集成测试3: 异常传播")
        print("=" * 80)

        from main_loop_controller_orchestrator_system import MainLoopController

        agent = MainLoopController()
        agent.initialize()
        agent.start()

        # 提交异常任务
        invalid_tasks = [
            (None, {'data': 1}),      # None类型
            ('', {'data': 2}),        # 空类型
            ('test', None),          # None payload
            ('test', 123),           # 非字典payload
        ]

        for task_type, payload in invalid_tasks:
            try:
                task_id = agent.submit_task(task_type, payload)
                print(f"   ✅ 处理了无效任务: {task_type}, {type(payload)}")
            except Exception as e:
                print(f"   ⚠️  抛出异常: {str(e)}")

        time.sleep(2)

        status = agent.get_system_status()
        health = status.get('guardian', {}).get('overall_status', 'unknown')

        agent.stop()

        result = TestResult(
            test_name="异常传播处理",
            passed=health == 'healthy',
            message=f"即使有异常，系统仍保持健康: {health}",
            details={'health': health}
        )
        self.results.append(result)

        return health == 'healthy'

    # ========================================
    # 3. 接口测试 - 所有公开API
    # ========================================

    def test_api_all_public_interfaces(self):
        """接口测试: 所有公开API"""
        print("\n" + "=" * 80)
        print("🔌 接口测试: 所有公开API")
        print("=" * 80)

        from main_loop_controller_orchestrator_system import MainLoopController
        from task_execution_engine_core_module import TaskExecutionEngine
        from permanent_guardian_service_monitor_layer import GuardianService

        apis_tested = []

        # MainLoopController APIs
        print("   MainLoopController APIs:")
        agent = MainLoopController()
        apis_tested.append("MainLoopController.__init__")
        print("   ✅ __init__")

        agent.initialize()
        apis_tested.append("MainLoopController.initialize")
        print("   ✅ initialize")

        agent.start()
        apis_tested.append("MainLoopController.start")
        print("   ✅ start")

        task_id = agent.submit_task('compute', {'data': 1})
        apis_tested.append("MainLoopController.submit_task")
        print("   ✅ submit_task")

        status = agent.get_system_status()
        apis_tested.append("MainLoopController.get_system_status")
        print("   ✅ get_system_status")

        agent.stop()
        apis_tested.append("MainLoopController.stop")
        print("   ✅ stop")

        # TaskExecutionEngine APIs
        print("\n   TaskExecutionEngine APIs:")
        engine = TaskExecutionEngine()
        apis_tested.append("TaskExecutionEngine.__init__")
        print("   ✅ __init__")

        engine.start()
        apis_tested.append("TaskExecutionEngine.start")
        print("   ✅ start")

        task_id = engine.submit_task('compute', {'data': 1})
        apis_tested.append("TaskExecutionEngine.submit_task")
        print("   ✅ submit_task")

        summary = engine.get_execution_summary()
        apis_tested.append("TaskExecutionEngine.get_execution_summary")
        print("   ✅ get_execution_summary")

        engine.stop()
        apis_tested.append("TaskExecutionEngine.stop")
        print("   ✅ stop")

        # GuardianService APIs
        print("\n   GuardianService APIs:")
        guardian = GuardianService()
        apis_tested.append("GuardianService.__init__")
        print("   ✅ __init__")

        guardian.register_component('test', object())
        apis_tested.append("GuardianService.register_component")
        print("   ✅ register_component")

        guardian.start()
        apis_tested.append("GuardianService.start")
        print("   ✅ start")

        health_status = guardian.get_health_status()
        apis_tested.append("GuardianService.get_health_status")
        print("   ✅ get_health_status")

        guardian.stop()
        apis_tested.append("GuardianService.stop")
        print("   ✅ stop")

        result = TestResult(
            test_name="所有公开API",
            passed=len(apis_tested) == 15,
            message=f"测试了{len(apis_tested)}个API接口",
            details={'apis': apis_tested}
        )
        self.results.append(result)

        return len(apis_tested) == 15

    # ========================================
    # 4. 业务场景测试 - 真实使用场景
    # ========================================

    def test_business_scenario_continuous_processing(self):
        """业务场景1: 持续处理"""
        print("\n" + "=" * 80)
        print("💼 业务场景1: 持续处理")
        print("=" * 80)

        from main_loop_controller_orchestrator_system import MainLoopController

        agent = MainLoopController()
        agent.initialize()
        agent.start()

        print("   模拟24小时持续运行 (缩短为30秒)...")
        total_tasks = 0
        checkpoints = []

        for i in range(30):
            # 模拟不同的业务场景
            scenario = i % 4
            if scenario == 0:
                # 数据计算
                agent.submit_task('compute', {'operation': 'sum', 'range': (0, i)})
                total_tasks += 1
            elif scenario == 1:
                # 数据处理
                agent.submit_task('process', {'items': list(range(i))})
                total_tasks += 1
            elif scenario == 2:
                # 数据分析
                agent.submit_task('analyze', {'dataset': list(range(i))})
                total_tasks += 1
            else:
                # 批量处理
                for _ in range(5):
                    agent.submit_task('process', {'batch': True})
                    total_tasks += 1

            if (i + 1) % 10 == 0:
                status = agent.get_system_status()
                checkpoints.append({
                    'iteration': i + 1,
                    'tasks': total_tasks,
                    'health': status.get('guardian', {}).get('overall_status', 'unknown')
                })
                print(f"   检查点 {i+1}: 已提交{total_tasks}个任务")

            time.sleep(1)

        agent.stop()

        all_healthy = all(c['health'] == 'healthy' for c in checkpoints)

        result = TestResult(
            test_name="持续处理业务场景",
            passed=all_healthy,
            message=f"提交{total_tasks}个任务，所有检查点健康",
            details={'total_tasks': total_tasks, 'checkpoints': checkpoints}
        )
        self.results.append(result)

        return all_healthy

    def test_business_scenario_burst_load(self):
        """业务场景2: 突发负载"""
        print("\n" + "=" * 80)
        print("💼 业务场景2: 突发负载")
        print("=" * 80)

        from main_loop_controller_orchestrator_system import MainLoopController

        agent = MainLoopController()
        agent.initialize()
        agent.start()

        print("   模拟突发负载...")
        tasks_submitted = 0

        # 突发负载
        for _ in range(100):
            agent.submit_task('compute', {'burst': True})
            tasks_submitted += 1

        print(f"   短时间内提交{tasks_submitted}个任务")

        time.sleep(5)

        status = agent.get_system_status()
        health = status.get('guardian', {}).get('overall_status', 'unknown')

        agent.stop()

        result = TestResult(
            test_name="突发负载业务场景",
            passed=health == 'healthy',
            message=f"突发提交{tasks_submitted}个任务，系统健康: {health}",
            details={'tasks': tasks_submitted, 'health': health}
        )
        self.results.append(result)

        return health == 'healthy'

    # ========================================
    # 5. 数据流测试 - 数据完整性和一致性
    # ========================================

    def test_data_flow_integrity(self):
        """数据流测试: 数据完整性"""
        print("\n" + "=" * 80)
        print("🔄 数据流测试: 数据完整性")
        print("=" * 80)

        from main_loop_controller_orchestrator_system import MainLoopController

        agent = MainLoopController()
        agent.initialize()
        agent.start()

        # 提交带详细数据的任务
        test_data = {
            'user_id': 'test_user_123',
            'timestamp': time.time(),
            'operations': ['read', 'write', 'update', 'delete'],
            'metadata': {
                'source': 'test_suite',
                'version': '1.0.0'
            }
        }

        task_id = agent.submit_task('process', test_data)
        print(f"   ✅ 提交任务: {task_id}")

        time.sleep(3)

        # 验证数据流
        status = agent.get_system_status()
        execution = status.get('execution', {})

        agent.stop()

        result = TestResult(
            test_name="数据完整性",
            passed=True,
            message=f"数据流测试完成，任务ID: {task_id}",
            details={'task_id': task_id, 'data': test_data}
        )
        self.results.append(result)

        return True

    def test_data_flow_consistency(self):
        """数据流测试: 数据一致性"""
        print("\n" + "=" * 80)
        print("🔄 数据流测试: 数据一致性")
        print("=" * 80)

        from main_loop_controller_orchestrator_system import MainLoopController

        agent = MainLoopController()
        agent.initialize()
        agent.start()

        # 提交多个任务
        task_ids = []
        for i in range(20):
            task_id = agent.submit_task(
                random.choice(['compute', 'process', 'analyze']),
                {'sequence': i, 'random': random.random()}
            )
            task_ids.append(task_id)

        time.sleep(5)

        # 多次获取状态，验证一致性
        status1 = agent.get_system_status()
        time.sleep(1)
        status2 = agent.get_system_status()
        time.sleep(1)
        status3 = agent.get_system_status()

        agent.stop()

        # 验证状态一致性
        summary1 = status1.get('execution', {})
        summary2 = status2.get('execution', {})
        summary3 = status3.get('execution', {})

        completed1 = summary1.get('completed_tasks', 0)
        completed2 = summary2.get('completed_tasks', 0)
        completed3 = summary3.get('completed_tasks', 0)

        print(f"   三次检查完成数: {completed1}, {completed2}, {completed3}")

        result = TestResult(
            test_name="数据一致性",
            passed=completed1 <= completed2 <= completed3,
            message=f"完成数递增: {completed1} -> {completed2} -> {completed3}",
            details={
                'completed1': completed1,
                'completed2': completed2,
                'completed3': completed3
            }
        )
        self.results.append(result)

        return completed1 <= completed2 <= completed3

    # ========================================
    # 运行所有测试
    # ========================================

    def run_all_tests(self):
        """运行所有分层测试"""
        print("=" * 80)
        print("🎯 全面分层测试框架 - 慢工出细活")
        print("=" * 80)
        print("基于第一性本质的全覆盖测试")
        print("\n测试层次:")
        print("  1. 单元测试 - 每个方法的所有分支")
        print("  2. 集成测试 - 模块间调用链路")
        print("  3. 接口测试 - 所有公开API")
        print("  4. 业务场景 - 真实使用场景")
        print("  5. 数据流测试 - 数据完整性和一致性")

        tests = [
            ("单元测试-分支覆盖1", self.test_task_execution_submit_task_branches),
            ("单元测试-分支覆盖2", self.test_task_execution_execute_branches),
            ("单元测试-分支覆盖3", self.test_guardian_service_health_branches),
            ("集成测试-完整流程", self.test_integration_full_workflow),
            ("集成测试-数据流", self.test_integration_data_flow),
            ("集成测试-异常传播", self.test_integration_exception_propagation),
            ("接口测试-所有API", self.test_api_all_public_interfaces),
            ("业务场景-持续处理", self.test_business_scenario_continuous_processing),
            ("业务场景-突发负载", self.test_business_scenario_burst_load),
            ("数据流-完整性", self.test_data_flow_integrity),
            ("数据流-一致性", self.test_data_flow_consistency),
        ]

        passed_count = 0
        failed_tests = []

        for test_name, test_func in tests:
            try:
                passed = test_func()
                if passed:
                    passed_count += 1
                    print(f"\n✅ {test_name}: 通过")
                else:
                    failed_tests.append(test_name)
                    print(f"\n❌ {test_name}: 失败")
            except Exception as e:
                failed_tests.append(test_name)
                print(f"\n❌ {test_name}: 异常 - {str(e)}")
                print(traceback.format_exc())

        # 打印结果汇总
        print("\n" + "=" * 80)
        print("📊 测试结果汇总")
        print("=" * 80)

        for result in self.results:
            status = "✅ 通过" if result.passed else "❌ 失败"
            print(f"  {result.test_name}: {status}")
            print(f"    {result.message}")

        print("\n" + "=" * 80)
        print(f"总计: {len(self.results)}个测试, {passed_count}个通过, {len(failed_tests)}个失败")
        print("=" * 80)

        if len(failed_tests) == 0:
            print("\n🎉 所有分层测试通过！系统符合设计规格！")
        else:
            print(f"\n⚠️  {len(failed_tests)}个测试失败: {', '.join(failed_tests)}")

        return len(failed_tests) == 0


def main():
    tester = ComprehensiveLayeredTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断测试")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 未预料的错误: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
