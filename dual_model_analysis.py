#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双模型股票分析脚本
同时使用两个模型分析同一只股票，生成更全面的分析报告

用法:
    python dual_model_analysis.py 600519
    python dual_model_analysis.py 002709 天赐材料
"""

import os
import sys
import asyncio
from typing import Optional, Dict, Any

# 设置项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.config import Config, get_config
from src.analyzer import StockAnalyzer
from src.search_service import SearchService
from src.stock_data import StockDataProvider


def create_analyzer_for_model(config: Config, model_name: str) -> StockAnalyzer:
    """为指定模型创建分析器"""
    # 临时修改配置使用指定模型
    config.litellm_model = model_name
    config.litellm_fallback_models = []
    
    return StockAnalyzer(config)


async def analyze_with_model(
    analyzer: StockAnalyzer,
    stock_code: str,
    stock_name: str,
    model_name: str
) -> Dict[str, Any]:
    """使用指定模型分析股票"""
    print(f"\n{'='*50}")
    print(f"🤖 使用模型: {model_name}")
    print(f"{'='*50}")
    
    try:
        # 创建搜索服务和数据提供器
        search_service = SearchService(analyzer.config)
        stock_data = StockDataProvider(analyzer.config)
        
        # 获取股票信息
        stock_info = await stock_data.get_stock_info(stock_code)
        if stock_name:
            stock_info['name'] = stock_name
        
        # 获取实时行情
        realtime_data = await stock_data.get_realtime_quotes([stock_code])
        
        # 获取近期新闻
        news = await search_service.search_stock_news(stock_code, max_results=5)
        
        # 执行分析
        context = {
            'stock_code': stock_code,
            'stock_name': stock_name or stock_info.get('name', stock_code),
            'stock_info': stock_info,
            'realtime_data': realtime_data,
            'news': news,
            'is_hk': stock_code.startswith(('hk', 'HK', '0')),
            'is_us': stock_code.isalpha(),
        }
        
        result = await analyzer.analyze(context)
        
        return {
            'model': model_name,
            'success': True,
            'result': result,
            'context': context
        }
        
    except Exception as e:
        print(f"❌ 模型 {model_name} 分析失败: {e}")
        return {
            'model': model_name,
            'success': False,
            'error': str(e)
        }


def merge_results(gemini_result: Dict, deepseek_result: Dict) -> str:
    """合并两个模型的分析结果"""
    
    report = f"""
{'='*60}
📊 双模型综合分析报告
{'='*60}

股票: {gemini_result.get('context', {}).get('stock_name', 'N/A')} 
代码: {gemini_result.get('context', {}).get('stock_code', 'N/A')}

"""
    
    # Gemini 结果
    if gemini_result.get('success'):
        report += f"""
{'='*60}
🟢 Gemini 模型分析结果
{'='*60
{gemini_result.get('result', {}).content[:3000] if hasattr(gemini_result.get('result', {}), 'content') else str(gemini_result.get('result', {}))[:3000]}
"""
    else:
        report += f"""
{'='*60}
🟢 Gemini 模型分析结果
{'='*60
❌ 分析失败: {gemini_result.get('error', '未知错误')}
"""
    
    # DeepSeek 结果
    if deepseek_result.get('success'):
        report += f"""
{'='*60}
🔵 DeepSeek 模型分析结果
{'='*60
{deepseek_result.get('result', {}).content[:3000] if hasattr(deepseek_result.get('result', {}), 'content') else str(deepseek_result.get('result', {}))[:3000]}
"""
    else:
        report += f"""
{'='*60}
🔵 DeepSeek 模型分析结果
{'='*60
❌ 分析失败: {deepseek_result.get('error', '未知错误')}
"""
    
    # 综合建议
    report += f"""
{'='*60}
📝 综合分析建议
{'='*60

当两个模型的结论一致时，信号更强；
当结论不一致时，建议保持谨慎，等待进一步确认。

"""
    
    return report


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python dual_model_analysis.py <股票代码> [股票名称]")
        print("示例: python dual_model_analysis.py 600519 贵州茅台")
        print("       python dual_model_analysis.py 002709 天赐材料")
        print("       python dual_model_analysis.py hk0981 中芯国际")
        sys.exit(1)
    
    stock_code = sys.argv[1]
    stock_name = sys.argv[2] if len(sys.argv) > 2 else ""
    
    print(f"\n🚀 开始双模型分析: {stock_code} {stock_name}")
    
    # 加载配置
    config = get_config()
    
    # 设置 DeepSeek 配置
    os.environ['OPENAI_API_KEY'] = 'sk-365cf5111f1a4ebc8bfbe87793122b9a'
    os.environ['OPENAI_BASE_URL'] = 'https://api.deepseek.com/v1'
    os.environ['OPENAI_MODEL'] = 'deepseek-chat'
    
    # 重新加载配置
    config = get_config()
    
    # 创建两个分析器
    print("\n📱 初始化 Gemini 分析器...")
    gemini_analyzer = create_analyzer_for_model(config, 'gemini/gemini-2.0-flash')
    
    print("📱 初始化 DeepSeek 分析器...")
    # 临时修改配置使用 DeepSeek
    config_deepseek = get_config()
    config_deepseek.litellm_model = 'deepseek/deepseek-chat'
    config_deepseek.litellm_fallback_models = []
    deepseek_analyzer = StockAnalyzer(config_deepseek)
    
    # 并行执行两个模型的分析
    print("\n⚡ 开始并行分析...")
    
    gemini_task = analyze_with_model(
        gemini_analyzer, stock_code, stock_name, "Gemini"
    )
    deepseek_task = analyze_with_model(
        deepseek_analyzer, stock_code, stock_name, "DeepSeek"
    )
    
    gemini_result, deepseek_result = await asyncio.gather(gemini_task, deepseek_task)
    
    # 生成合并报告
    report = merge_results(gemini_result, deepseek_result)
    
    print(report)
    
    # 保存报告
    output_file = f"/tmp/{stock_code}_dual_analysis.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n💾 报告已保存到: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
