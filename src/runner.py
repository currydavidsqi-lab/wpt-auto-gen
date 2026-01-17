import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright

async def run_wpt_test(html_file_path: Path):
    """
    使用 Playwright 运行 WPT 测试并抓取结果。
    """
    results = {
        "status": "error",
        "test_name": html_file_path.name,
        "subtests": [],
        "log": ""
    }

    if not html_file_path.exists():
        results["log"] = f"文件不存在: {html_file_path}"
        return results

    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # 转发控制台日志以便调试
        page.on("console", lambda msg: print(f"浏览器日志: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"页面脚本错误: {exc}"))

        # 注入初始化脚本：尽早定义结果对象和回调
        # 我们直接覆盖 WPT 的回调注册，或者在它们可用时立即注入
        await page.add_init_script("""
            window.test_results = { subtests: [], completed: false, status: null };
            
            window._setup_wpt_hooks = function() {
                if (window.add_result_callback && !window._hooks_installed) {
                    window.add_result_callback(function(test) {
                        window.test_results.subtests.push({
                            name: test.name,
                            status: test.status,
                            message: test.message,
                            stack: test.stack
                        });
                    });
                    window.add_completion_callback(function(tests, status) {
                        window.test_results.status = status;
                        window.test_results.completed = true;
                    });
                    window._hooks_installed = true;
                    console.log("WPT 回调挂载成功");
                }
            };

            // 轮询检查 WPT 钩子是否可用
            var interval = setInterval(function() {
                window._setup_wpt_hooks();
                if (window._hooks_installed) clearInterval(interval);
            }, 50);
            
            window.addEventListener('load', window._setup_wpt_hooks);
        """)

        try:
            file_url = f"file://{html_file_path.absolute()}"
            print(f"正在加载测试文件: {file_url}")
            
            # 导航并等待页面加载
            await page.goto(file_url, wait_until="load")

            # 等待测试完成，最多等待 10 秒
            for _ in range(100):
                # 防御性检查 window.test_results
                is_completed = await page.evaluate("""
                    () => window.test_results && window.test_results.completed
                """)
                if is_completed:
                    break
                await asyncio.sleep(0.1)
            
            # 获取结果，增加空值处理
            raw_results = await page.evaluate("""
                () => window.test_results || { error: "window.test_results is undefined" }
            """)
            
            if "error" in raw_results:
                results["log"] = raw_results["error"]
            else:
                results.update(raw_results)
                if not results.get("completed"):
                    results["log"] = "测试执行超时"
                else:
                    results["status"] = "success"

        except Exception as e:
            results["log"] = f"运行器异常: {str(e)}"
        finally:
            await browser.close()
            
    return results

if __name__ == "__main__":
    # 查找最新生成的测试文件
    test_dir = Path(__file__).parent.parent / "wpt" / "tests"
    test_files = list(test_dir.glob("*.html"))
    if test_files:
        latest_file = max(test_files, key=os.path.getmtime)
        print(f"运行最新测试: {latest_file}")
        res = asyncio.run(run_wpt_test(latest_file))
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print("未找到测试文件")
