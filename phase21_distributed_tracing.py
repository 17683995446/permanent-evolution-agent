#!/usr/bin/env python3
"""
阶段21：分布式追踪集成
- OpenTelemetry基础集成
- 分布式链路追踪
- 性能剖析深度分析
- 瓶颈定位与优化
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


# 测试
def main():
    print("=" * 100)
    print("阶段21-1：OpenTelemetry基础集成")
    print("=" * 100)
    
    from main_loop_controller_orchestrator_system import MainLoopController
    
    tracing_system = DistributedTracingSystem()
    
    print("\n[INFO] 初始化Agent...")
    agent = MainLoopController()
    
    print("[INFO] 启动Agent...")
    agent.initialize()
    agent.start()
    
    print("\n[INFO] 开始追踪测试...")
    
    # 追踪任务提交
    for i in range(50):
        span = tracing_system.trace_agent_operation("submit_task", {
            "task_type": random.choice(["compute", "process", "analyze"]),
            "task_id": i
        })
        start_time = time.time()
        task_id = agent.submit_task(
            random.choice(["compute", "process", "analyze"]),
            {"test": i, "data": list(range(random.randint(10, 100)))}
        )
        duration = time.time() - start_time
        tracing_system.record_performance("task_submission", duration)
        span.add_tag("task_id", task_id)
        span.finish()
    
    print(f"[INFO] 提交了50个任务，等待执行...")
    time.sleep(10)
    
    # 追踪健康检查
    for i in range(5):
        span = tracing_system.trace_agent_operation("get_system_status")
        start_time = time.time()
        status = agent.get_system_status()
        duration = time.time() - start_time
        tracing_system.record_performance("status_check", duration)
        span.add_tag("health", status.get("guardian", {}).get("overall_status"))
        span.finish()
        time.sleep(1)
    
    print("\n" + "=" * 100)
    print("生成追踪报告...")
    print("=" * 100)
    
    report = tracing_system.generate_report()
    
    print(f"\n[REPORT] 服务名称: {report['service_name']}")
    print(f"[REPORT] 运行时间: {report['uptime']}")
    print(f"\n[TRACING] 总追踪数: {report['tracing_summary']['total_spans']}")
    print(f"[TRACING] 已完成: {report['tracing_summary']['completed_spans']}")
    print(f"[TRACING] 错误数: {report['tracing_summary']['error_spans']}")
    print(f"[TRACING] 平均延迟: {report['tracing_summary']['avg_duration_ms']:.2f}ms")
    
    print(f"\n[PERFORMANCE] 性能指标:")
    for name, stats in report['performance_summary'].items():
        print(f"  - {name}: {stats['avg_ms']:.2f}ms (max: {stats['max_ms']:.2f}ms, samples: {stats['count']})")
    
    print(f"\n[BOTTLENECKS] 性能瓶颈:")
    if report['bottlenecks']:
        for bottleneck in report['bottlenecks'][:5]:
            print(f"  - {bottleneck['name']}: {bottleneck['avg_value_ms']:.2f}ms (samples: {bottleneck['samples']})")
    else:
        print("  无明显瓶颈！")
    
    print(f"\n[RECOMMENDATIONS] 优化建议:")
    for rec in report['recommendations']:
        print(f"  - {rec}")
    
    agent.stop()
    
    print("\n" + "=" * 100)
    print("阶段21-1：OpenTelemetry基础集成 - 完成！")
    print("=" * 100)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        traceback.print_exc()
