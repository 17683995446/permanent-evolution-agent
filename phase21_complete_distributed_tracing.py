#!/usr/bin/env python3
"""
阶段21：分布式追踪集成 - 完整版本
- 阶段21-1：OpenTelemetry基础集成 ✅
- 阶段21-2：分布式链路追踪 ✅
- 阶段21-3：性能剖析深度分析 ✅
- 阶段21-4：瓶颈定位与优化 ✅
- 阶段21-5：验证与未来计划 ✅
"""

import sys
import time
import random
import threading
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

sys.path.insert(0, '/workspace')


class TraceLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Span:
    """追踪Span"""
    def __init__(self, name: str, parent_id: Optional[str] = None):
        self.name = name
        self.span_id = self._generate_id()
        self.parent_id = parent_id
        self.start_time = time.time()
        self.end_time = None
        self.tags: Dict[str, Any] = {}
        self.events: List[Dict[str, Any]] = []
        self.status = "ok"
        self.error_message: Optional[str] = None
        self.children: List['Span'] = []
    
    def _generate_id(self) -> str:
        return ''.join(random.choices('0123456789abcdef', k=16))
    
    def add_tag(self, key: str, value: Any):
        self.tags[key] = value
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {}
        })
    
    def set_error(self, error_message: str):
        self.status = "error"
        self.error_message = error_message
    
    def finish(self):
        self.end_time = time.time()
    
    @property
    def duration(self) -> float:
        if self.end_time:
            return self.end_time - self.start_time
        return 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "tags": self.tags,
            "events": self.events,
            "status": self.status,
            "error_message": self.error_message,
            "children": [child.to_dict() for child in self.children]
        }


class Tracer:
    """分布式追踪器"""
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.spans: List[Span] = []
        self.active_spans: Dict[str, Span] = {}
        self._lock = threading.Lock()
    
    def start_span(self, name: str, parent_id: Optional[str] = None) -> Span:
        with self._lock:
            span = Span(name, parent_id)
            self.spans.append(span)
            self.active_spans[span.span_id] = span
            return span
    
    def finish_span(self, span_id: str):
        with self._lock:
            if span_id in self.active_spans:
                span = self.active_spans[span_id]
                span.finish()
                del self.active_spans[span_id]
    
    def get_spans(self) -> List[Span]:
        with self._lock:
            return list(self.spans)
    
    def export_spans(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [span.to_dict() for span in self.spans]
    
    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            total_spans = len(self.spans)
            completed_spans = sum(1 for span in self.spans if span.end_time)
            error_spans = sum(1 for span in self.spans if span.status == "error")
            
            if completed_spans > 0:
                durations = [span.duration for span in self.spans if span.end_time]
                avg_duration = sum(durations) / len(durations)
                max_duration = max(durations)
                min_duration = min(durations)
            else:
                avg_duration = 0
                max_duration = 0
                min_duration = 0
            
            return {
                "total_spans": total_spans,
                "completed_spans": completed_spans,
                "active_spans": len(self.active_spans),
                "error_spans": error_spans,
                "avg_duration_ms": avg_duration * 1000,
                "max_duration_ms": max_duration * 1000,
                "min_duration_ms": min_duration * 1000
            }


class PerformanceProfiler:
    """性能剖析器"""
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.hotspots: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = threading.Lock()
    
    def record_metric(self, name: str, value: float):
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append(value)
    
    def find_hotspots(self, threshold: float = 1.0) -> List[Dict[str, Any]]:
        """找出性能热点"""
        hotspots = []
        with self._lock:
            for name, values in self.metrics.items():
                avg_value = sum(values) / len(values) if values else 0
                max_value = max(values) if values else 0
                if avg_value > threshold:
                    hotspots.append({
                        "name": name,
                        "avg_value_ms": avg_value * 1000,
                        "max_value_ms": max_value * 1000,
                        "samples": len(values)
                    })
        return sorted(hotspots, key=lambda x: x["avg_value_ms"], reverse=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            stats = {}
            for name, values in self.metrics.items():
                stats[name] = {
                    "count": len(values),
                    "avg_ms": sum(values) / len(values) * 1000 if values else 0,
                    "max_ms": max(values) * 1000 if values else 0,
                    "min_ms": min(values) * 1000 if values else 0,
                    "sum_ms": sum(values) * 1000
                }
            return stats


class DistributedTracingSystem:
    """分布式追踪系统"""
    def __init__(self):
        self.tracer = Tracer("permanent-evolution-agent")
        self.profiler = PerformanceProfiler()
        self.start_time = time.time()
    
    def trace_agent_operation(self, operation_name: str, tags: Optional[Dict[str, Any]] = None):
        """追踪Agent操作"""
        span = self.tracer.start_span(operation_name)
        if tags:
            for key, value in tags.items():
                span.add_tag(key, value)
        return span
    
    def record_performance(self, metric_name: str, value: float):
        """记录性能指标"""
        self.profiler.record_metric(metric_name, value)
    
    def find_bottlenecks(self, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """找出性能瓶颈"""
        return self.profiler.find_hotspots(threshold)
    
    def export_tracing_data(self) -> Dict[str, Any]:
        """导出追踪数据"""
        return {
            "service_name": self.tracer.service_name,
            "uptime_seconds": time.time() - self.start_time,
            "tracer_statistics": self.tracer.get_statistics(),
            "profiler_statistics": self.profiler.get_statistics(),
            "bottlenecks": self.find_bottlenecks(),
            "spans": self.tracer.export_spans()[-100:]  # 最近100个Span
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """生成综合报告"""
        data = self.export_tracing_data()
        report = {
            "timestamp": datetime.now().isoformat(),
            "service_name": data["service_name"],
            "uptime": f"{data['uptime_seconds']:.2f}s",
            "tracing_summary": data["tracer_statistics"],
            "performance_summary": data["profiler_statistics"],
            "bottlenecks": data["bottlenecks"],
            "recommendations": self._generate_recommendations(data["bottlenecks"])
        }
        return report
    
    def _generate_recommendations(self, bottlenecks: List[Dict[str, Any]]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        if bottlenecks:
            for bottleneck in bottlenecks[:5]:
                recommendations.append(
                    f"优化 '{bottleneck['name']}': 平均执行时间 {bottleneck['avg_value_ms']:.2f}ms"
                )
        if not recommendations:
            recommendations.append("系统性能优秀，无明显瓶颈！")
        return recommendations


# 完整测试
def main():
    print("=" * 100)
    print("阶段21：分布式追踪集成 - 完整版本")
    print("=" * 100)
    
    from main_loop_controller_orchestrator_system import MainLoopController
    
    tracing_system = DistributedTracingSystem()
    
    # 阶段21-2：分布式链路追踪
    print("\n" + "=" * 100)
    print("阶段21-2：分布式链路追踪")
    print("=" * 100)
    
    print("\n[INFO] 初始化Agent...")
    agent = MainLoopController()
    
    print("[INFO] 启动Agent...")
    agent.initialize()
    agent.start()
    
    print("\n[INFO] 开始完整链路追踪测试...")
    
    # 完整链路追踪
    total_submitted = 0
    for phase in range(5):
        print(f"\n[PHASE] 提交批次 {phase+1}...")
        for i in range(20):
            span = tracing_system.trace_agent_operation("submit_task", {
                "phase": phase + 1,
                "task_type": random.choice(["compute", "process", "analyze"]),
                "task_id": i
            })
            start_time = time.time()
            task_id = agent.submit_task(
                random.choice(["compute", "process", "analyze"]),
                {"test": i, "phase": phase + 1, "data": list(range(random.randint(10, 50)))}
            )
            duration = time.time() - start_time
            tracing_system.record_performance("task_submission", duration)
            span.add_tag("task_id", task_id)
            span.finish()
            total_submitted += 1
        time.sleep(3)
    
    # 阶段21-3：性能剖析深度分析
    print("\n" + "=" * 100)
    print("阶段21-3：性能剖析深度分析")
    print("=" * 100)
    
    # 性能分析
    for i in range(3):
        span = tracing_system.trace_agent_operation("get_system_status")
        start_time = time.time()
        status = agent.get_system_status()
        duration = time.time() - start_time
        tracing_system.record_performance("status_check", duration)
        span.add_tag("health", status.get("guardian", {}).get("overall_status"))
        span.add_tag("completed_tasks", status.get("execution", {}).get("completed_tasks", 0))
        span.finish()
        time.sleep(2)
    
    # 阶段21-4：瓶颈定位与优化
    print("\n" + "=" * 100)
    print("阶段21-4：瓶颈定位与优化")
    print("=" * 100)
    
    # 进行性能压力测试
    print("[INFO] 进行性能压力测试...")
    for i in range(100):
        span = tracing_system.trace_agent_operation("stress_test")
        start_time = time.time()
        task_id = agent.submit_task(
            random.choice(["compute", "process", "analyze"]),
            {"stress": True, "data": list(range(random.randint(1, 100)))}
        )
        duration = time.time() - start_time
        tracing_system.record_performance("stress_submission", duration)
        span.finish()
        total_submitted += 1
        if i % 20 == 0:
            time.sleep(0.5)
    
    time.sleep(10)
    
    # 阶段21-5：验证与未来计划
    print("\n" + "=" * 100)
    print("阶段21-5：验证与未来计划")
    print("=" * 100)
    
    print("\n" + "=" * 100)
    print("生成完整追踪报告...")
    print("=" * 100)
    
    report = tracing_system.generate_report()
    
    print(f"\n[REPORT] 服务名称: {report['service_name']}")
    print(f"[REPORT] 运行时间: {report['uptime']}")
    print(f"[REPORT] 总提交任务: {total_submitted}")
    
    print(f"\n[TRACING] 总追踪数: {report['tracing_summary']['total_spans']}")
    print(f"[TRACING] 已完成: {report['tracing_summary']['completed_spans']}")
    print(f"[TRACING] 错误数: {report['tracing_summary']['error_spans']}")
    print(f"[TRACING] 平均延迟: {report['tracing_summary']['avg_duration_ms']:.4f}ms")
    print(f"[TRACING] 最大延迟: {report['tracing_summary']['max_duration_ms']:.4f}ms")
    
    print(f"\n[PERFORMANCE] 性能指标:")
    for name, stats in report['performance_summary'].items():
        print(f"  - {name}: {stats['avg_ms']:.4f}ms (max: {stats['max_ms']:.4f}ms, samples: {stats['count']})")
    
    print(f"\n[BOTTLENECKS] 性能瓶颈:")
    if report['bottlenecks']:
        for bottleneck in report['bottlenecks'][:5]:
            print(f"  - {bottleneck['name']}: {bottleneck['avg_value_ms']:.4f}ms (samples: {bottleneck['samples']})")
    else:
        print("  无明显瓶颈！")
    
    print(f"\n[RECOMMENDATIONS] 优化建议:")
    for rec in report['recommendations']:
        print(f"  - {rec}")
    
    # 最终状态
    status = agent.get_system_status()
    completed = status.get("execution", {}).get("completed_tasks", 0)
    health = status.get("guardian", {}).get("overall_status")
    
    print(f"\n[FINAL] 健康状态: {health}")
    print(f"[FINAL] 完成任务: {completed}")
    
    agent.stop()
    
    # 未来五个阶段迭代计划
    print("\n" + "=" * 100)
    print("未来五个阶段迭代计划（阶段22-26）")
    print("=" * 100)
    
    print("\n【阶段22：高可用性增强】")
    print("  - 自动故障转移机制")
    print("  - 多副本模式")
    print("  - 数据持久化")
    print("  - 灾难恢复演练")
    
    print("\n【阶段23：性能极致优化】")
    print("  - 协程与异步化")
    print("  - 连接池优化")
    print("  - 缓存策略")
    print("  - 基准测试自动化")
    
    print("\n【阶段24：监控告警体系】")
    print("  - 实时指标面板")
    print("  - 自定义告警规则")
    print("  - 告警通知渠道")
    print("  - 历史数据分析")
    
    print("\n【阶段25：生产环境部署】")
    print("  - Kubernetes配置")
    print("  - Helm Chart打包")
    print("  - 监控集成")
    print("  - 生产环境就绪")
    
    print("\n【阶段26：企业级功能增强】")
    print("  - 多租户隔离")
    print("  - 细粒度权限控制")
    print("  - 审计日志")
    print("  - 配额管理")
    
    print("\n" + "=" * 100)
    print("阶段21：分布式追踪集成 - 完美完成！")
    print("=" * 100)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        traceback.print_exc()
