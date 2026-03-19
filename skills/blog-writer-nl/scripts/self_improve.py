#!/usr/bin/env python3
"""
Blog Writer Skill - Self-Improve System
自我改进系统：收集反馈、分析性能、优化策略
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ExecutionFeedback:
    """执行反馈数据"""
    execution_id: str
    timestamp: str
    topic: str
    target_word_count: int
    actual_word_count: int
    word_count_accuracy: float  # 字数准确率
    success: bool
    error_message: Optional[str]
    user_rating: Optional[int]  # 用户评分 1-5
    user_feedback: Optional[str]  # 用户文字反馈
    execution_time_ms: int
    style: str
    keywords_count: int


@dataclass
class PerformanceMetrics:
    """性能指标"""
    total_executions: int
    success_rate: float
    avg_word_count_accuracy: float
    avg_execution_time_ms: int
    user_satisfaction: float  # 基于用户评分的满意度
    common_errors: List[Dict[str, Any]]
    improvement_suggestions: List[str]


class FeedbackCollector:
    """反馈收集器"""
    
    def __init__(self, feedback_dir: str = None):
        if feedback_dir is None:
            # 默认保存到 skill 目录下的 .feedback 文件夹
            skill_dir = Path(__file__).parent.parent
            feedback_dir = skill_dir / ".feedback"
        
        self.feedback_dir = Path(feedback_dir)
        self.feedback_dir.mkdir(exist_ok=True)
        
        self.feedback_file = self.feedback_dir / "execution_feedback.jsonl"
        self.metrics_file = self.feedback_dir / "performance_metrics.json"
    
    def record_execution(self, params: Dict, result: Dict, execution_time_ms: int) -> str:
        """记录一次执行"""
        execution_id = f"exec_{int(time.time() * 1000)}"
        
        # 计算字数准确率（允许 ±20% 误差为 100%，超出按比例递减）
        target = result.get('data', {}).get('target_word_count', 0)
        actual = result.get('data', {}).get('word_count', 0)
        if target > 0:
            deviation = abs(actual - target) / target
            accuracy = max(0, 1 - max(0, deviation - 0.2) / 0.8)
        else:
            accuracy = 1.0
        
        feedback = ExecutionFeedback(
            execution_id=execution_id,
            timestamp=datetime.now().isoformat(),
            topic=params.get('topic', ''),
            target_word_count=target,
            actual_word_count=actual,
            word_count_accuracy=round(accuracy, 2),
            success=result.get('success', False),
            error_message=result.get('error'),
            user_rating=None,  # 初始为空，等待用户反馈
            user_feedback=None,
            execution_time_ms=execution_time_ms,
            style=params.get('style', 'professional'),
            keywords_count=len(params.get('keywords', '').split(',')) if params.get('keywords') else 0
        )
        
        # 追加写入 JSONL 文件
        with open(self.feedback_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(feedback), ensure_ascii=False) + '\n')
        
        return execution_id
    
    def add_user_feedback(self, execution_id: str, rating: int, feedback_text: str = None):
        """添加用户反馈"""
        if not self.feedback_file.exists():
            return False
        
        # 读取所有记录
        records = []
        updated = False
        
        with open(self.feedback_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    if record['execution_id'] == execution_id:
                        record['user_rating'] = rating
                        record['user_feedback'] = feedback_text
                        updated = True
                    records.append(record)
        
        # 写回文件
        if updated:
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                for record in records:
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        return updated
    
    def get_recent_feedback(self, limit: int = 100) -> List[Dict]:
        """获取最近的反馈记录"""
        if not self.feedback_file.exists():
            return []
        
        records = []
        with open(self.feedback_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        
        return records[-limit:]


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self, feedback_collector: FeedbackCollector):
        self.feedback_collector = feedback_collector
    
    def analyze(self) -> PerformanceMetrics:
        """分析性能指标"""
        records = self.feedback_collector.get_recent_feedback(limit=1000)
        
        if not records:
            return PerformanceMetrics(
                total_executions=0,
                success_rate=0.0,
                avg_word_count_accuracy=0.0,
                avg_execution_time_ms=0,
                user_satisfaction=0.0,
                common_errors=[],
                improvement_suggestions=[]
            )
        
        total = len(records)
        successful = sum(1 for r in records if r['success'])
        
        # 计算各项指标
        success_rate = successful / total if total > 0 else 0
        avg_accuracy = sum(r['word_count_accuracy'] for r in records) / total
        avg_time = sum(r['execution_time_ms'] for r in records) / total
        
        # 用户满意度（只计算有评分的）
        rated_records = [r for r in records if r.get('user_rating')]
        if rated_records:
            user_satisfaction = sum(r['user_rating'] for r in rated_records) / len(rated_records) / 5.0
        else:
            user_satisfaction = 0.0
        
        # 常见错误分析
        error_counts = {}
        for r in records:
            if not r['success'] and r.get('error_message'):
                error_type = self._classify_error(r['error_message'])
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        common_errors = [
            {"type": k, "count": v, "percentage": round(v/total*100, 1)}
            for k, v in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # 生成改进建议
        suggestions = self._generate_suggestions(
            success_rate, avg_accuracy, user_satisfaction, common_errors
        )
        
        return PerformanceMetrics(
            total_executions=total,
            success_rate=round(success_rate, 2),
            avg_word_count_accuracy=round(avg_accuracy, 2),
            avg_execution_time_ms=int(avg_time),
            user_satisfaction=round(user_satisfaction, 2),
            common_errors=common_errors,
            improvement_suggestions=suggestions
        )
    
    def _classify_error(self, error_message: str) -> str:
        """对错误进行分类"""
        error_lower = error_message.lower()
        
        if 'timeout' in error_lower or 'time' in error_lower:
            return "执行超时"
        elif 'memory' in error_lower or '内存' in error_lower:
            return "内存不足"
        elif 'file' in error_lower or '文件' in error_lower or 'permission' in error_lower:
            return "文件操作错误"
        elif 'parameter' in error_lower or '参数' in error_lower:
            return "参数错误"
        elif 'topic' in error_lower or '主题' in error_lower:
            return "主题处理错误"
        else:
            return "其他错误"
    
    def _generate_suggestions(self, success_rate: float, accuracy: float, 
                             satisfaction: float, errors: List[Dict]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if success_rate < 0.95:
            suggestions.append(f"成功率偏低 ({success_rate:.1%})，建议检查错误日志并修复常见问题")
        
        if accuracy < 0.85:
            suggestions.append(f"字数控制精度不足 ({accuracy:.1%})，建议优化字数计算和扩展算法")
        
        if satisfaction > 0 and satisfaction < 0.7:
            suggestions.append(f"用户满意度较低 ({satisfaction:.1%})，建议改进内容质量和人性化处理")
        
        if errors:
            top_error = errors[0]
            if top_error['percentage'] > 10:
                suggestions.append(f"'{top_error['type']}' 占比较高 ({top_error['percentage']}%)，建议针对性优化")
        
        if not suggestions:
            suggestions.append("当前性能良好，继续保持并收集更多用户反馈")
        
        return suggestions


class StrategyOptimizer:
    """策略优化器 - 基于反馈数据优化写作策略"""
    
    def __init__(self, feedback_collector: FeedbackCollector):
        self.feedback_collector = feedback_collector
        self.skill_dir = Path(__file__).parent.parent
        self.strategy_file = self.skill_dir / ".feedback" / "writing_strategies.json"
    
    def get_optimized_params(self, base_params: Dict) -> Dict:
        """根据历史数据优化参数"""
        records = self.feedback_collector.get_recent_feedback(limit=500)
        
        if len(records) < 10:
            # 数据不足，返回原参数
            return base_params
        
        optimized = base_params.copy()
        topic = base_params.get('topic', '')
        target_style = base_params.get('style', 'professional')
        
        # 1. 根据历史数据优化字数缓冲因子
        style_records = [r for r in records if r['style'] == target_style]
        if style_records:
            avg_accuracy = sum(r['word_count_accuracy'] for r in style_records) / len(style_records)
            if avg_accuracy < 0.8:
                # 字数控制不好，调整缓冲因子
                optimized['_buffer_factor'] = 0.85  # 更保守的估计
            elif avg_accuracy > 0.95:
                optimized['_buffer_factor'] = 0.95  # 可以更激进
        
        # 2. 根据主题相似度推荐风格
        similar_topics = self._find_similar_topics(topic, records)
        if similar_topics:
            best_style = self._get_best_style_for_topics(similar_topics)
            if best_style and base_params.get('style') != best_style:
                optimized['_suggested_style'] = best_style
        
        # 3. 根据用户评分优化人性化处理
        humanized_records = [r for r in records if r.get('user_rating')]
        if humanized_records:
            avg_rating = sum(r['user_rating'] for r in humanized_records) / len(humanized_records)
            if avg_rating >= 4:
                optimized['humanize'] = 'true'  # 高分保持人性化
            elif avg_rating <= 2:
                optimized['humanize'] = 'false'  # 低分尝试关闭
        
        return optimized
    
    def _find_similar_topics(self, topic: str, records: List[Dict]) -> List[Dict]:
        """找到相似主题的历史记录"""
        topic_keywords = set(topic.lower().split())
        similar = []
        
        for r in records:
            record_keywords = set(r.get('topic', '').lower().split())
            # 计算 Jaccard 相似度
            intersection = topic_keywords & record_keywords
            union = topic_keywords | record_keywords
            if union and len(intersection) / len(union) > 0.3:
                similar.append(r)
        
        return similar
    
    def _get_best_style_for_topics(self, records: List[Dict]) -> Optional[str]:
        """获取对相似主题效果最好的风格"""
        style_ratings = {}
        
        for r in records:
            if r.get('user_rating'):
                style = r.get('style', 'professional')
                if style not in style_ratings:
                    style_ratings[style] = []
                style_ratings[style].append(r['user_rating'])
        
        if not style_ratings:
            return None
        
        # 计算平均评分
        avg_ratings = {
            style: sum(ratings) / len(ratings)
            for style, ratings in style_ratings.items()
        }
        
        # 返回评分最高的风格
        return max(avg_ratings.items(), key=lambda x: x[1])[0]
    
    def save_strategy_snapshot(self, metrics: PerformanceMetrics):
        """保存策略快照"""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'metrics': asdict(metrics),
            'version': '1.0.0'
        }
        
        snapshots = []
        if self.strategy_file.exists():
            with open(self.strategy_file, 'r', encoding='utf-8') as f:
                snapshots = json.load(f)
        
        snapshots.append(snapshot)
        
        # 只保留最近 100 个快照
        snapshots = snapshots[-100:]
        
        with open(self.strategy_file, 'w', encoding='utf-8') as f:
            json.dump(snapshots, f, ensure_ascii=False, indent=2)
    
    def get_strategy_history(self) -> List[Dict]:
        """获取策略历史"""
        if not self.strategy_file.exists():
            return []
        
        with open(self.strategy_file, 'r', encoding='utf-8') as f:
            return json.load(f)


class SelfImprovementManager:
    """自我改进管理器 - 整合所有组件"""
    
    def __init__(self):
        self.feedback_collector = FeedbackCollector()
        self.analyzer = PerformanceAnalyzer(self.feedback_collector)
        self.optimizer = StrategyOptimizer(self.feedback_collector)
    
    def record_and_analyze(self, params: Dict, result: Dict, execution_time_ms: int) -> Dict:
        """记录执行并返回分析结果"""
        # 1. 记录执行
        execution_id = self.feedback_collector.record_execution(
            params, result, execution_time_ms
        )
        
        # 2. 分析性能
        metrics = self.analyzer.analyze()
        
        # 3. 获取优化建议
        optimized_params = self.optimizer.get_optimized_params(params)
        
        # 4. 保存策略快照
        self.optimizer.save_strategy_snapshot(metrics)
        
        return {
            'execution_id': execution_id,
            'metrics': asdict(metrics),
            'optimized_params': optimized_params,
            'suggestions': metrics.improvement_suggestions
        }
    
    def get_improvement_report(self) -> Dict:
        """获取改进报告"""
        metrics = self.analyzer.analyze()
        history = self.optimizer.get_strategy_history()
        
        # 计算趋势
        trend = self._calculate_trend(history)
        
        return {
            'current_metrics': asdict(metrics),
            'trend': trend,
            'total_snapshots': len(history),
            'recommendations': self._generate_recommendations(metrics, trend)
        }
    
    def _calculate_trend(self, history: List[Dict]) -> Dict:
        """计算性能趋势"""
        if len(history) < 2:
            return {'status': 'insufficient_data'}
        
        recent = history[-10:]  # 最近 10 次
        older = history[:10] if len(history) >= 20 else history[:len(history)//2]
        
        recent_success = sum(s['metrics']['success_rate'] for s in recent) / len(recent)
        older_success = sum(s['metrics']['success_rate'] for s in older) / len(older)
        
        recent_accuracy = sum(s['metrics']['avg_word_count_accuracy'] for s in recent) / len(recent)
        older_accuracy = sum(s['metrics']['avg_word_count_accuracy'] for s in older) / len(older)
        
        return {
            'success_rate_change': round(recent_success - older_success, 2),
            'accuracy_change': round(recent_accuracy - older_accuracy, 2),
            'status': 'improving' if recent_success > older_success else 'stable' if recent_success == older_success else 'declining'
        }
    
    def _generate_recommendations(self, metrics: PerformanceMetrics, trend: Dict) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if trend.get('status') == 'declining':
            recommendations.append("⚠️ 性能呈下降趋势，建议立即检查最近的变更")
        
        if metrics.total_executions < 50:
            recommendations.append("📊 执行次数较少，建议增加使用频率以收集更多数据")
        
        if metrics.user_satisfaction == 0:
            recommendations.append("💡 尚未收到用户评分，建议主动收集用户反馈")
        
        recommendations.extend(metrics.improvement_suggestions)
        
        return recommendations


# 全局实例
_improvement_manager = None

def get_improvement_manager() -> SelfImprovementManager:
    """获取全局自我改进管理器实例"""
    global _improvement_manager
    if _improvement_manager is None:
        _improvement_manager = SelfImprovementManager()
    return _improvement_manager


if __name__ == '__main__':
    # 测试代码
    manager = get_improvement_manager()
    
    # 模拟一些测试数据
    test_params = {
        'topic': '测试主题',
        'word_count': 2000,
        'style': 'professional'
    }
    
    test_result = {
        'success': True,
        'data': {
            'target_word_count': 2000,
            'word_count': 2100
        }
    }
    
    result = manager.record_and_analyze(test_params, test_result, 1500)
    print("记录结果:", json.dumps(result, ensure_ascii=False, indent=2))
    
    report = manager.get_improvement_report()
    print("\n改进报告:", json.dumps(report, ensure_ascii=False, indent=2))
