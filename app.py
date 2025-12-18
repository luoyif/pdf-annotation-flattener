"""
PDF Annotation Flattener - Streamlit Web App
=============================================
将 PDF 中的批注固化到页面上，并生成汇总页
支持中文批注内容

部署到 Streamlit Cloud:
1. 将代码推送到 GitHub
2. 访问 share.streamlit.io
3. 连接你的 GitHub 仓库
4. 选择 app.py 作为入口文件
"""

import streamlit as st
import fitz  # PyMuPDF
import re
from dataclasses import dataclass
from typing import List, Tuple

# 页面配置
st.set_page_config(
    page_title="PDF Annotation Flattener",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 自定义样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        color: #1e3a5f;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #e7f3ff;
        border: 1px solid #b8daff;
        color: #004085;
    }
</style>
""", unsafe_allow_html=True)


# ================== 中文支持 & 混合字体渲染 ==================

def is_cjk_char(char: str) -> bool:
    """检测单个字符是否为中日韩字符"""
    if len(char) != 1:
        return False
    code = ord(char)
    return (
        0x4e00 <= code <= 0x9fff or    # CJK Unified Ideographs
        0x3400 <= code <= 0x4dbf or    # CJK Extension A
        0x3000 <= code <= 0x303f or    # CJK Symbols and Punctuation
        0xff00 <= code <= 0xffef or    # Fullwidth Forms
        0x3040 <= code <= 0x309f or    # Hiragana
        0x30a0 <= code <= 0x30ff       # Katakana
    )


def contains_cjk(text: str) -> bool:
    """检测文本是否包含中日韩字符"""
    return any(is_cjk_char(c) for c in text)


def split_text_by_script(text: str) -> list:
    """将文本按中英文分段，返回 [(text, is_cjk), ...]"""
    if not text:
        return []
    
    segments = []
    current_segment = ""
    current_is_cjk = None
    
    for char in text:
        char_is_cjk = is_cjk_char(char)
        
        if current_is_cjk is None:
            current_is_cjk = char_is_cjk
            current_segment = char
        elif char_is_cjk == current_is_cjk:
            current_segment += char
        else:
            if current_segment:
                segments.append((current_segment, current_is_cjk))
            current_segment = char
            current_is_cjk = char_is_cjk
    
    if current_segment:
        segments.append((current_segment, current_is_cjk))
    
    return segments


def insert_mixed_text(page, pos: tuple, text: str, fontsize: float, color: tuple) -> float:
    """
    插入中英文混合文本，返回文本结束的 x 坐标
    中文用 china-ss 字体，英文用 helv 字体
    """
    x, y = pos
    segments = split_text_by_script(text)
    
    for idx, (segment_text, is_cjk) in enumerate(segments):
        fontname = "china-ss" if is_cjk else "helv"
        page.insert_text((x, y), segment_text, fontsize=fontsize, fontname=fontname, color=color)
        
        # 计算这段文字的宽度，移动 x 坐标
        # 中文字符宽度约等于字号，英文约为字号的 0.52
        if is_cjk:
            x += len(segment_text) * fontsize * 1.0
        else:
            x += len(segment_text) * fontsize * 0.52
        
        # 中英文切换时添加小间距
        if idx < len(segments) - 1:
            next_is_cjk = segments[idx + 1][1]
            if is_cjk != next_is_cjk:
                x += fontsize * 0.1  # 切换时加一点间距
    
    return x


# ================== 数据结构 ==================

@dataclass
class AnnotationInfo:
    """批注信息"""
    number: int
    annot_type: str
    content: str
    page_num: int
    rect: fitz.Rect
    color: Tuple[float, float, float]
    text_snippet: str = ""
    author: str = ""


def get_type_label(annot_type: str) -> str:
    """获取批注类型标签"""
    type_labels = {
        "Text": "Note",
        "FreeText": "Text Box",
        "Highlight": "Highlight",
        "StrikeOut": "Strikeout",
        "Underline": "Underline",
        "Square": "Rectangle",
        "Rectangle": "Rectangle",
        "Circle": "Ellipse",
        "Ellipse": "Ellipse",
        "Line": "Line",
        "Polygon": "Polygon",
        "PolyLine": "Polyline",
        "Caret": "Insert",
        "Ink": "Drawing",
        "Popup": "Popup",
    }
    return type_labels.get(annot_type, annot_type)


def get_type_color(annot_type: str) -> Tuple[float, float, float]:
    """获取批注类型颜色"""
    type_colors = {
        "Text": (0.85, 0.45, 0.1),
        "FreeText": (0.25, 0.65, 0.35),
        "Highlight": (0.92, 0.75, 0.15),
        "StrikeOut": (0.85, 0.25, 0.25),
        "Underline": (0.25, 0.45, 0.85),
        "Square": (0.65, 0.35, 0.65),
        "Rectangle": (0.65, 0.35, 0.65),
        "Circle": (0.35, 0.65, 0.65),
        "Caret": (0.25, 0.75, 0.35),
        "Ink": (0.45, 0.45, 0.75),
    }
    return type_colors.get(annot_type, (0.5, 0.5, 0.5))


def wrap_text(text: str, max_width: float, fontsize: float, has_cjk: bool = False) -> List[str]:
    """将文本按宽度换行"""
    # 中文字符宽度约等于字号，英文约为 0.52
    if has_cjk:
        char_width = fontsize * 1.0
    else:
        char_width = fontsize * 0.52
    chars_per_line = int(max_width / char_width)
    
    lines = []
    paragraphs = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    
    for para in paragraphs:
        if not para:
            lines.append("")
            continue
        
        if has_cjk:
            # 对于中文文本，按字符数换行
            current_line = ""
            for char in para:
                if len(current_line) >= chars_per_line:
                    lines.append(current_line)
                    current_line = char
                else:
                    current_line += char
            if current_line:
                lines.append(current_line)
        else:
            # 对于英文文本，按单词换行
            words = para.split(' ')
            current_line = ""
            
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if len(test_line) <= chars_per_line:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    while len(word) > chars_per_line:
                        lines.append(word[:chars_per_line])
                        word = word[chars_per_line:]
                    current_line = word
            
            if current_line:
                lines.append(current_line)
    
    return lines


def calc_text_width(text: str, fontsize: float) -> float:
    """计算混合文本的实际宽度"""
    width = 0
    for char in text:
        if is_cjk_char(char):
            width += fontsize * 1.0
        else:
            width += fontsize * 0.52
    return width


def wrap_text_mixed(text: str, max_width: float, fontsize: float) -> List[str]:
    """将中英文混合文本按宽度换行"""
    lines = []
    paragraphs = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    
    for para in paragraphs:
        if not para:
            lines.append("")
            continue
        
        current_line = ""
        current_width = 0
        
        i = 0
        while i < len(para):
            char = para[i]
            
            # 计算这个字符的宽度 (中文=1.0, 英文=0.52)
            if is_cjk_char(char):
                char_width = fontsize * 1.0
            else:
                char_width = fontsize * 0.52
            
            # 检查是否需要换行
            if current_width + char_width > max_width:
                if current_line:
                    lines.append(current_line)
                current_line = char
                current_width = char_width
            else:
                current_line += char
                current_width += char_width
            
            i += 1
        
        if current_line:
            lines.append(current_line)
    
    return lines


def render_annotation_mark(page, annot, number: int):
    """在页面上渲染批注标记"""
    annot_type = annot.type[1]
    rect = annot.rect
    colors = annot.colors
    stroke_color = colors.get("stroke", (1, 0, 0))
    fill_color = colors.get("fill", (1, 1, 0))
    
    if annot_type == "Highlight":
        quads = annot.vertices
        if quads:
            shape = page.new_shape()
            for i in range(0, len(quads), 4):
                if i + 3 < len(quads):
                    quad = fitz.Quad(quads[i:i+4])
                    shape.draw_quad(quad)
            color = fill_color if fill_color else (1, 1, 0)
            shape.finish(color=None, fill=color, fill_opacity=0.35)
            shape.commit()
        add_number_marker(page, rect.x1, rect.y0, number)
    
    elif annot_type == "StrikeOut":
        quads = annot.vertices
        if quads:
            shape = page.new_shape()
            for i in range(0, len(quads), 4):
                if i + 3 < len(quads):
                    q = quads[i:i+4]
                    y_mid = (q[0][1] + q[2][1]) / 2
                    shape.draw_line((q[0][0], y_mid), (q[1][0], y_mid))
            shape.finish(color=stroke_color if stroke_color else (1, 0, 0), width=1.5)
            shape.commit()
        add_number_marker(page, rect.x1, rect.y0, number)
    
    elif annot_type == "Underline":
        quads = annot.vertices
        if quads:
            shape = page.new_shape()
            for i in range(0, len(quads), 4):
                if i + 3 < len(quads):
                    q = quads[i:i+4]
                    shape.draw_line((q[2][0], q[2][1] + 1), (q[3][0], q[3][1] + 1))
            shape.finish(color=stroke_color if stroke_color else (0, 0, 1), width=1)
            shape.commit()
        add_number_marker(page, rect.x1, rect.y1, number)
    
    elif annot_type in ["Square", "Rectangle"]:
        shape = page.new_shape()
        shape.draw_rect(rect)
        shape.finish(color=stroke_color if stroke_color else (1, 0, 0), width=1.5)
        shape.commit()
        add_number_marker(page, rect.x1, rect.y0, number)
    
    elif annot_type in ["Circle", "Ellipse"]:
        shape = page.new_shape()
        shape.draw_oval(rect)
        shape.finish(color=stroke_color if stroke_color else (1, 0, 0), width=1.5)
        shape.commit()
        add_number_marker(page, rect.x1, rect.y0, number)
    
    elif annot_type == "Text":
        add_number_marker(page, rect.x0, rect.y0, number, size=12)
    
    elif annot_type == "FreeText":
        shape = page.new_shape()
        shape.draw_rect(rect)
        shape.finish(color=(0.8, 0.4, 0), width=1, dashes="[2 2]")
        shape.commit()
        add_number_marker(page, rect.x0 - 2, rect.y0, number)
    
    elif annot_type == "Caret":
        shape = page.new_shape()
        x, y = rect.x0, rect.y0
        shape.draw_polyline([(x, y + 5), (x + 4, y), (x + 8, y + 5)])
        shape.finish(color=(0, 0.6, 0), fill=(0.6, 1, 0.6), width=0.5, closePath=True)
        shape.commit()
        add_number_marker(page, x + 10, y, number)
    
    elif annot_type == "Ink":
        paths = annot.vertices
        if paths:
            shape = page.new_shape()
            for path in paths:
                if len(path) >= 2:
                    shape.draw_polyline(path)
            shape.finish(color=stroke_color if stroke_color else (0, 0, 1), width=1)
            shape.commit()
        add_number_marker(page, rect.x1, rect.y0, number)
    
    elif annot_type == "Line":
        vertices = annot.vertices
        if vertices and len(vertices) >= 2:
            shape = page.new_shape()
            shape.draw_line(vertices[0], vertices[1])
            shape.finish(color=stroke_color if stroke_color else (1, 0, 0), width=1.5)
            shape.commit()
        add_number_marker(page, rect.x1, rect.y0, number)
    
    else:
        add_number_marker(page, rect.x0, rect.y0, number)


def add_number_marker(page, x: float, y: float, number: int, size: int = 10):
    """添加编号标记"""
    page_rect = page.rect
    x = min(max(x, 8), page_rect.width - 12)
    y = min(max(y, 8), page_rect.height - 12)
    
    radius = size / 2 + 2
    shape = page.new_shape()
    center = fitz.Point(x + radius, y + radius)
    shape.draw_circle(center, radius)
    shape.finish(color=(0.8, 0, 0), fill=(1, 0.3, 0.3), width=0.5)
    shape.commit()
    
    num_str = str(number)
    num_x = x + radius - len(num_str) * 2.5
    num_y = y + radius + 3
    page.insert_text((num_x, num_y), num_str, fontsize=size - 2, fontname="helv", color=(1, 1, 1))


def estimate_entry_height(info: AnnotationInfo, width: float) -> float:
    """估算批注条目需要的高度"""
    height = 30
    
    if info.text_snippet:
        has_cjk = contains_cjk(info.text_snippet)
        char_factor = 1.0 if has_cjk else 0.52
        lines = len(info.text_snippet) / (width / (8.5 * char_factor)) + 1
        height += min(lines * 11 + 12, 75)
    
    if info.content:
        has_cjk = contains_cjk(info.content)
        char_factor = 1.0 if has_cjk else 0.52
        lines = len(info.content) / (width / (9.5 * char_factor)) + info.content.count('\n') + info.content.count('\r') + 1
        height += min(lines * 12 + 14, 200)
    else:
        height += 25
    
    return height + 15


def render_annotation_entry(page, info: AnnotationInfo, x: float, y: float, width: float) -> float:
    """渲染单个批注条目"""
    
    # 编号圆圈
    circle_radius = 9
    shape = page.new_shape()
    shape.draw_circle(fitz.Point(x + circle_radius, y + circle_radius), circle_radius)
    shape.finish(color=(0.7, 0.1, 0.1), fill=(0.9, 0.25, 0.25), width=0.5)
    shape.commit()
    
    # 编号 - 数字用英文字体
    num_str = str(info.number)
    num_x = x + circle_radius - len(num_str) * 2.5
    num_y = y + circle_radius + 3.5
    page.insert_text((num_x, num_y), num_str, fontsize=10, fontname="helv", color=(1, 1, 1))
    
    # 类型标签 - 英文标签用英文字体
    type_x = x + circle_radius * 2 + 8
    type_label = get_type_label(info.annot_type)
    type_color = get_type_color(info.annot_type)
    type_width = len(type_label) * 6.5 + 12
    
    shape = page.new_shape()
    type_rect = fitz.Rect(type_x, y + 1, type_x + type_width, y + 17)
    shape.draw_rect(type_rect)
    shape.finish(color=None, fill=type_color)
    shape.commit()
    
    label_x = type_x + 6
    label_y = y + 13
    page.insert_text((label_x, label_y), type_label, fontsize=9, fontname="helv", color=(1, 1, 1))
    
    content_x = x + circle_radius * 2 + 8
    current_y = y + 24
    
    # 被标注的原文 - 混合字体渲染
    if info.text_snippet:
        snippet_text = info.text_snippet[:250]
        if len(info.text_snippet) > 250:
            snippet_text += "..."
        
        has_cjk = contains_cjk(snippet_text)
        
        snippet_lines = wrap_text_mixed(f'"{snippet_text}"', width - 25, 8.5)
        snippet_height = len(snippet_lines) * 11 + 8
        snippet_height = min(snippet_height, 70)
        
        # 灰色背景
        shape = page.new_shape()
        snippet_rect = fitz.Rect(content_x, current_y, x + width, current_y + snippet_height)
        shape.draw_rect(snippet_rect)
        shape.finish(color=None, fill=(0.94, 0.94, 0.94))
        shape.commit()
        
        # 左边框
        shape = page.new_shape()
        shape.draw_rect(fitz.Rect(content_x, current_y, content_x + 2, current_y + snippet_height))
        shape.finish(color=None, fill=(0.6, 0.6, 0.6))
        shape.commit()
        
        # 文字 - 使用混合字体渲染
        text_y = current_y + 10
        max_lines = int((snippet_height - 8) / 11)
        for i, line in enumerate(snippet_lines[:max_lines]):
            insert_mixed_text(page, (content_x + 6, text_y), line, 8.5, (0.35, 0.35, 0.35))
            text_y += 11
        
        current_y += snippet_height + 6
    
    # 评论内容 - 混合字体渲染
    if info.content:
        content_text = info.content.strip()
        
        has_cjk = contains_cjk(content_text)
        
        content_lines = wrap_text_mixed(content_text, width - 25, 9.5)
        content_height = len(content_lines) * 12 + 12
        content_height = min(content_height, 180)
        
        # 浅蓝色背景
        shape = page.new_shape()
        content_rect = fitz.Rect(content_x, current_y, x + width, current_y + content_height)
        shape.draw_rect(content_rect)
        shape.finish(color=(0.75, 0.82, 0.92), fill=(0.95, 0.97, 1), width=0.5)
        shape.commit()
        
        # 左边蓝色装饰条
        shape = page.new_shape()
        shape.draw_rect(fitz.Rect(content_x, current_y, content_x + 3, current_y + content_height))
        shape.finish(color=None, fill=(0.3, 0.5, 0.8))
        shape.commit()
        
        # 文字 - 使用混合字体渲染
        text_y = current_y + 12
        max_lines = int((content_height - 10) / 12)
        for i, line in enumerate(content_lines[:max_lines]):
            insert_mixed_text(page, (content_x + 8, text_y), line, 9.5, (0.15, 0.15, 0.25))
            text_y += 12
        
        current_y += content_height + 6
    else:
        # 无评论提示
        shape = page.new_shape()
        no_comment_rect = fitz.Rect(content_x, current_y, content_x + 85, current_y + 18)
        shape.draw_rect(no_comment_rect)
        shape.finish(color=None, fill=(0.92, 0.92, 0.92))
        shape.commit()
        
        page.insert_text((content_x + 8, current_y + 13), "(no comment)", fontsize=8.5, fontname="helv", color=(0.5, 0.5, 0.5))
        current_y += 22
    
    # 底部分隔线
    shape = page.new_shape()
    shape.draw_line((x, current_y), (x + width, current_y))
    shape.finish(color=(0.88, 0.88, 0.88), width=0.3)
    shape.commit()
    
    return current_y + 3


def create_summary_page(doc, annotations: List[AnnotationInfo], page_num: int, page_rect: fitz.Rect):
    """创建批注汇总页"""
    summary_page = doc.new_page(width=page_rect.width, height=page_rect.height)
    
    margin_left = 45
    margin_right = 45
    margin_top = 55
    margin_bottom = 40
    
    content_width = page_rect.width - margin_left - margin_right
    current_y = margin_top
    
    # 标题背景
    shape = summary_page.new_shape()
    shape.draw_rect(fitz.Rect(0, 0, page_rect.width, current_y + 35))
    shape.finish(color=None, fill=(0.25, 0.35, 0.55))
    shape.commit()
    
    # 标题 - 英文标题用英文字体
    title = f"Page {page_num} - Comments Summary ({len(annotations)} items)"
    title_width = len(title) * 7
    title_x = (page_rect.width - title_width) / 2
    summary_page.insert_text((title_x, current_y + 22), title, fontsize=14, fontname="helv", color=(1, 1, 1))
    
    current_y += 45
    
    # 分隔线
    shape = summary_page.new_shape()
    shape.draw_line((margin_left, current_y), (page_rect.width - margin_right, current_y))
    shape.finish(color=(0.8, 0.8, 0.8), width=0.5)
    shape.commit()
    
    current_y += 12
    
    # 渲染每个批注
    for info in annotations:
        needed_height = estimate_entry_height(info, content_width)
        
        if current_y + needed_height > page_rect.height - margin_bottom:
            summary_page = doc.new_page(width=page_rect.width, height=page_rect.height)
            current_y = margin_top
            
            shape = summary_page.new_shape()
            shape.draw_rect(fitz.Rect(0, 0, page_rect.width, current_y + 25))
            shape.finish(color=None, fill=(0.35, 0.45, 0.65))
            shape.commit()
            
            cont_title = f"Page {page_num} - Comments Summary (cont.)"
            cont_title_x = (page_rect.width - len(cont_title) * 6) / 2
            summary_page.insert_text((cont_title_x, current_y + 17), cont_title, fontsize=11, fontname="helv", color=(1, 1, 1))
            current_y += 35
        
        current_y = render_annotation_entry(summary_page, info, margin_left, current_y, content_width)
        current_y += 8


def process_pdf(pdf_bytes: bytes, progress_callback=None) -> Tuple[bytes, dict]:
    """处理 PDF 文件，返回处理后的 PDF 字节和统计信息"""
    src_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    new_doc = fitz.open()
    
    stats = {
        "total_pages": len(src_doc),
        "annotated_pages": 0,
        "total_annotations": 0,
        "annotation_types": {}
    }
    
    for page_num in range(len(src_doc)):
        if progress_callback:
            progress_callback((page_num + 1) / len(src_doc))
        
        src_page = src_doc[page_num]
        new_doc.insert_pdf(src_doc, from_page=page_num, to_page=page_num)
        new_page = new_doc[-1]
        
        annots = list(src_page.annots()) if src_page.annots() else []
        
        if not annots:
            continue
        
        stats["annotated_pages"] += 1
        annotations_info: List[AnnotationInfo] = []
        
        for idx, annot in enumerate(annots, 1):
            annot_type = annot.type[1]
            content = annot.info.get("content", "").strip()
            author = annot.info.get("title", "")
            rect = annot.rect
            colors = annot.colors
            stroke_color = colors.get("stroke", (1, 0, 0))
            fill_color = colors.get("fill", (1, 1, 0))
            
            # 统计批注类型
            type_label = get_type_label(annot_type)
            stats["annotation_types"][type_label] = stats["annotation_types"].get(type_label, 0) + 1
            
            text_snippet = ""
            try:
                if annot.vertices and len(annot.vertices) >= 4:
                    all_points = annot.vertices
                    min_x = min(p[0] for p in all_points)
                    min_y = min(p[1] for p in all_points)
                    max_x = max(p[0] for p in all_points)
                    max_y = max(p[1] for p in all_points)
                    clip_rect = fitz.Rect(min_x, min_y, max_x, max_y)
                    text_snippet = src_page.get_text("text", clip=clip_rect).strip()
                elif rect.is_valid and not rect.is_empty:
                    text_snippet = src_page.get_text("text", clip=rect).strip()
            except:
                pass
            
            if text_snippet:
                text_snippet = " ".join(text_snippet.split())[:300]
            
            info = AnnotationInfo(
                number=idx,
                annot_type=annot_type,
                content=content,
                page_num=page_num + 1,
                rect=rect,
                color=stroke_color if stroke_color else fill_color,
                text_snippet=text_snippet,
                author=author
            )
            annotations_info.append(info)
            render_annotation_mark(new_page, annot, idx)
        
        for annot in list(new_page.annots()) if new_page.annots() else []:
            new_page.delete_annot(annot)
        
        if annotations_info:
            create_summary_page(new_doc, annotations_info, page_num + 1, src_page.rect)
            stats["total_annotations"] += len(annotations_info)
    
    output_bytes = new_doc.tobytes(garbage=4, deflate=True)
    new_doc.close()
    src_doc.close()
    
    return output_bytes, stats


# ================== Streamlit UI ==================

def main():
    st.markdown('<h1 class="main-header">📄 PDF Annotation Flattener</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Flatten PDF annotations onto pages with summary / 将 PDF 批注固化到页面上</p>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Upload PDF file / 上传 PDF 文件",
        type=["pdf"],
        help="Supports annotated PDFs from Adobe Acrobat, Mac Preview, etc."
    )
    
    if uploaded_file is not None:
        file_size = len(uploaded_file.getvalue()) / 1024 / 1024
        st.markdown(f"""
        <div class="info-box">
            <strong>📎 File:</strong> {uploaded_file.name}<br>
            <strong>📦 Size:</strong> {file_size:.2f} MB
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("")
        
        if st.button("🚀 Process / 开始处理", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(progress):
                progress_bar.progress(progress)
                status_text.text(f"Processing... {int(progress * 100)}%")
            
            try:
                status_text.text("Processing...")
                pdf_bytes = uploaded_file.getvalue()
                output_bytes, stats = process_pdf(pdf_bytes, update_progress)
                
                progress_bar.progress(1.0)
                status_text.text("Done! ✅")
                
                st.markdown("---")
                st.subheader("📊 Results / 处理结果")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Pages / 总页数", stats["total_pages"])
                with col2:
                    st.metric("Annotated Pages / 有批注页数", stats["annotated_pages"])
                with col3:
                    st.metric("Total Annotations / 总批注数", stats["total_annotations"])
                
                if stats["annotation_types"]:
                    st.markdown("**Annotation Types / 批注类型:**")
                    type_cols = st.columns(min(len(stats["annotation_types"]), 4))
                    for i, (type_name, count) in enumerate(stats["annotation_types"].items()):
                        with type_cols[i % len(type_cols)]:
                            st.markdown(f"- {type_name}: **{count}**")
                
                st.markdown("---")
                
                output_filename = uploaded_file.name.replace(".pdf", "_flattened.pdf")
                
                st.download_button(
                    label="📥 Download / 下载处理后的 PDF",
                    data=output_bytes,
                    file_name=output_filename,
                    mime="application/pdf",
                    use_container_width=True
                )
                
                st.markdown("""
                <div class="success-box">
                    ✅ <strong>Done!</strong> Annotations have been flattened with summary pages added.<br>
                    ✅ <strong>完成！</strong> 批注已固化到页面上，并添加了汇总页。
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.exception(e)
    
    st.markdown("---")
    with st.expander("📖 Help / 使用说明"):
        st.markdown("""
        ### What does this tool do? / 这个工具做什么？
        
        Flattens PDF annotations onto pages so they're visible in any PDF reader.
        
        将 PDF 中的批注固化到页面上，使其在任何 PDF 阅读器中都能看到。
        
        ### Supported Annotation Types / 支持的批注类型
        
        | Type | Description |
        |------|-------------|
        | 📝 Note | Sticky notes / 便签批注 |
        | 🟡 Highlight | Highlighted text / 高亮 |
        | ~~Strikeout~~ | Strikethrough / 删除线 |
        | <u>Underline</u> | Underlined text / 下划线 |
        | ▲ Insert | Caret / 插入符号 |
        | □ Rectangle | Rectangle markup / 矩形框 |
        | ○ Ellipse | Circle markup / 椭圆 |
        | ✏️ Drawing | Ink annotations / 手绘 |
        
        ### Output / 输出格式
        
        - Original pages with visual marks + numbered markers
        - Summary page after each annotated page (supports Chinese / 支持中文)
        
        ### Privacy / 隐私说明
        
        Files are processed in memory and not stored. / 文件在内存中处理，不会被存储。
        """)
    
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #888;'>Made with ❤️ using Streamlit & PyMuPDF</p>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()