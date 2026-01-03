from pathlib import Path
from paddleocr import PPStructureV3

"""
测试PPStructureV3表格处理函数

太慢，23p的pdf使用CPU时需要1个多小时，对文档中的原生表格处理还原较好但对图片中的表格识别一般。
整体上还有优化空间。
"""

input_file = "../../files/fj-23p.pdf"
output_path = Path("../../files/output")

pipeline = PPStructureV3()
output = pipeline.predict(input=input_file)

markdown_list = []
markdown_images = []

print(f"start process file {input_file}")
for res in output:
    md_info = res.markdown
    markdown_list.append(md_info)
    markdown_images.append(md_info.get("markdown_images", {}))

print(f"process {len(output)} pages")
markdown_texts = pipeline.concatenate_markdown_pages(markdown_list)

mkd_file_path = output_path / f"{Path(input_file).stem}.md"
mkd_file_path.parent.mkdir(parents=True, exist_ok=True)

print(f"open file {mkd_file_path}")
with open(mkd_file_path, "w", encoding="utf-8") as f:
    f.write(markdown_texts)

print(f"process {len(markdown_images)} images")
for item in markdown_images:
    if item:
        for path, image in item.items():
            file_path = output_path / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"output image to {file_path}")
            image.save(file_path)