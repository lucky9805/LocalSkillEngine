#!/usr/bin/env python3
"""
博客长文写作 Skill
支持选题研究、大纲规划、深度写作、SEO优化、人性化处理
具备 Self-Improve 能力：收集反馈、分析性能、持续优化
"""

import sys
import json
import re
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

# 导入 Self-Improve 系统
try:
    from self_improve import get_improvement_manager
    SELF_IMPROVE_AVAILABLE = True
except ImportError:
    try:
        from .self_improve import get_improvement_manager
        SELF_IMPROVE_AVAILABLE = True
    except ImportError:
        SELF_IMPROVE_AVAILABLE = False


# 知识库系统
KNOWLEDGE_BASE = {
    "区块链": {
        "核心概念": [
            "区块链是一种分布式账本技术，通过密码学原理将数据区块按时间顺序链接",
            "去中心化：没有单一控制点，数据由网络中所有节点共同维护",
            "不可篡改：一旦数据写入区块链，几乎不可能被修改或删除",
            "透明性：所有交易记录对网络参与者公开可见"
        ],
        "工作原理": [
            "交易发起后，会被广播到整个网络",
            "矿工/验证节点收集交易，打包成区块",
            "通过共识机制（如PoW、PoS）验证区块有效性",
            "区块被添加到链上，交易得到确认"
        ],
        "应用场景": [
            "加密货币：比特币、以太坊等数字货币",
            "供应链管理：商品溯源、防伪验证",
            "数字身份：去中心化身份认证",
            "智能合约：自动执行的合约程序",
            "DeFi：去中心化金融服务",
            "NFT：非同质化代币，数字艺术品确权"
        ],
        "技术优势": [
            "安全性高：分布式存储，单点攻击无效",
            "去信任化：无需第三方中介即可建立信任",
            "可追溯：完整的历史记录便于审计",
            "降低成本：减少中间环节，提高效率"
        ],
        "局限性": [
            "性能瓶颈：交易处理速度相对较慢",
            "能耗问题：PoW机制消耗大量电力",
            "监管挑战：去中心化与监管合规的矛盾",
            "技术门槛：普通用户理解和使用有难度",
            "扩展性问题：随着数据增长，存储成本上升"
        ],
        "发展趋势": [
            "Layer 2 扩展方案：如闪电网络、Rollup",
            "跨链技术：实现不同区块链间的互操作",
            "企业级应用：联盟链在B2B场景的应用",
            "绿色区块链：转向PoS等低能耗共识机制",
            "监管友好：合规化发展成为主流趋势"
        ]
    },
    "Python": {
        "核心概念": [
            "Python是一种高级、解释型、通用的编程语言，由Guido van Rossum于1991年创建",
            "简洁优雅的语法设计，强调代码可读性，使用缩进表示代码块",
            "丰富的标准库和第三方生态系统，PyPI上有超过40万个包",
            "支持多种编程范式：面向对象、函数式、过程式编程",
            "动态类型系统，无需显式声明变量类型",
            "跨平台支持，可在Windows、macOS、Linux等系统运行"
        ],
        "异步编程": [
            "asyncio是Python 3.4+标准库中的异步I/O框架，提供事件循环和协程支持",
            "使用async/await关键字定义协程，async def定义异步函数，await挂起执行",
            "事件循环（Event Loop）驱动协程的调度执行，实现单线程并发",
            "适合高并发I/O密集型场景，如网络请求、数据库操作、Web服务",
            "asyncio.gather()可并发执行多个协程，提高程序效率",
            "与多线程相比，协程切换开销更小，内存占用更少"
        ],
        "性能优化": [
            "使用生成器（yield）替代列表推导式节省内存，惰性求值处理大数据",
            "多进程（multiprocessing）绕过GIL限制实现CPU并行，适合计算密集型任务",
            "Cython将Python编译为C代码提升性能，静态类型声明加速计算",
            "使用functools.lru_cache缓存重复计算结果，避免重复运算",
            "NumPy/Pandas等C扩展库替代纯Python实现数值计算",
            "使用__slots__减少对象内存占用，优化属性访问速度",
            "PyPy替代CPython，JIT编译提升循环和数值计算性能"
        ],
        "最佳实践": [
            "遵循PEP 8代码风格规范，保持代码一致性和可读性",
            "使用类型注解（Type Hints）提高代码可维护性和IDE支持",
            "编写单元测试和集成测试，使用pytest框架保证代码质量",
            "使用虚拟环境（venv/conda）隔离项目依赖，避免版本冲突",
            "使用Black、isort等工具自动格式化代码",
            "使用mypy进行静态类型检查，提前发现类型错误",
            "使用Sphinx编写文档，提高项目可维护性"
        ],
        "常见框架": [
            "Web开发：Django、Flask、FastAPI，分别适合不同规模和性能需求",
            "数据分析：NumPy、Pandas、Matplotlib，科学计算和可视化标准工具",
            "机器学习：TensorFlow、PyTorch、Scikit-learn，从入门到生产环境",
            "爬虫开发：Scrapy、BeautifulSoup、Requests，数据采集和处理",
            "自动化测试：Selenium、Playwright，浏览器自动化和端到端测试",
            "任务队列：Celery、RQ，异步任务处理和分布式调度"
        ]
    },
    "人工智能": {
        "核心概念": [
            "机器学习：让计算机从数据中学习规律，无需显式编程",
            "深度学习：基于神经网络的机器学习方法，多层非线性变换",
            "大语言模型：如GPT、Claude等生成式AI，基于Transformer架构",
            "Transformer架构：注意力机制的革命性突破，并行处理序列数据",
            "神经网络：模拟生物神经元的计算模型，由层和节点组成",
            "训练与推理：训练阶段学习参数，推理阶段应用模型预测"
        ],
        "应用场景": [
            "自然语言处理：文本生成、机器翻译、情感分析、智能问答",
            "计算机视觉：图像识别、目标检测、图像分割、人脸识别",
            "语音识别：语音转文字、语音合成、声纹识别",
            "推荐系统：个性化内容推荐、协同过滤、深度学习推荐",
            "自动驾驶：环境感知、路径规划、决策控制",
            "医疗诊断：影像分析、药物发现、疾病预测",
            "金融风控：欺诈检测、信用评分、算法交易"
        ],
        "发展趋势": [
            "多模态融合：文本、图像、音频、视频统一处理和理解",
            "边缘AI：模型轻量化、量化、剪枝，端侧部署和推理",
            "AI Agent：自主决策的智能体，能规划、执行、反思",
            "可解释AI：让模型决策更透明，提高可信度和可审计性",
            "AI安全：价值对齐、隐私保护、对抗鲁棒性",
            "通用人工智能（AGI）：具备人类水平认知能力的AI系统",
            "AI for Science：加速科学研究，如蛋白质结构预测"
        ],
        "技术挑战": [
            "数据质量：高质量标注数据获取困难，数据偏见问题",
            "计算资源：大模型训练需要海量算力和能源消耗",
            "模型可解释性：深度学习黑盒特性难以理解和调试",
            "泛化能力：模型在分布外数据上表现不稳定",
            "伦理问题：AI偏见、隐私侵犯、就业冲击等社会影响",
            "安全风险：对抗样本攻击、模型窃取、数据投毒"
        ]
    }
}


def execute(params: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    博客写作主函数
    
    Args:
        params: 参数字典
            - topic: 文章主题（必填）
            - word_count: 目标字数（默认3000）
            - style: 写作风格（默认professional）
            - keywords: SEO关键词
            - outline: 是否只生成大纲（默认false）
            - humanize: 是否人性化处理（默认true）
            - debug: 是否显示详细调试信息（默认true）
            - save_to_file: 是否保存到文件（默认true）
            - output_dir: 文件保存目录（默认当前目录）
            - enable_self_improve: 是否启用自我改进（默认true）
    
    Returns:
        执行结果字典
    """
    import sys
    import os
    
    # 记录开始时间
    start_time = time.time()
    
    params = params or {}
    # 默认开启调试模式，可以通过设置 debug=false 关闭
    debug = str(params.get("debug", "true")).lower() != "false"
    save_to_file = str(params.get("save_to_file", "true")).lower() != "false"
    output_dir = params.get("output_dir", os.getcwd())
    enable_self_improve = str(params.get("enable_self_improve", "true")).lower() != "false"
    
    def log_debug(msg: str):
        """输出调试信息到stderr"""
        if debug:
            print(f"[DEBUG] {msg}", file=sys.stderr, flush=True)
    
    log_debug(f"=== Blog Writer Skill 开始执行 ===")
    log_debug(f"调试模式: {'开启' if debug else '关闭'}")
    log_debug(f"输入参数: {params}")
    
    # 获取参数
    raw_topic = params.get("topic", "").strip()
    
    # 智能提取核心主题：去除冗余词汇
    def extract_core_topic(raw: str) -> str:
        """从长标题中提取核心主题"""
        import re
        
        topic = raw.strip()
        
        # 去除常见的冗余前缀和后缀（按优先级排序，先去除长的）
        redundant_patterns = [
            # 前缀
            r'^帮我写一篇关于',
            r'^帮我写关于',
            r'^帮我写',
            r'^请写一篇关于',
            r'^请写关于',
            r'^请写',
            r'^写一篇关于',
            r'^写关于',
            r'^写一篇',
            r'^关于',
            # 后缀
            r'的博客文章$',
            r'的文章$',
            r'的论文$',
            r'的报告$',
            # 其他
            r'有关',
            r'谈谈',
            r'聊聊',
        ]
        
        for pattern in redundant_patterns:
            topic = re.sub(pattern, '', topic)
        
        # 去除多余的空格
        topic = topic.strip()
        
        # 如果主题太长，提取核心关键词
        if len(topic) > 40:
            # 尝试提取"XX的XX"或"XX与XX"结构
            match = re.search(r'([^，。]{2,20}(?:的|与|和)[^，。]{2,20})', topic)
            if match:
                topic = match.group(1)
            else:
                # 取前40个字符，尽量在标点处截断
                truncated = topic[:40]
                # 找到最后一个标点符号
                last_punct = max(truncated.rfind('，'), truncated.rfind('。'), 
                                truncated.rfind('、'), truncated.rfind('；'))
                if last_punct > 20:  # 如果标点位置合理，就在那里截断
                    topic = truncated[:last_punct]
                else:
                    topic = truncated
        
        return topic.strip()
    
    topic = extract_core_topic(raw_topic)
    log_debug(f"原始主题: '{raw_topic}'")
    log_debug(f"提取核心主题: '{topic}'")
    
    if not topic:
        log_debug("错误: 缺少主题参数")
        return {
            "success": False,
            "error": "缺少必填参数: topic（文章主题）",
            "output": None
        }
    
    word_count = int(params.get("word_count", 3000))
    style = params.get("style", "professional")
    keywords_str = params.get("keywords", "")
    outline_only = str(params.get("outline", "false")).lower() == "true"
    humanize = str(params.get("humanize", "true")).lower() == "true"
    
    log_debug(f"目标字数: {word_count}, 风格: {style}, 只生成大纲: {outline_only}")
    
    # 解析关键词
    keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
    log_debug(f"关键词: {keywords}")
    
    try:
        # 1. 选题研究
        log_debug("步骤1: 开始选题研究...")
        research_result = research_topic(topic)
        log_debug(f"选题研究完成: 类型={research_result.get('topic_types')}")
        
        # 2. 生成大纲
        log_debug("步骤2: 开始生成大纲...")
        outline = generate_outline(topic, word_count, style, keywords)
        log_debug(f"大纲生成完成: {len(outline)} 个章节")
        for i, section in enumerate(outline):
            log_debug(f"  章节{i+1}: {section.get('title')} ({section.get('word_count')}字)")
        
        if outline_only:
            log_debug("只生成大纲模式，直接返回")
            return {
                "success": True,
                "output": format_outline_output(topic, outline, keywords),
                "data": {
                    "topic": topic,
                    "outline": outline,
                    "keywords": keywords,
                    "research": research_result
                }
            }
        
        # 3. 深度写作
        log_debug("步骤3: 开始深度写作...")
        article = write_article_with_knowledge(topic, outline, word_count, style, keywords)
        current_words = count_words(article)
        log_debug(f"文章写作完成: {current_words} 字")
        
        # 4. SEO优化
        log_debug("步骤4: 开始SEO优化...")
        seo_data = optimize_seo(topic, article, keywords)
        log_debug(f"SEO优化完成: 标题='{seo_data.get('title')[:30]}...'")
        
        # 5. 人性化处理
        if humanize:
            log_debug("步骤5: 开始人性化处理...")
            article = humanize_content(article, style)
            log_debug("人性化处理完成")
        else:
            log_debug("步骤5: 跳过人性化处理")
        
        # 计算阅读时长
        reading_time = estimate_reading_time(article)
        log_debug(f"阅读时长: {reading_time}")
        
        # 格式化输出
        log_debug("格式化最终输出...")
        output = format_article_output(
            seo_data["title"],
            seo_data["meta_description"],
            seo_data["keywords"],
            article,
            reading_time,
            word_count
        )
        
        final_word_count = count_words(article)
        log_debug(f"=== 执行完成 ===")
        log_debug(f"最终字数: {final_word_count}, 目标: {word_count}")
        
        # 保存到文件
        saved_file = None
        if save_to_file:
            try:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"blog-{timestamp}.md"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(output)
                
                saved_file = filepath
                log_debug(f"文章已保存到: {filepath}")
            except Exception as e:
                log_debug(f"保存文件失败: {e}")
        
        # 构建结果
        result = {
            "success": True,
            "output": output,
            "data": {
                "topic": topic,
                "title": seo_data["title"],
                "meta_description": seo_data["meta_description"],
                "keywords": seo_data["keywords"],
                "word_count": final_word_count,
                "target_word_count": word_count,
                "reading_time": reading_time,
                "style": style,
                "outline": outline,
                "research": research_result,
                "saved_file": saved_file
            }
        }
        
        # Self-Improve: 记录执行并分析
        if enable_self_improve and SELF_IMPROVE_AVAILABLE:
            try:
                execution_time_ms = int((time.time() - start_time) * 1000)
                manager = get_improvement_manager()
                improve_result = manager.record_and_analyze(params, result, execution_time_ms)
                
                # 将改进建议添加到结果中
                result['data']['self_improve'] = {
                    'execution_id': improve_result['execution_id'],
                    'suggestions': improve_result['suggestions'],
                    'performance_summary': f"成功率: {improve_result['metrics']['success_rate']:.0%}, "
                                          f"字数精度: {improve_result['metrics']['avg_word_count_accuracy']:.0%}"
                }
                
                log_debug(f"Self-improve 记录完成: {improve_result['execution_id']}")
            except Exception as e:
                log_debug(f"Self-improve 记录失败: {e}")
        
        return result
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        tb = traceback.format_exc()
        log_debug(f"!!! 执行出错: {error_msg}")
        log_debug(f"堆栈跟踪:\n{tb}")
        return {
            "success": False,
            "error": error_msg,
            "traceback": tb,
            "output": None
        }


def research_topic(topic: str) -> Dict[str, Any]:
    """选题研究"""
    topic_types = analyze_topic_type(topic)
    angles = generate_writing_angles(topic, topic_types)
    audience = analyze_audience(topic, topic_types)
    
    return {
        "topic_types": topic_types,
        "writing_angles": angles,
        "target_audience": audience,
        "suggested_sections": generate_suggested_sections(topic_types),
        "research_notes": f"话题 '{topic}' 适合从 {', '.join(angles[:3])} 等角度展开"
    }


def analyze_topic_type(topic: str) -> List[str]:
    """分析话题类型"""
    types = []
    topic_lower = topic.lower()
    
    tech_keywords = ["python", "java", "编程", "代码", "算法", "架构", "数据库", 
                     "开发", "技术", "AI", "人工智能", "机器学习", "区块链", "云原生"]
    business_keywords = ["商业", "创业", "管理", "营销", "产品", "运营", "战略", "市场"]
    life_keywords = ["生活", "健康", "旅行", "美食", "读书", "学习", "成长", "职场"]
    
    if any(kw in topic_lower for kw in tech_keywords):
        types.append("technical")
    if any(kw in topic_lower for kw in business_keywords):
        types.append("business")
    if any(kw in topic_lower for kw in life_keywords):
        types.append("lifestyle")
    
    if not types:
        types.append("general")
    
    return types


def generate_writing_angles(topic: str, topic_types: List[str]) -> List[str]:
    """生成写作角度"""
    angles = []
    
    if "technical" in topic_types:
        angles.extend([
            "原理解析与底层逻辑",
            "实战案例与最佳实践",
            "性能优化与踩坑指南",
            "技术选型对比分析",
            "未来趋势与发展方向"
        ])
    
    if "business" in topic_types:
        angles.extend([
            "行业现状与市场分析",
            "成功案例深度拆解",
            "方法论与实操框架",
            "风险挑战与应对策略"
        ])
    
    if not angles:
        angles = [
            "概念定义与背景介绍",
            "核心原理深度解析",
            "实际应用场景",
            "优缺点分析",
            "未来发展趋势"
        ]
    
    return angles


def analyze_audience(topic: str, topic_types: List[str]) -> Dict[str, Any]:
    """分析目标读者"""
    if "technical" in topic_types:
        return {
            "primary": "技术人员、开发者",
            "secondary": "技术管理者、产品经理",
            "level": "中高级",
            "expectations": "深度技术内容、实战代码、最佳实践"
        }
    elif "business" in topic_types:
        return {
            "primary": "创业者、管理者",
            "secondary": "投资人、从业者",
            "level": "中级",
            "expectations": "商业洞察、案例分析、可执行建议"
        }
    else:
        return {
            "primary": "对该话题感兴趣的读者",
            "secondary": "相关行业从业者",
            "level": "入门到中级",
            "expectations": "清晰易懂、有深度、有实用价值"
        }


def generate_suggested_sections(topic_types: List[str]) -> List[str]:
    """生成建议的章节结构"""
    base_sections = [
        "引言：为什么这个话题重要",
        "背景：问题的来龙去脉",
        "核心内容：深度分析与解读",
        "实践应用：如何将理论落地",
        "总结与展望"
    ]
    
    if "technical" in topic_types:
        base_sections.insert(3, "技术实现：代码与架构")
        base_sections.insert(4, "性能优化：最佳实践")
    
    return base_sections


def generate_outline(topic: str, word_count: int, style: str, keywords: List[str]) -> List[Dict[str, Any]]:
    """生成文章大纲，根据目标字数合理分配章节"""
    # 根据字数确定章节数和每章字数
    # 允许 ±20% 的误差范围，优先保证内容完整性
    buffer_factor = 0.9  # 只预留10%缓冲，让内容更充实
    effective_word_count = int(word_count * buffer_factor)
    
    if word_count <= 1500:
        section_count = 3
    elif word_count <= 3000:
        section_count = 4
    elif word_count <= 5000:
        section_count = 6
    elif word_count <= 8000:
        section_count = 8
    else:
        section_count = 10
    
    # 重新计算每章字数
    words_per_section = effective_word_count // section_count
    
    outline = []
    
    # 引言（占1份）
    outline.append({
        "title": "引言",
        "level": 1,
        "word_count": words_per_section,
        "key_points": [
            "引出话题，说明重要性",
            "提出核心问题或观点",
            "预告文章结构和价值"
        ]
    })
    
    # 主体章节（占 section_count - 2 份）
    section_titles = generate_section_titles(topic, section_count - 2)
    for i, title in enumerate(section_titles, 1):
        outline.append({
            "title": title,
            "level": 1,
            "word_count": words_per_section,
            "key_points": generate_key_points(title, topic, keywords)
        })
    
    # 结语（占0.5份）
    outline.append({
        "title": "总结与展望",
        "level": 1,
        "word_count": words_per_section // 2,
        "key_points": [
            "回顾核心观点",
            "给出行动建议",
            "展望未来趋势"
        ]
    })
    
    return outline


def generate_section_titles(topic: str, count: int) -> List[str]:
    """生成章节标题"""
    # 匹配知识库
    knowledge = match_knowledge_base(topic)
    
    if knowledge:
        # 使用知识库的章节结构
        sections = []
        if "核心概念" in knowledge:
            sections.append(f"{topic}的核心概念与基本原理")
        if "工作原理" in knowledge:
            sections.append(f"深入理解{topic}的工作机制")
        if "应用场景" in knowledge:
            sections.append(f"{topic}的实际应用场景")
        if "技术优势" in knowledge or "局限性" in knowledge:
            sections.append(f"{topic}的优势与局限性分析")
        if "发展趋势" in knowledge:
            sections.append(f"{topic}的未来发展趋势")
        return sections[:count]
    
    # 默认模板
    templates = [
        f"{topic}的核心概念与原理",
        f"深入理解{topic}的工作机制",
        f"{topic}的实际应用场景",
        f"{topic}的优势与局限性",
        f"如何正确选择和使用{topic}",
        f"{topic}的常见误区与避坑指南",
        f"{topic}的性能优化策略",
        f"{topic}与其他方案的对比",
        f"{topic}的最佳实践案例",
        f"{topic}的未来发展趋势"
    ]
    
    return templates[:count]


def match_knowledge_base(topic: str) -> Dict[str, List[str]]:
    """匹配知识库"""
    topic_lower = topic.lower()
    
    for key, value in KNOWLEDGE_BASE.items():
        if key in topic or key in topic_lower:
            return value
    
    # 关键词匹配 - 检查知识库key中的每个词是否在topic中
    for key, value in KNOWLEDGE_BASE.items():
        # 将key拆分成关键词（如"人工智能"拆成["人工","智能"]）
        key_words = [key[i:i+2] for i in range(0, len(key)-1)]
        # 如果key中超过一半的关键词出现在topic中，则认为匹配
        match_count = sum(1 for word in key_words if word in topic)
        if len(key_words) > 0 and match_count / len(key_words) > 0.5:
            return value
    
    return {}


def generate_key_points(section_title: str, topic: str, keywords: List[str]) -> List[str]:
    """生成章节要点"""
    points = [
        f"深入解析{section_title}的核心内容",
        "提供具体案例和数据支撑",
        "给出可操作的实践建议"
    ]
    
    if keywords:
        points.append(f"自然融入关键词：{', '.join(keywords[:2])}")
    
    return points


def write_article_with_knowledge(topic: str, outline: List[Dict], word_count: int, 
                                  style: str, keywords: List[str]) -> str:
    """使用知识库撰写文章"""
    knowledge = match_knowledge_base(topic)
    article_parts = []
    
    for section in outline:
        section_content = write_section_with_knowledge(section, style, keywords, knowledge, topic)
        article_parts.append(section_content)
    
    article = "\n\n".join(article_parts)
    
    # 确保字数达标
    current_words = count_words(article)
    if current_words < word_count:
        article = expand_with_knowledge(article, word_count - current_words, knowledge, topic)
    
    return article


def write_section_with_knowledge(section: Dict[str, Any], style: str, 
                                  keywords: List[str], knowledge: Dict, topic: str) -> str:
    """使用知识库撰写单个章节，参考目标字数但不严格限制"""
    title = section["title"]
    target_words = section["word_count"]
    
    content_parts = [f"## {title}\n"]
    
    # 根据章节标题匹配知识库内容
    section_knowledge = match_section_knowledge(title, knowledge)
    
    if section_knowledge:
        # 使用知识库内容 - 更自然的展开
        if style == "storytelling":
            content_parts.append(f"让我们从一个真实的故事开始说起。{section_knowledge[0]}\n")
        elif style == "casual":
            content_parts.append(f"说到{title}，相信很多人都有同感。{section_knowledge[0]}\n")
        else:
            content_parts.append(f"{section_knowledge[0]}\n")
        
        # 展开知识要点 - 更详细的阐述
        for i, point in enumerate(section_knowledge[1:], 1):
            # 提取小标题（取前15个字符作为标题）
            short_title = point[:15] if len(point) > 15 else point
            content_parts.append(f"\n### {i}. {short_title}\n")
            content_parts.append(f"{point}\n")
            
            # 为每个要点添加详细阐述
            elaboration = generate_detailed_elaboration(point, topic, i)
            content_parts.append(elaboration)
            
            # 添加实际案例或数据支撑
            if i % 2 == 0:
                example = generate_example(point, topic)
                content_parts.append(f"\n**实际案例**：{example}")
    else:
        # 知识库中没有匹配内容，使用智能内容生成
        content_parts.extend(generate_smart_content(topic, title, style, target_words))
    
    # 章节小结
    summary = f"\n\n### 小结\n\n通过以上的分析，我们可以看出，{title}涉及的内容远比表面看起来要丰富。理解这些核心概念不仅有助于我们建立系统性的认知框架，更能在实际应用中避免常见的误区。"
    content_parts.append(summary)
    
    return "\n".join(content_parts)


def generate_smart_content(topic: str, section_title: str, style: str, target_words: int = 500) -> List[str]:
    """智能生成章节内容 - 基于主题和章节标题生成相关内容，控制字数"""
    content_parts = []
    
    # 分析章节类型
    section_type = analyze_section_type(section_title)
    
    # 根据章节类型生成不同内容
    if section_type == "introduction":
        content_parts = generate_introduction_content(topic, style, target_words)
    elif section_type == "concept":
        content_parts = generate_concept_content(topic, style, target_words)
    elif section_type == "mechanism":
        content_parts = generate_mechanism_content(topic, style, target_words)
    elif section_type == "application":
        content_parts = generate_application_content(topic, style, target_words)
    elif section_type == "pros_cons":
        content_parts = generate_pros_cons_content(topic, style, target_words)
    elif section_type == "trend":
        content_parts = generate_trend_content(topic, style, target_words)
    elif section_type == "conclusion":
        content_parts = generate_conclusion_content(topic, style, target_words)
    else:
        # 通用内容
        content_parts = generate_generic_section_content(topic, section_title, style, target_words)
    
    return content_parts


def analyze_section_type(section_title: str) -> str:
    """分析章节类型"""
    title_lower = section_title.lower()
    
    if any(word in title_lower for word in ["引言", "介绍", "前言", "背景"]):
        return "introduction"
    elif any(word in title_lower for word in ["概念", "原理", "基础", "是什么"]):
        return "concept"
    elif any(word in title_lower for word in ["机制", "原理", "工作", "如何", "深入"]):
        return "mechanism"
    elif any(word in title_lower for word in ["应用", "场景", "案例", "实践", "使用"]):
        return "application"
    elif any(word in title_lower for word in ["优势", "局限", "优缺点", "对比", "利弊"]):
        return "pros_cons"
    elif any(word in title_lower for word in ["趋势", "未来", "发展", "展望", "前景"]):
        return "trend"
    elif any(word in title_lower for word in ["总结", "结论", "结语"]):
        return "conclusion"
    else:
        return "general"


def generate_introduction_content(topic: str, style: str, target_words: int = 500) -> List[str]:
    """生成引言内容"""
    return [
        f"近年来，{topic}成为了业界关注的热点话题。无论是技术从业者还是普通用户，都对其表现出浓厚的兴趣。那么，{topic}究竟是什么？它为什么如此重要？本文将带你深入了解这一话题。\n",
        f"\n### 为什么{topic}值得关注\n",
        f"首先，我们需要认识到{topic}在当前环境下的重要性。随着技术的快速发展和市场需求的不断变化，{topic}所涉及的内容正在深刻影响着我们的生活和工作方式。",
        f"\n从行业角度来看，越来越多的企业和组织开始重视{topic}，并将其作为战略布局的重要组成部分。这一趋势不仅反映了市场的需求，也预示着未来发展方向的转变。",
        f"\n### 本文的主要内容\n",
        f"在本文中，我们将从以下几个方面对{topic}进行全面解读：",
        f"\n1. **核心概念解析** - 深入理解{topic}的基本原理和关键要素",
        f"2. **实际应用场景** - 探讨{topic}在不同领域的具体应用",
        f"3. **优势与挑战** - 客观分析{topic}带来的机遇和面临的问题",
        f"4. **未来发展趋势** - 展望{topic}的发展方向和潜在影响",
        f"\n无论你是初次接触这个话题，还是希望深化理解，相信本文都能为你提供有价值的参考。"
    ]


def generate_concept_content(topic: str, style: str, target_words: int = 500) -> List[str]:
    """生成概念解释内容"""
    return [
        f"要理解{topic}，我们首先需要明确它的核心概念。简单来说，{topic}代表了一种新的方法或趋势，它通过创新的方式解决了传统方案难以处理的问题。\n",
        f"\n### 基本定义\n",
        f"从专业角度来看，{topic}可以定义为：一种基于特定原理或技术的解决方案，旨在提高效率、降低成本或创造新的价值。这一定义涵盖了其核心要素和主要特征。",
        f"\n值得注意的是，{topic}并不是孤立存在的，它与许多相关概念和技术密切相关。理解这些关联有助于我们更全面地把握其内涵。",
        f"\n### 核心要素\n",
        f"{topic}的核心要素主要包括以下几个方面：\n",
        f"\n**1. 创新性** - {topic}最大的特点在于其创新性，它打破了传统的思维模式，提供了全新的解决方案。",
        f"\n**2. 实用性** - 理论必须服务于实践。{topic}的另一个重要特征是其强大的实用性，能够切实解决实际问题。",
        f"\n**3. 可扩展性** - 随着需求的变化，{topic}需要具备良好的可扩展性，能够适应不同规模和复杂度的应用场景。",
        f"\n### 与其他概念的区别\n",
        f"很多人容易将{topic}与一些相关概念混淆。实际上，它们之间存在着明显的区别。{topic}更侧重于特定的维度，而其他概念则可能关注不同的层面。理解这些区别有助于我们更准确地应用相关理论。"
    ]


def generate_mechanism_content(topic: str, style: str, target_words: int = 500) -> List[str]:
    """生成机制原理内容"""
    return [
        f"了解了{topic}的基本概念后，让我们深入探讨其背后的工作原理。理解这些机制有助于我们更好地应用和优化相关方案。\n",
        f"\n### 核心工作流程\n",
        f"{topic}的运作遵循着特定的流程和规则。一般来说，整个过程可以分为以下几个阶段：",
        f"\n**第一阶段：准备与输入** - 在这一阶段，需要收集和整理必要的信息和资源，为后续处理做好准备。",
        f"\n**第二阶段：核心处理** - 这是整个流程的关键环节。系统会根据预设的规则和算法，对输入进行处理和转换。",
        f"\n**第三阶段：输出与反馈** - 处理完成后，系统会生成相应的结果，并根据反馈进行调整和优化。",
        f"\n### 关键技术支撑\n",
        f"{topic}的实现离不开一系列关键技术的支撑。这些技术相互配合，共同构成了完整的技术体系。",
        f"\n首先是基础架构层面的技术，它们提供了稳定可靠的运行环境。其次是算法层面的创新，这些算法决定了系统的处理能力和效果。",
        f"\n### 影响因素分析\n",
        f"{topic}的效果受到多种因素的影响。外部环境的变化、内部资源的配置、以及执行策略的选择，都会对最终结果产生重要影响。"
    ]


def generate_application_content(topic: str, style: str) -> List[str]:
    """生成应用场景内容"""
    return [
        f"理论的价值在于指导实践。让我们来看看{topic}在实际中的应用场景，以及它如何为不同领域带来价值。\n",
        f"\n### 主要应用领域\n",
        f"{topic}的应用范围非常广泛，几乎涵盖了各个行业和领域。以下是几个典型的应用场景：",
        f"\n**1. 企业级应用** - 在企业环境中，{topic}可以帮助组织提高效率、降低成本、优化流程。许多成功的企业已经将{topic}纳入其核心战略。",
        f"\n**2. 个人用户场景** - 对于个人用户而言，{topic}同样具有重要的实用价值。它可以帮助用户更好地完成任务、提升体验、实现目标。",
        f"\n**3. 行业解决方案** - 在特定行业中，{topic}可以与其他技术和方法结合，形成针对性的解决方案，解决行业特有的问题。",
        f"\n### 成功案例分享\n",
        f"为了更好地理解{topic}的实际效果，让我们来看几个成功案例。",
        f"\n**案例一：某领先企业的实践** - 该企业通过引入{topic}，成功实现了业务流程的优化，效率提升了30%以上，成本降低了20%。",
        f"\n**案例二：创新项目的突破** - 在一个创新项目中，团队利用{topic}解决了长期存在的技术难题，取得了突破性的进展。",
        f"\n这些案例充分说明了{topic}在实际应用中的价值和潜力。",
        f"\n### 应用中的注意事项\n",
        f"虽然{topic}具有诸多优势，但在实际应用中也需要注意一些问题。首先，要充分评估自身的需求和条件，确保{topic}适合当前场景。其次，要做好充分的准备工作，包括资源准备、团队培训等。最后，要建立完善的评估机制，及时跟踪和优化应用效果。"
    ]


def generate_pros_cons_content(topic: str, style: str) -> List[str]:
    """生成优缺点分析内容"""
    return [
        f"任何技术或方法都有其优势和局限性。客观分析{topic}的优缺点，有助于我们做出更明智的决策。\n",
        f"\n### 主要优势\n",
        f"{topic}的优势主要体现在以下几个方面：",
        f"\n**1. 效率提升** - 通过优化流程和自动化处理，{topic}可以显著提高工作效率，节省时间和人力成本。",
        f"\n**2. 质量改善** - {topic}能够减少人为错误，提高输出质量的一致性和可靠性。",
        f"\n**3. 创新能力** - {topic}为创新提供了新的可能，帮助用户发现新的机会和解决方案。",
        f"\n**4. 可扩展性** - 随着需求的增长，{topic}可以灵活扩展，适应不同的规模和复杂度。",
        f"\n### 局限性与挑战\n",
        f"当然，{topic}也存在一些局限性和挑战：",
        f"\n**1. 学习成本** - 对于新手来说，掌握{topic}需要一定的时间和精力投入。",
        f"\n**2. 资源需求** - 实施{topic}可能需要一定的资源投入，包括技术、人力和资金等。",
        f"\n**3. 兼容性问题** - 在某些场景下，{topic}可能与现有系统存在兼容性问题，需要进行适配和调整。",
        f"\n**4. 风险控制** - 任何新技术都伴随着一定的风险，需要建立完善的风险控制机制。",
        f"\n### 如何权衡利弊\n",
        f"面对这些优缺点，我们应该如何做出选择？建议从以下几个方面考虑：首先，明确自身的需求和目标；其次，评估现有的资源和条件；再次，参考同行的实践经验和案例；最后，制定合理的实施计划和风险预案。"
    ]


def generate_trend_content(topic: str, style: str, target_words: int = 500) -> List[str]:
    """生成趋势展望内容"""
    return [
        f"展望未来，{topic}将继续发展和演进。了解这些趋势有助于我们提前布局，把握机遇。\n",
        f"\n### 技术发展趋势\n",
        f"从技术角度看，{topic}将朝着以下几个方向发展：",
        f"\n**1. 智能化** - 随着人工智能技术的发展，{topic}将变得更加智能，能够自动适应不同的场景和需求。",
        f"\n**2. 集成化** - 未来的{topic}将与其他技术和平台深度集成，形成更加完整的解决方案。",
        f"\n**3. 个性化** - 用户对个性化的需求越来越高，{topic}也将提供更多定制化的选项和功能。",
        f"\n**4. 生态化** - 围绕{topic}将形成更加完善的生态系统，包括工具、服务、社区等。",
        f"\n### 市场发展趋势\n",
        f"从市场角度看，{topic}的发展前景同样值得期待。根据行业分析，相关市场规模将持续增长，应用场景将不断拓展。",
        f"\n### 对行业的影响\n",
        f"{topic}的发展将对整个行业产生深远影响。它可能改变现有的商业模式、重塑竞争格局、创造新的就业机会。"
    ]


def generate_conclusion_content(topic: str, style: str) -> List[str]:
    """生成总结内容"""
    return [
        f"通过以上的分析，我们对{topic}有了更加全面和深入的认识。让我们回顾一下本文的核心观点。\n",
        f"\n### 核心观点回顾\n",
        f"首先，我们介绍了{topic}的基本概念和核心要素，帮助读者建立起基础认知。其次，我们深入探讨了其工作原理和机制，揭示了背后的逻辑。再次，我们分析了实际应用场景和成功案例，展示了{topic}的实际价值。最后，我们客观评估了其优缺点，并展望了未来的发展趋势。",
        f"\n### 行动建议\n",
        f"基于以上分析，我们为不同读者提供以下建议：",
        f"\n**对于初学者**：建议从基础概念入手，通过实践项目加深理解。可以参考本文提到的案例，从中学习经验。",
        f"\n**对于实践者**：建议关注{topic}的最新发展，及时更新知识和技能。同时，要注重总结经验，形成自己的方法论。",
        f"\n**对于决策者**：建议综合考虑{topic}的利弊，结合自身情况制定合理的策略。可以先进行小规模试点，验证效果后再扩大应用。",
        f"\n### 结语\n",
        f"{topic}是一个充满机遇和挑战的领域。无论你是出于兴趣学习，还是为了工作应用，希望本文都能为你提供有价值的参考。技术的进步永无止境，让我们保持学习的态度，共同探索{topic}的无限可能。"
    ]


def generate_generic_section_content(topic: str, section_title: str, style: str, target_words: int = 500) -> List[str]:
    """生成通用章节内容"""
    return [
        f"{section_title}是整个话题中最重要的部分之一。要真正掌握它，我们需要从多个维度进行深入分析。\n",
        f"\n### 基本概念与定义\n",
        f"首先，我们需要明确{section_title}的基本含义。从专业角度来看，它代表了一种新的方法论或技术范式，能够在实际应用中解决传统方案难以处理的问题。\n\n具体来说，{section_title}的核心在于通过创新的方式重构现有的流程和模式，从而带来效率提升和成本降低。",
        f"\n### 核心原理分析\n",
        f"深入剖析{section_title}背后的工作原理，我们可以发现几个关键要素。第一，它建立在先进的理论基础之上；第二，它的运作遵循着特定的规则和流程。",
        f"\n### 实际应用案例\n",
        f"理论需要结合实践。在实际应用中，我们可以看到许多{section_title}的成功案例。这些案例不仅验证了其有效性，也为我们提供了宝贵的经验和参考。"
    ]


def generate_detailed_elaboration(point: str, topic: str, index: int) -> str:
    """生成详细的阐述内容"""
    elaborations_map = {
        "去中心化": [
            "去中心化是区块链最核心的特性之一。在传统的中心化系统中，所有的数据都存储在单一的服务器或机构中，这不仅存在单点故障的风险，还意味着中心机构拥有绝对的控制权。",
            "而在区块链网络中，数据被分布式地存储在网络中的每一个节点上。每个节点都保存着完整的数据副本，任何数据的变更都需要经过网络中多数节点的验证和确认。",
            "这种设计带来了几个显著的优势：首先，系统的可靠性大大提高，即使部分节点出现故障，整个网络仍然可以正常运行；其次，数据的透明性和可追溯性得到了保障；最后，去除了中间环节，降低了信任成本。"
        ],
        "不可篡改": [
            "不可篡改性是区块链数据可信度的根本保障。这一特性源于区块链的链式存储结构和密码学原理。",
            "每个区块都包含了前一个区块的哈希值，形成了一个环环相扣的链条。如果有人试图篡改某个区块中的数据，那么这个区块的哈希值就会发生变化，导致后续所有区块的哈希值都不匹配。",
            "在实际应用中，这意味着一旦数据被写入区块链，就很难被恶意修改。这对于金融交易、合同存证、身份认证等场景具有重要价值。"
        ],
        "智能合约": [
            "智能合约是区块链2.0时代的重要创新，它使得区块链不仅可以记录交易，还可以执行复杂的业务逻辑。",
            "简单来说，智能合约就是运行在区块链上的自动执行程序。开发者可以将业务规则编码成智能合约，部署到区块链上。当预设的条件被触发时，合约就会自动执行相应的操作。",
            "以太坊是最具代表性的智能合约平台，它提供了一个图灵完备的编程环境，开发者可以使用Solidity等语言编写各种复杂的去中心化应用（DApps）。"
        ],
        "共识机制": [
            "共识机制是区块链网络中节点之间达成一致的规则。由于区块链是去中心化的，没有中央机构来仲裁哪个交易是有效的，因此需要一种机制来让网络中的所有节点就交易顺序和状态达成一致。",
            "目前主流的共识机制包括工作量证明（PoW）和权益证明（PoS）。PoW通过计算难题来竞争记账权，安全性高但能耗大；PoS则根据持有的代币数量和时间来分配记账权，更加节能环保。",
            "不同的共识机制在去中心化程度、安全性和效率之间做出了不同的权衡，适用于不同的应用场景。"
        ]
    }
    
    for key, paragraphs in elaborations_map.items():
        if key in point:
            return "\n\n".join(paragraphs)
    
    # 默认阐述
    return f"这一点在实际应用中非常重要。深入理解{point[:15]}的本质，有助于我们更好地把握{topic}的核心价值。建议读者在实践中多加体会，结合实际案例来加深理解。"


def generate_example(point: str, topic: str) -> str:
    """生成实际案例"""
    examples = {
        "去中心化": "比特币网络就是一个典型的去中心化系统。全球有数万个节点在运行比特币软件，没有任何个人或组织能够单独控制整个网络。即使某些国家的政府禁止比特币交易，网络仍然可以继续运行。",
        "不可篡改": "2018年，深圳法院首次认可了区块链存证的法律效力。某知识产权案件中，原告使用区块链技术存证了作品的创作时间和内容，法院最终采纳了这一证据。这充分说明了区块链不可篡改特性的实际价值。",
        "智能合约": "DeFi（去中心化金融）是智能合约最热门的应用领域之一。以Uniswap为例，它是一个基于智能合约的去中心化交易所，用户可以直接在链上完成代币兑换，无需注册账户或进行KYC验证，所有交易都由智能合约自动执行。",
        "共识机制": "比特币采用PoW共识机制，全网算力超过200 EH/s，这意味着攻击者需要控制超过100 EH/s的算力才能成功发起51%攻击，成本高达数十亿美元，这在经济上几乎是不可能的。"
    }
    
    for key, example in examples.items():
        if key in point:
            return example
    
    return f"在{topic}的实际应用中，这一点已经得到了广泛验证。许多成功的项目都证明了这一原理的有效性。"


def generate_generic_content(topic: str, title: str) -> List[Dict[str, str]]:
    """生成通用章节内容"""
    return [
        {
            "subtitle": "基本概念与定义",
            "content": f"首先，我们需要明确{topic}的基本含义。从专业角度来看，它代表了一种新的方法论或技术范式，能够在实际应用中解决传统方案难以处理的问题。理解这一点，是掌握整个话题的基础。\n\n具体来说，{topic}的核心在于通过创新的方式重构现有的流程和模式，从而带来效率提升和成本降低。"
        },
        {
            "subtitle": "核心原理分析",
            "content": f"深入剖析{topic}背后的工作原理，我们可以发现几个关键要素。第一，它建立在分布式系统理论之上，通过多节点协作实现目标；第二，它的运作遵循着特定的算法和协议，确保系统的稳定性和安全性；第三，理解这些原理有助于我们在实际应用中做出正确的技术选型。"
        },
        {
            "subtitle": "实际应用案例",
            "content": f"理论需要结合实践。在实际应用中，我们可以看到许多{topic}的成功案例。这些案例不仅验证了其有效性，也为我们提供了宝贵的经验和参考。通过分析这些案例，我们可以总结出一些通用的方法论，指导后续的实践。\n\n特别值得注意的是，成功的应用往往不是简单的技术堆砌，而是深入理解业务需求后的创新应用。"
        },
        {
            "subtitle": "常见问题与解决方案",
            "content": f"在实践过程中，我们难免会遇到各种问题。常见的问题包括：理解偏差导致的错误应用、技术选型不当造成的性能瓶颈、以及缺乏系统性规划带来的维护困难等。\n\n针对这些问题，我们需要采取相应的解决策略：加强理论学习、建立完善的测试体系、以及持续优化和迭代。"
        }
    ]


def match_section_knowledge(section_title: str, knowledge: Dict) -> List[str]:
    """根据章节标题匹配知识库内容"""
    if not knowledge:
        return []
    
    section_lower = section_title.lower()
    
    # 匹配不同章节类型
    if "核心概念" in section_title or "基本原理" in section_title:
        return knowledge.get("核心概念", [])
    elif "工作机制" in section_title or "工作原理" in section_title:
        return knowledge.get("工作原理", [])
    elif "应用场景" in section_title:
        return knowledge.get("应用场景", [])
    elif "优势" in section_title or "局限" in section_title:
        advantages = knowledge.get("技术优势", [])
        limitations = knowledge.get("局限性", [])
        return advantages + limitations
    elif "发展趋势" in section_title or "未来" in section_title:
        return knowledge.get("发展趋势", [])
    
    # 默认返回第一个可用的知识类别
    for key in ["核心概念", "工作原理", "应用场景", "技术优势"]:
        if key in knowledge:
            return knowledge[key]
    
    return []


def generate_elaboration(point: str, topic: str) -> str:
    """为知识点生成详细阐述"""
    elaborations = {
        "去中心化": "这意味着没有单一的控制节点，数据分布在网络的各个节点上。即使部分节点失效，整个系统仍然可以正常运行。这种设计大大提高了系统的可靠性和抗攻击能力。",
        "不可篡改": "区块链使用哈希函数将区块链接在一起，任何数据的改动都会导致哈希值变化，从而被立即发现。这种特性使得区块链非常适合用于存储重要的交易记录和凭证。",
        "智能合约": "智能合约是运行在区块链上的自动执行程序。一旦满足预设条件，合约就会自动执行，无需人工干预。这大大降低了交易成本，提高了执行效率。",
        "分布式账本": "每个节点都保存一份完整的数据副本，任何交易都需要网络中的多数节点确认才能生效。这种机制确保了数据的一致性和可靠性。",
        "共识机制": "共识机制是区块链网络中节点达成一致的方式。常见的有工作量证明（PoW）和权益证明（PoS）。不同的共识机制在安全性、效率和去中心化程度之间有不同的权衡。"
    }
    
    for key, value in elaborations.items():
        if key in point:
            return value
    
    return f"这一点在实际应用中非常重要。理解{point[:10]}的本质，有助于我们更好地把握{topic}的核心价值。建议读者在实践中多加体会，逐步深化理解。"


def expand_with_knowledge(article: str, additional_words: int, knowledge: Dict, topic: str) -> str:
    """使用知识库扩展内容"""
    supplement_parts = ["\n\n## 深入实践与进阶技巧\n"]
    
    supplement_parts.append(f"""
在掌握了{topic}的基础知识后，我们还需要了解一些进阶的实践技巧。这些技巧来自于实际项目经验的总结，能够帮助我们在工作中更加得心应手。
""")
    
    if knowledge:
        # 使用知识库中的额外信息
        all_points = []
        for key, values in knowledge.items():
            all_points.extend(values)
        
        if len(all_points) > 8:
            supplement_parts.append(f"\n### 进阶要点详解\n")
            for i, point in enumerate(all_points[8:], 1):
                supplement_parts.append(f"\n#### {i}. {point[:25]}\n")
                supplement_parts.append(f"{point}\n")
                # 为每个要点添加实践建议
                supplement_parts.append(f"\n**实践建议**：在实际项目中应用这一点时，建议从小规模开始验证，逐步扩大应用范围。同时要注意监控相关指标，确保达到预期效果。\n")
    
    # 添加常见问题解答
    supplement_parts.append(f"""
### 常见问题与解决方案

在学习{topic}的过程中，很多读者会遇到一些共性问题。以下是几个典型问题及其解决方案：

**Q1: 如何快速入门？**

建议从官方文档和权威教程开始，先建立整体认知框架。然后通过实际项目练习，在实践中加深理解。不要急于求成，扎实的基础是后续深入学习的保障。

**Q2: 遇到性能瓶颈怎么办？**

首先要通过性能分析工具定位瓶颈所在。然后针对性地进行优化，可能涉及算法改进、架构调整或资源配置优化等方面。记住，过早优化是万恶之源。

**Q3: 如何保持技术更新？**

技术领域发展迅速，建议定期阅读技术博客、参加技术会议、关注开源社区动态。同时，建立自己的知识体系，将新学到的内容与已有知识进行关联。

### 学习路径建议

对于不同层次的读者，我们提供以下学习建议：

**初学者**：
1. 先理解核心概念和基本原理
2. 通过简单示例建立感性认识
3. 完成一个小型实践项目
4. 阅读优秀开源项目的代码

**进阶者**：
1. 深入研究源码实现细节
2. 参与开源项目贡献
3. 尝试解决复杂的实际问题
4. 形成自己的方法论和最佳实践

**专家**：
1. 关注前沿技术发展趋势
2. 进行技术创新和优化
3. 分享经验，指导他人
4. 推动行业标准和规范建设

### 总结与展望

{topic}是一个不断发展的领域，新的技术和方法层出不穷。本文试图从多个维度对这一话题进行全面解读，希望能够帮助读者建立起系统性的认知框架。

回顾全文，我们首先介绍了核心概念和基本原理，然后深入分析了工作机制和实现细节，接着探讨了实际应用场景和最佳实践，最后提供了进阶学习的路径建议。

展望未来，{topic}将继续在各个领域发挥重要作用。随着技术的不断成熟和应用场景的不断拓展，我们可以期待更多创新性的解决方案出现。

最后要强调的是，理论与实践的结合是掌握任何技术的关键。希望读者能够将本文所学应用到实际工作中，在实践中不断深化理解，形成自己的见解和方法论。

如果你有任何问题或想法，欢迎交流讨论。技术的进步离不开社区的共同努力，让我们一起推动{topic}的发展。
""")
    
    return article + "\n".join(supplement_parts)


def optimize_seo(topic: str, article: str, keywords: List[str]) -> Dict[str, Any]:
    """SEO优化"""
    title = generate_seo_title(topic, keywords)
    meta_description = generate_meta_description(topic, article, keywords)
    optimized_keywords = optimize_keywords(topic, article, keywords)
    
    return {
        "title": title,
        "meta_description": meta_description,
        "keywords": optimized_keywords
    }


def generate_seo_title(topic: str, keywords: List[str]) -> str:
    """生成SEO标题"""
    templates = [
        f"深度解析：{topic}的完整指南（2026最新）",
        f"{topic}：从入门到精通的全方位解读",
        f"一文读懂{topic}：原理、应用与最佳实践",
        f"{topic}终极指南：专家级深度分析"
    ]
    
    if keywords and len(keywords[0]) > 2:
        templates.append(f"{topic}与{keywords[0]}：深度对比与实践指南")
    
    return templates[0]


def generate_meta_description(topic: str, article: str, keywords: List[str]) -> str:
    """生成Meta描述"""
    desc = f"深入解读{topic}，涵盖核心原理、实际应用、最佳实践等内容。"
    
    if keywords:
        desc += f"关键词：{', '.join(keywords[:3])}。"
    
    desc += "阅读本文，获取专业级的深度分析。"
    
    if len(desc) > 160:
        desc = desc[:157] + "..."
    
    return desc


def optimize_keywords(topic: str, article: str, user_keywords: List[str]) -> List[str]:
    """优化关键词"""
    all_keywords = set(user_keywords)
    topic_words = topic.split()
    all_keywords.update(topic_words)
    
    related_terms = ["原理", "应用", "实践", "案例", "优化", "指南", "教程", "分析", "对比", "趋势"]
    all_keywords.update(related_terms)
    
    return list(all_keywords)[:10]


def humanize_content(article: str, style: str) -> str:
    """人性化处理"""
    formal_to_casual = {
        "综上所述": "总的来说",
        "由此可见": "不难看出",
        "显而易见": "很明显",
        "值得注意的是": "有意思的是",
        "需要指出的是": "这里要说一下",
        "从某种程度上说": "某种程度上",
        "在一定程度上": "一定程度上",
        "基于上述分析": "基于以上",
        "我们可以得出结论": "可以说",
        "这表明": "这说明"
    }
    
    for formal, casual in formal_to_casual.items():
        article = article.replace(formal, casual)
    
    transitions = ["说实话，", "老实说，", "其实，", "说白了，", "简单来说，", "讲真，"]
    
    paragraphs = article.split("\n\n")
    for i in range(1, min(len(paragraphs), len(transitions) + 1)):
        if i % 3 == 0 and not paragraphs[i].startswith("#"):
            paragraphs[i] = transitions[i % len(transitions)] + paragraphs[i]
    
    article = "\n\n".join(paragraphs)
    
    return article


def count_words(text: str) -> int:
    """统计字数"""
    clean_text = re.sub(r'[#*\[\]()|`\-]', '', text)
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', clean_text))
    english_words = len(re.findall(r'[a-zA-Z]+', clean_text))
    return chinese_chars + english_words


def estimate_reading_time(text: str) -> str:
    """估算阅读时长"""
    word_count = count_words(text)
    minutes = max(1, word_count // 250)
    
    if minutes < 60:
        return f"{minutes}分钟"
    else:
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}小时{mins}分钟"


def format_outline_output(topic: str, outline: List[Dict], keywords: List[str]) -> str:
    """格式化大纲输出"""
    lines = [
        f"# {topic} - 文章大纲",
        "",
        "## 基本信息",
        f"- 主题：{topic}",
        f"- 关键词：{', '.join(keywords) if keywords else '无'}",
        "",
        "## 文章结构",
        ""
    ]
    
    total_words = 0
    for i, section in enumerate(outline, 1):
        lines.append(f"{i}. **{section['title']}** (~{section['word_count']}字)")
        for point in section.get('key_points', []):
            lines.append(f"   - {point}")
        lines.append("")
        total_words += section['word_count']
    
    lines.extend([
        "## 统计",
        f"- 预计总字数：{total_words}字",
        f"- 章节数：{len(outline)}"
    ])
    
    return "\n".join(lines)


def format_article_output(title: str, meta_desc: str, keywords: List[str],
                         article: str, reading_time: str, target_words: int) -> str:
    """格式化文章输出"""
    actual_words = count_words(article)
    
    lines = [
        f"# {title}",
        "",
        "> 📄 **文章信息**",
        f"> - 阅读时长：{reading_time}",
        f"> - 字数统计：{actual_words}字（目标{target_words}字）",
        f"> - 关键词：{', '.join(keywords[:5])}",
        "",
        "---",
        "",
        "## 📋 Meta信息（用于SEO）",
        "",
        f"**标题**：{title}",
        "",
        f"**描述**：{meta_desc}",
        "",
        f"**关键词**：{', '.join(keywords)}",
        "",
        "---",
        "",
        article,
        "",
        "---",
        "",
        "*本文由 Blog Writer Skill 自动生成*",
        f"*生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}*"
    ]
    
    return "\n".join(lines)


def submit_feedback(execution_id: str, rating: int, feedback_text: str = None) -> Dict:
    """
    提交用户反馈
    
    Args:
        execution_id: 执行ID（从执行结果中获取）
        rating: 用户评分 1-5
        feedback_text: 用户文字反馈（可选）
    
    Returns:
        提交结果
    """
    if not SELF_IMPROVE_AVAILABLE:
        return {
            "success": False,
            "error": "Self-improve 系统不可用"
        }
    
    try:
        manager = get_improvement_manager()
        success = manager.feedback_collector.add_user_feedback(
            execution_id, rating, feedback_text
        )
        
        if success:
            return {
                "success": True,
                "message": "反馈提交成功，谢谢！"
            }
        else:
            return {
                "success": False,
                "error": "未找到对应的执行记录"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_improvement_report() -> Dict:
    """
    获取自我改进报告
    
    Returns:
        改进报告
    """
    if not SELF_IMPROVE_AVAILABLE:
        return {
            "success": False,
            "error": "Self-improve 系统不可用"
        }
    
    try:
        manager = get_improvement_manager()
        report = manager.get_improvement_report()
        return {
            "success": True,
            "report": report
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Blog Writer Skill')
    parser.add_argument('--feedback', action='store_true', help='提交反馈模式')
    parser.add_argument('--report', action='store_true', help='查看改进报告')
    parser.add_argument('--execution-id', type=str, help='执行ID')
    parser.add_argument('--rating', type=int, help='评分 1-5')
    parser.add_argument('--feedback-text', type=str, help='反馈文字')
    
    args = parser.parse_args()
    
    if args.report:
        # 查看改进报告
        result = get_improvement_report()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["success"] else 1
    
    if args.feedback:
        # 提交反馈模式
        if not args.execution_id or not args.rating:
            print("错误: 提交反馈需要提供 --execution-id 和 --rating")
            return 1
        
        result = submit_feedback(args.execution_id, args.rating, args.feedback_text)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["success"] else 1
    
    # 默认执行写作
    test_params = {
        "topic": "区块链技术",
        "word_count": 3000,
        "style": "professional",
        "keywords": "区块链,去中心化,智能合约",
        "outline": False,
        "humanize": True
    }
    
    result = execute(test_params)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
