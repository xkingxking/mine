from mine_sdk import MineSDK

sdk = MineSDK(base_url="http://119.29.147.62:5000")

# 1. 获取全部题库列表（包含元数据）
print("=== 所有题库 ===")
banks = sdk.list_question_banks()
print("基础题库:")
for b in banks["baseBanks"]:
    print(f"- 题库ID: {b['id']}")
    print(f"  名称: {b['name']}")
    print(f"  元数据:")
    print(f"    - 题目总数: {b['metadata']['total']}")
    print(f"    - 维度: {', '.join(b['metadata']['dimensions'])}")
    print(f"    - 难度: {', '.join(b['metadata']['difficulties'])}")
    print(f"    - 创建时间: {b['metadata']['created_at']}")
    print(f"    - 版本: {b['metadata']['version']}")
    print()

print("变形题库:")
for b in banks["transformedBanks"]:
    print(f"- 题库ID: {b['id']}")
    print(f"  来源文件: {b['source_file']}")
    print(f"  元数据:")
    print(f"    - 变形版本数: {b['metadata']['total_transformed_versions']}")
    print(f"    - 变形时间: {b['metadata']['transformed_at']}")
    print(f"    - 源文件: {b['metadata']['source_file']}")
    print()

# 2. 创建题库
result = sdk.create_question_bank(
    name="sdk_test",
    dimensions=["语言能力", "知识能力"],
    difficulties=["easy", "medium"],
    count=2
)
print("\n=== 创建题库 ===")
print("题库创建:", result)

# 3. 预览题库
bank_id = result["bankId"]
questions = sdk.preview_question_bank(bank_id)
print("\n=== 预览题库 ===")
print(f"题库ID: {bank_id}")
print(f"题目数量: {questions['total']}")
print("题目列表:", questions["questions"])

# 4. 列出所有变形任务
tasks = sdk.list_all_tasks()
print("\n=== 所有任务列表 ===")
print("任务列表:", tasks)

# 5. 创建变形任务和评估任务
task_result = sdk.create_transform_task("sdk_test_task", result["file"])
print("\n=== 创建变形任务 ===")
print("创建任务:", task_result)

# 6. 检查任务状态
status = sdk.check_task_status("sdk_test_task")
print("\n=== 检查任务状态 ===")
print("任务状态:", status)

# 7. 模型评估
qs = questions["questions"]
report = sdk.evaluate_model("deepseek-v3", qs, dataset_path=bank_id)
print("\n=== 模型评估 ===")
print("评估结果:", report)

# 8. 获取报告内容
report_content = sdk.get_report_content("deepseek-v3_domains.json")
print("\n=== 报告内容 ===")
print("报告内容:", report_content)

# 9. 下载评估报告（JSON和PDF）
download_result = sdk.download_report("deepseek-v3_domains.json")
print("\n=== 下载报告 ===")
print("JSON报告位置:", download_result["json"])
print("PDF报告位置:", download_result["pdf"])

# 10. 模型对比
compare = sdk.compare_models()
print("\n=== 模型对比 ===")
print("横向对比：")
for domain in compare["domains"]:
    print(f" - {domain}")
    for model in compare["models"]:
        s = compare["scores"].get(model, {}).get(domain, {})
        print(f"   模型 {model}: 平均分={s.get('average_score')}, 数量={s.get('total_evaluations')}")


# 11. 删除变形任务
try:
    delete_result = sdk.delete_transform_task("sdk_test_task")
    print("\n=== 删除任务 ===")
    print("删除结果:", delete_result)
except Exception as e:
    print("\n=== 删除任务失败 ===")
    print(f"错误信息: {str(e)}")
    print("提示: 任务可能已经被删除或不存在")
