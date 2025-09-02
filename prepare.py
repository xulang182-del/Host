import os
import time
import subprocess
import yaml
from m_config.load_path import path_config


def convert_ui_files():
    """
    将ui目录中的所有.ui文件转换为.py文件
    """
    ui_dir = path_config.ui_dir
    uic_path = path_config.uic_path

    if not os.path.exists(ui_dir):
        print(f"UI目录不存在: {ui_dir}")
        return

    current_time = time.time()
    converted_files = []

    for file_name in os.listdir(ui_dir):
        if not file_name.endswith(".ui"):
            continue

        file_path = os.path.join(ui_dir, file_name)
        modified_time = os.path.getmtime(file_path)

        # 检查文件是否在10分钟内修改过
        if current_time - modified_time > 600:  # 600秒=10分钟
            continue

        # 生成输出文件名 (ui_原文件名.py)
        py_file_name = f"ui_{file_name.replace('.ui', '.py')}"
        output_path = os.path.join(ui_dir, py_file_name)

        # 执行转换命令
        command = [uic_path, file_path, "-o", output_path]
        try:
            subprocess.run(command, check=True)
            converted_files.append(file_name)
            print(f"转换成功: {file_name} -> {py_file_name}")
        except subprocess.CalledProcessError as e:
            print(f"转换失败: {file_name}, 错误: {e}")
        print("fix import...", os.path.join(ui_dir, py_file_name))
        
        if not os.path.exists(os.path.join(ui_dir, py_file_name)):
            print(f"文件不存在: {os.path.join(ui_dir, py_file_name)}")
        with open(os.path.join(ui_dir, py_file_name), "a+", encoding="utf-8") as f:
            f.seek(0)
            text = f.read()

        with open(os.path.join(ui_dir, py_file_name), "w+", encoding="utf-8") as f:
            text = text.replace("import src_rc", "import src.src")
            f.write(text)

    return converted_files


def convert_qrc_file():
    """
    将资源文件.qrc转换为.py文件
    """
    qrc_path = path_config.qrc_path
    rcc_path = path_config.rcc_path

    if not os.path.exists(qrc_path):
        print(f"QRC文件不存在: {qrc_path}")
        return None

    current_time = time.time()
    modified_time = os.path.getmtime(qrc_path)

    # 检查文件是否在10分钟内修改过
    if current_time - modified_time > 600:  # 600秒=10分钟
        return None

    # 生成输出文件名 (resource_rc.py)
    output_path = os.path.join(os.path.dirname(qrc_path), "src.py")

    # 执行转换命令
    command = [rcc_path, qrc_path, "-o", output_path]
    try:
        subprocess.run(command, check=True)
        print(f"资源文件转换成功: {qrc_path} -> {os.path.basename(output_path)}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"资源文件转换失败: {qrc_path}, 错误: {e}")
        return None


def fix_imports_in_ui_files(converted_ui_files):
    """
    修复UI生成的.py文件中的导入语句
    """
    ui_dir = path_config.ui_dir
    fix_count = 0

    for py_file in converted_ui_files:
        py_file = f"ui_{py_file.replace('.ui', '.py')}"
        file_path = os.path.join(ui_dir, py_file)

        if not os.path.exists(file_path):
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 替换旧的导入语句
            new_content = content.replace("import resource_rc",
                                          "import src.resource_rc").replace(
                                              "from resource_rc",
                                              "from src.resource_rc")

            if content != new_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                fix_count += 1
                print(f"导入已修复: {py_file}")
        except Exception as e:
            print(f"修复导入失败: {py_file}, 错误: {e}")

    return fix_count


def main():
    print("=" * 50)
    print("开始转换UI和资源文件...")
    print(f"项目路径: {path_config.project_path}")
    print(f"UI目录: {path_config.ui_dir}")
    print(f"QRC文件: {path_config.qrc_path}")
    print("=" * 50 + "\n")

    start_time = time.time()

    # 转换UI文件
    converted_ui = convert_ui_files()
    print(f"\n转换完成 {len(converted_ui)} 个UI文件\n")

    # 转换资源文件
    qrc_output = convert_qrc_file()

    # 修复导入语句
    if converted_ui:
        fix_count = fix_imports_in_ui_files(converted_ui)
        print(f"\n修复了 {fix_count} 个文件中的资源导入")

    elapsed = time.time() - start_time
    print(f"\n{'操作成功完成' if qrc_output or converted_ui else '没有需要转换的文件'}")
    print(f"耗时: {elapsed:.2f}秒")


if __name__ == "__main__":
    main()
