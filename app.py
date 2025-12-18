"""
PDF 批注固化工具 - Streamlit Web App
====================================
将 PDF 中的批注固化到页面上，并生成汇总页

部署到 Streamlit Cloud:
1. 将代码推送到 GitHub
2. 访问 share.streamlit.io
3. 连接你的 GitHub 仓库
4. 选择 app.py 作为入口文件
"""

import streamlit as st
import fitz  # PyMuPDF
import io
from dataclasses import dataclass
from typing import List, Tuple

# 页面配置
st.set_page_config(
    page_title="PDF 批注固化工具",
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
    .stDownloadButton > button {
        width: 100%;
        background-color: #28a745;
        color: white;
    }
    .stDownloadButton > button:hover {
        background-color: #218838;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


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


def wrap_text(text: str, max_width: float, fontsize: float) -> List[str]:
    """将文本按宽度换行"""
    char_width = fontsize * 0.5
    chars_per_line = int(max_width / char_width)
    
    lines = []
    paragraphs = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    
    for para in paragraphs:
        if not para:
            lines.append("")
            continue
        
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
        lines = len(info.text_snippet) / (width / 5.5) + 1
        height += min(lines * 11 + 12, 75)
    
    if info.content:
        lines = len(info.content) / (width / 5.5) + info.content.count('\n') + info.content.count('\r') + 1
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
    
    # 编号
    num_str = str(info.number)
    num_x = x + circle_radius - len(num_str) * 2.5
    num_y = y + circle_radius + 3.5
    page.insert_text((num_x, num_y), num_str, fontsize=10, fontname="helv", color=(1, 1, 1))
    
    # 类型标签
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
    
    # 被标注的原文
    if info.text_snippet:
        snippet_text = info.text_snippet[:250]
        if len(info.text_snippet) > 250:
            snippet_text += "..."
        
        snippet_lines = wrap_text(f'"{snippet_text}"', width - 25, 8.5)
        snippet_height = len(snippet_lines) * 11 + 8
        snippet_height = min(snippet_height, 70)
        
        shape = page.new_shape()
        snippet_rect = fitz.Rect(content_x, current_y, x + width, current_y + snippet_height)
        shape.draw_rect(snippet_rect)
        shape.finish(color=None, fill=(0.94, 0.94, 0.94))
        shape.commit()
        
        shape = page.new_shape()
        shape.draw_rect(fitz.Rect(content_x, current_y, content_x + 2, current_y + snippet_height))
        shape.finish(color=None, fill=(0.6, 0.6, 0.6))
        shape.commit()
        
        text_y = current_y + 10
        max_lines = int((snippet_height - 8) / 11)
        for i, line in enumerate(snippet_lines[:max_lines]):
            page.insert_text((content_x + 6, text_y), line, fontsize=8.5, fontname="helv", color=(0.35, 0.35, 0.35))
            text_y += 11
        
        current_y += snippet_height + 6
    
    # 评论内容
    if info.content:
        content_text = info.content.strip()
        
        content_lines = wrap_text(content_text, width - 25, 9.5)
        content_height = len(content_lines) * 12 + 12
        content_height = min(content_height, 180)
        
        shape = page.new_shape()
        content_rect = fitz.Rect(content_x, current_y, x + width, current_y + content_height)
        shape.draw_rect(content_rect)
        shape.finish(color=(0.75, 0.82, 0.92), fill=(0.95, 0.97, 1), width=0.5)
        shape.commit()
        
        shape = page.new_shape()
        shape.draw_rect(fitz.Rect(content_x, current_y, content_x + 3, current_y + content_height))
        shape.finish(color=None, fill=(0.3, 0.5, 0.8))
        shape.commit()
        
        text_y = current_y + 12
        max_lines = int((content_height - 10) / 12)
        for i, line in enumerate(content_lines[:max_lines]):
            page.insert_text((content_x + 8, text_y), line, fontsize=9.5, fontname="helv", color=(0.15, 0.15, 0.25))
            text_y += 12
        
        current_y += content_height + 6
    else:
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
    
    # 标题
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
    """
    处理 PDF 文件，返回处理后的 PDF 字节和统计信息
    """
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
    
    # 保存到字节
    output_bytes = new_doc.tobytes(garbage=4, deflate=True)
    new_doc.close()
    src_doc.close()
    
    return output_bytes, stats


# ================== Streamlit UI ==================

def main():
    # 标题
    st.markdown('<h1 class="main-header">📄 PDF 批注固化工具</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">将 PDF 中的批注（高亮、便签、删除线等）固化到页面上，方便分享和打印</p>', unsafe_allow_html=True)
    
    # 文件上传
    uploaded_file = st.file_uploader(
        "上传 PDF 文件",
        type=["pdf"],
        help="支持带批注的 PDF 文件（来自 Adobe Acrobat、Mac Preview 等）"
    )
    
    if uploaded_file is not None:
        # 显示文件信息
        file_size = len(uploaded_file.getvalue()) / 1024 / 1024
        st.markdown(f"""
        <div class="info-box">
            <strong>📎 已选择文件：</strong> {uploaded_file.name}<br>
            <strong>📦 文件大小：</strong> {file_size:.2f} MB
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("")
        
        # 处理按钮
        if st.button("🚀 开始处理", type="primary", use_container_width=True):
            
            # 进度条
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(progress):
                progress_bar.progress(progress)
                status_text.text(f"正在处理... {int(progress * 100)}%")
            
            try:
                # 处理 PDF
                status_text.text("正在处理...")
                pdf_bytes = uploaded_file.getvalue()
                output_bytes, stats = process_pdf(pdf_bytes, update_progress)
                
                progress_bar.progress(1.0)
                status_text.text("处理完成！")
                
                # 显示统计信息
                st.markdown("---")
                st.subheader("📊 处理结果")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("总页数", stats["total_pages"])
                with col2:
                    st.metric("有批注的页数", stats["annotated_pages"])
                with col3:
                    st.metric("总批注数", stats["total_annotations"])
                
                # 批注类型统计
                if stats["annotation_types"]:
                    st.markdown("**批注类型分布：**")
                    type_cols = st.columns(min(len(stats["annotation_types"]), 4))
                    for i, (type_name, count) in enumerate(stats["annotation_types"].items()):
                        with type_cols[i % len(type_cols)]:
                            st.markdown(f"- {type_name}: **{count}**")
                
                st.markdown("---")
                
                # 下载按钮
                output_filename = uploaded_file.name.replace(".pdf", "_commented.pdf")
                
                st.download_button(
                    label="📥 下载处理后的 PDF",
                    data=output_bytes,
                    file_name=output_filename,
                    mime="application/pdf",
                    use_container_width=True
                )
                
                st.markdown("""
                <div class="success-box">
                    ✅ <strong>处理完成！</strong><br>
                    批注已固化到页面上，每个有批注的页面后都添加了汇总页。
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ 处理失败：{str(e)}")
                st.exception(e)
    
    # 使用说明
    st.markdown("---")
    with st.expander("📖 使用说明"):
        st.markdown("""
        ### 这个工具可以做什么？
        
        将 PDF 文件中的批注（annotations）固化到页面上，使其在任何 PDF 阅读器中都能看到。
        
        ### 支持的批注类型
        
        | 类型 | 说明 |
        |------|------|
        | 📝 Note | 便签批注 |
        | 🟡 Highlight | 高亮标记 |
        | ~~删除线~~ | 删除线标记 |
        | <u>下划线</u> | 下划线标记 |
        | ▲ Insert | 插入符号 |
        | □ Rectangle | 矩形框 |
        | ○ Ellipse | 椭圆框 |
        | ✏️ Drawing | 手绘墨迹 |
        
        ### 输出格式
        
        - 原文页面上保留视觉标记（高亮、删除线等）+ 红色编号
        - 每个有批注的页面后自动生成**汇总页**
        - 汇总页包含：批注编号、类型、被标注的原文、评论内容
        
        ### 隐私说明
        
        - 所有处理都在服务器内存中完成
        - 文件不会被存储
        - 处理完成后立即删除
        """)
    
    # 页脚
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #888;'>Made with ❤️ using Streamlit & PyMuPDF</p>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
