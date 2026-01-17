import os
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from jinja2 import Template

def load_prompts(prompt_dir: Path):
    """读取 prompts/ 文件夹下所有的 .md 文件"""
    prompts = {}
    for md_file in prompt_dir.glob("*.md"):
        prompts[md_file.stem] = md_file.read_text(encoding="utf-8")
    return prompts

def generate_wpt_code(demand: str, feature: str, api_key: str = None, base_url: str = None, model: str = None):
    """核心生成逻辑，可供 CLI 和 Streamlit 调用"""
    # 1. 加载环境变量 (如果未提供参数)
    if not api_key:
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("未找到 API_KEY")

    if not base_url:
        base_url = os.getenv("OPENAI_BASE_URL")
        if not base_url and api_key.startswith("AIzaSy"):
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    
    client = OpenAI(api_key=api_key, base_url=base_url)

    # 2. 读取提示词
    base_dir = Path(__file__).parent.parent
    prompt_dir = base_dir / "prompts"
    prompts = load_prompts(prompt_dir)

    # 3. 拼接 Base Prompt (meta, system, coding)
    base_prompt = "\n\n".join([
        prompts.get("meta", ""),
        prompts.get("system", ""),
        prompts.get("coding", "")
    ])

    # 4. 填充 user_template
    user_template_str = prompts.get("user_template", "")
    template = Template(user_template_str)
    user_prompt = template.render(user_demand=demand, target_feature=feature)

    if not model:
        model = os.getenv("MODEL_NAME", "gpt-4o")
        if api_key.startswith("AIzaSy") and model == "gpt-4o":
            model = "gemini-2.0-flash"

    # 5. 调用 AI 接口
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": base_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )

    # 6. 解析返回的 JSON
    result_content = response.choices[0].message.content
    
    # 兼容处理：去除可能的 Markdown 标记
    if "```json" in result_content:
        result_content = result_content.split("```json")[1].split("```")[0].strip()
    elif "```" in result_content:
        result_content = result_content.split("```")[1].split("```")[0].strip()
    
    try:
        # 使用 strict=False 可以处理 Invalid \escape 等非标准转义问题
        result_json = json.loads(result_content, strict=False)
    except json.JSONDecodeError as e:
        # 如果解析依然失败，尝试一次简单的反斜杠转义修复
        try:
            fixed_content = result_content.replace('\\', '\\\\')
            result_json = json.loads(fixed_content, strict=False)
        except:
            raise ValueError(f"AI 返回的 JSON 格式非法: {str(e)}\n原始内容预览: {result_content[:200]}...")

    if isinstance(result_json, list) and len(result_json) > 0:
        result_json = result_json[0]

    if not isinstance(result_json, dict):
        raise ValueError(f"AI 返回的不是有效的 JSON 对象: {result_content}")

    return result_json

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="WPT 自动化脚本生成引擎")
    parser.add_argument("--demand", required=True, help="测试需求描述")
    parser.add_argument("--feature", required=True, help="目标特性")
    args = parser.parse_args()

    try:
        result = generate_wpt_code(args.demand, args.feature)
        filename = result.get("filename", "output.html")
        content = result.get("content", "")

        # 保存到 wpt/tests/ 文件夹
        base_dir = Path(__file__).parent.parent
        output_dir = base_dir / "wpt" / "tests"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / filename
        output_path.write_text(content, encoding="utf-8")

        print(f"成功！结果已保存至: {output_path}")

    except Exception as e:
        print(f"执行过程中出现错误: {e}")

if __name__ == "__main__":
    main()
