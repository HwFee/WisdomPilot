# -*- coding: utf-8 -*-
"""向开题报告 docx 插入配图（居中图片 + 图题），另存为新文件。"""
import docx
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

SRC = r"C:\Users\17445\Desktop\开题报告和申请表\本科综合设计（论文）开题报告-何树杰-2024211372.docx"
OUT = r"C:\Users\17445\Desktop\开题报告和申请表\本科综合设计（论文）开题报告-何树杰-2024211372-插图版.docx"
IMG = r"C:\Users\17445\Desktop\WisdomPilot\docs\开题报告配图"

# (锚点段前缀, 图片文件名, 图题, 图宽inch)
FIGURES = [
    ("（1）基于事件溯源的个性化掌握度建模。",
     "图4_HLR遗忘曲线_精确版.png", "图1  HLR 半衰期回归记忆模型遗忘曲线", 5.6),
    ("（1）基于事件溯源的个性化掌握度建模。",
     "图3_四级掌握状态机图.png", "图2  四级掌握状态机", 5.6),
    ("系统采用前后端分离架构。",
     "图1_系统总体架构图.png", "图3  系统总体架构", 5.9),
    ("在数据设计上，",
     "图5_掌握度事件溯源架构图.png", "图4  掌握度事件溯源架构", 5.6),
    ("个性化调度流程为：",
     "图2_个性化调度流程图.png", "图5  个性化训练调度流程", 5.6),
]


def set_ea_font(run, name):
    """设置中文字体（eastAsia）。"""
    rpr = run._r.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn("w:eastAsia"), name)


def insert_paragraph_after(paragraph):
    """在给定段后新增一个空段落，返回新 Paragraph 对象。"""
    new_p = paragraph._p.makeelement(qn("w:p"), {})
    paragraph._p.addnext(new_p)  # addnext 返回 None，需先创建元素再插入
    return Paragraph(new_p, paragraph._parent)


def add_figure_after(anchor_para, img_path, caption, width_in):
    # 图片段（居中）
    p_img = insert_paragraph_after(anchor_para)
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p_img.paragraph_format
    pf.space_before = Pt(6)
    pf.space_after = Pt(2)
    run = p_img.add_run()
    run.add_picture(img_path, width=Inches(width_in))
    # 图题段（居中，宋体五号）
    p_cap = insert_paragraph_after(p_img)
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p_cap.paragraph_format
    pf.space_before = Pt(2)
    pf.space_after = Pt(12)
    r = p_cap.add_run(caption)
    r.font.size = Pt(10.5)
    r.font.name = "宋体"
    set_ea_font(r, "宋体")


d = docx.Document(SRC)
paras = list(d.paragraphs)

# 收集锚点 Paragraph 对象（按文本前缀匹配，唯一）
anchors = {}
for p in paras:
    t = p.text.strip()
    for prefix in [f[0] for f in FIGURES]:
        if t.startswith(prefix) and prefix not in anchors:
            anchors[prefix] = p

missing = [f[0] for f in FIGURES if f[0] not in anchors]
if missing:
    raise SystemExit(f"锚点未找到: {missing}")

# 插入（用对象引用，不受索引位移影响）
for prefix, fname, caption, width in FIGURES:
    add_figure_after(anchors[prefix],
                     f"{IMG}\\{fname}", caption, width)
    print("inserted:", fname, "->", caption)

d.save(OUT)
print("saved:", OUT)
