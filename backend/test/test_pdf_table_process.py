import pdfplumber
import os

"""
测试表格处理函数
"""

def get_cell_span(row_idx, col_idx, table_data):
    """
    计算单元格的rowspan和colspan（基于表格数据推断合并单元格）
    :param row_idx: 当前单元格行索引
    :param col_idx: 当前单元格列索引
    :param table_data: 表格数据（二维列表）
    :return: (rowspan, colspan)
    """
    rowspan = 1
    colspan = 1
    
    # 检查当前单元格是否为空（如果是空单元格，可能是合并单元格的一部分）
    current_cell = table_data[row_idx][col_idx] if row_idx < len(table_data) and col_idx < len(table_data[row_idx]) else ""
    
    # 如果当前单元格为空，则不需要计算合并
    if not current_cell or current_cell.strip() == "":
        return 1, 1
    
    # 计算colspan：向右检查连续的空单元格
    for c in range(col_idx + 1, len(table_data[row_idx])):
        next_cell = table_data[row_idx][c] if c < len(table_data[row_idx]) else ""
        if not next_cell or next_cell.strip() == "":
            colspan += 1
        else:
            break
    
    # 计算rowspan：向下检查连续的空单元格
    for r in range(row_idx + 1, len(table_data)):
        if col_idx < len(table_data[r]):
            next_cell = table_data[r][col_idx]
            if not next_cell or next_cell.strip() == "":
                rowspan += 1
            else:
                break
        else:
            break
    
    return rowspan, colspan

def pdf_tables_to_md_pure_python(pdf_path, output_md_path):
    """
    纯Python实现：PDF表格转Markdown（HTML格式）
    :param pdf_path: 输入PDF文件路径
    :param output_md_path: 输出Markdown文件路径
    """
    # 初始化Markdown内容
    md_content = "# PDF提取的表格（纯Python实现）\n\n"
    table_index = 1

    # 打开PDF文件
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # 遍历所有页面
            for page_num, page in enumerate(pdf.pages, 1):
                # 提取当前页面的所有表格
                tables = page.extract_tables(
                    table_settings={
                        "vertical_strategy": "lines",  # 按竖线识别表格列
                        "horizontal_strategy": "lines",  # 按横线识别表格行
                        "explicit_vertical_lines": page.objects.get("lines", []),
                        "explicit_horizontal_lines": page.objects.get("lines", []),
                    }
                )
                # 提取单元格的详细信息（用于判断合并单元格）
                # 使用 pdfplumber 的 find_tables 方法获取表格结构信息
                table_cells = []
                try:
                    # 使用 find_tables 获取表格结构
                    found_tables = page.find_tables(table_settings={
                        "vertical_strategy": "lines",
                        "horizontal_strategy": "lines",
                        "explicit_vertical_lines": page.objects.get("lines", []),
                        "explicit_horizontal_lines": page.objects.get("lines", []),
                    })
                    
                    # 提取第一个表格的单元格信息（如果有的话）
                    if found_tables:
                        table_obj = found_tables[0]
                        # 获取表格的边界框信息
                        table_bbox = table_obj.bbox
                        # 这里可以添加更多单元格信息提取逻辑
                        
                except Exception as e:
                    print(f"提取表格单元格信息时出错: {e}")
                    table_cells = []

                if not tables:
                    continue

                # 处理当前页面的每个表格
                for table in tables:
                    md_content += f"## 表格 {table_index}（第{page_num}页）\n\n"
                    table_index += 1

                    # 构建HTML表格
                    html_table = ["<table border='1' style='border-collapse: collapse;'>"]
                    # 记录已处理的单元格（避免合并单元格重复渲染）
                    processed_cells = set()

                    # 逐行处理表格数据
                    for row_idx, row in enumerate(table):
                        html_table.append("  <tr>")
                        for col_idx, cell_text in enumerate(row):
                            # 跳过已处理的合并单元格
                            if (row_idx, col_idx) in processed_cells:
                                continue

                            # 清理单元格文本
                            cell_text = cell_text.strip() if cell_text else ""
                            # 转义HTML特殊字符
                            cell_text = cell_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

                            # 计算合并单元格的跨度
                            rowspan, colspan = get_cell_span(row_idx, col_idx, table)

                            # 标记合并的单元格为已处理
                            for r in range(row_idx, row_idx + rowspan):
                                for c in range(col_idx, col_idx + colspan):
                                    processed_cells.add((r, c))

                            # 构建HTML单元格
                            cell_attrs = []
                            if rowspan > 1:
                                cell_attrs.append(f"rowspan='{rowspan}'")
                            if colspan > 1:
                                cell_attrs.append(f"colspan='{colspan}'")

                            if cell_attrs:
                                html_table.append(f"    <td {' '.join(cell_attrs)}>{cell_text}</td>")
                            else:
                                html_table.append(f"    <td>{cell_text}</td>")

                        html_table.append("  </tr>")

                    # 结束HTML表格
                    html_table.append("</table>\n\n")
                    # 将HTML表格添加到Markdown内容
                    md_content += "\n".join(html_table) + "\n"

        # 写入Markdown文件
        with open(output_md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"✅ 成功生成Markdown文件：{output_md_path}")

    except FileNotFoundError:
        print(f"❌ PDF文件不存在：{pdf_path}")
    except Exception as e:
        print(f"❌ 处理失败：{str(e)}")

# ------------------- 示例调用 -------------------
if __name__ == "__main__":
    # 替换为你的PDF路径和输出Markdown路径
    PDF_FILE_PATH = "../files/fj-23p.pdf"   # 输入PDF文件路径
    OUTPUT_MD_PATH = "extracted_tables_pure_python.md"  # 输出Markdown文件路径  

    if os.path.exists(PDF_FILE_PATH):
        pdf_tables_to_md_pure_python(PDF_FILE_PATH, OUTPUT_MD_PATH)
    else:
        print(f"❌ 找不到PDF文件：{PDF_FILE_PATH}")