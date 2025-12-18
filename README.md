# PDF Annotation Flattener

📄 Flatten PDF annotations (highlights, notes, strikeouts, etc.) onto pages and generate summary pages for easy sharing.

将 PDF 中的批注（高亮、便签、删除线等）固化到页面上，并生成汇总页，方便分享和打印。

## ✨ Features

- ✅ **Chinese/CJK Support** - Automatically detects and renders Chinese, Japanese, Korean text / 自动检测并渲染中日韩文字
- ✅ **Two Output Modes** - PDF with summary pages OR JSON export / 两种输出模式
- ✅ Supports multiple annotation types: highlights, strikeouts, underlines, sticky notes, caret, rectangles, etc.
- ✅ Preserves visual marks on original pages with numbered markers
- ✅ Auto-generates summary pages after each annotated page
- ✅ Works with PDFs from Adobe Acrobat, Mac Preview, and other PDF editors
- ✅ Privacy-friendly: files are processed in memory and not stored

## 🚀 Usage

### Option 1: Web App (Online)

Visit the online app: **[Your Streamlit App URL]**

1. Upload your PDF
2. Choose output format:
   - **PDF with Summary Pages** - Visual PDF with annotations flattened
   - **JSON Only** - Structured data export for further processing
3. Download the result

### Option 2: Command Line (Local)

For batch processing or offline use.

#### Installation

```bash
pip install pymupdf
```

#### Basic Usage (PDF Output)

```bash
# Process a PDF (output: input_flattened.pdf)
python flatten_pdf.py paper.pdf

# Specify output filename
python flatten_pdf.py paper.pdf output.pdf

# Or use -o flag
python flatten_pdf.py paper.pdf -o output.pdf

# Quiet mode (no console output)
python flatten_pdf.py paper.pdf -q
```

#### JSON Export Mode

```bash
# Export annotations as JSON (output: paper_annotations.json)
python flatten_pdf.py paper.pdf --json

# Specify JSON output filename
python flatten_pdf.py paper.pdf --json -o annotations.json

# Quiet mode
python flatten_pdf.py paper.pdf --json -q
```

#### Batch Processing

```bash
# Process all PDFs in current directory
for f in *.pdf; do python flatten_pdf.py "$f"; done

# Export all as JSON
for f in *.pdf; do python flatten_pdf.py "$f" --json; done
```

### Option 3: Run Web App Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py

# Open browser at http://localhost:8501
```

## 📋 Supported Annotation Types

| Type | Icon | Description |
|------|------|-------------|
| Note | 📝 | Sticky notes / 便签批注 |
| Highlight | 🟡 | Highlighted text / 高亮 |
| Strikeout | ~~text~~ | Strikethrough / 删除线 |
| Underline | <u>text</u> | Underlined text / 下划线 |
| Insert | ▲ | Caret / 插入符号 |
| Rectangle | □ | Rectangle markup / 矩形框 |
| Ellipse | ○ | Circle markup / 椭圆 |
| Line | / | Line markup / 线条 |
| Drawing | ✏️ | Ink annotations / 手绘 |
| Text Box | 📄 | Free text / 文本框 |

## 📁 Project Structure

```
pdf-annotation-flattener/
├── app.py              # Streamlit web application
├── flatten_pdf.py      # Command line tool
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## 🖼️ Output Formats

### PDF Mode (Default)

**Original Page:**
- Visual marks (highlights, strikeouts, etc.) are preserved
- Red numbered circles are added next to each annotation

**Summary Page (auto-generated):**
- Number: Corresponds to the marker on the original page
- Type: Annotation type (Highlight, Note, Strikeout, etc.)
- Quoted Text: The text that was annotated (gray background)
- Comment: The reviewer's comment (blue background) - supports Chinese / 支持中文

### JSON Mode (`--json`)

```json
{
  "filename": "paper.pdf",
  "exported_at": "2025-12-18T15:30:00",
  "total_pages": 28,
  "annotated_pages": 10,
  "total_annotations": 56,
  "pages": [
    {
      "page": 1,
      "annotation_count": 6,
      "annotations": [
        {
          "number": 1,
          "type": "Highlight",
          "quoted_text": "original text that was highlighted",
          "comment": "This needs revision / 这里需要修改",
          "author": "Reviewer A",
          "position": {"x0": 72.5, "y0": 120.3, "x1": 540.2, "y1": 135.8}
        }
      ]
    }
  ]
}
```

**JSON Fields:**
- `quoted_text`: The annotated text (null if not available)
- `comment`: Reviewer's comment (null if no comment)
- `author`: Annotation author (null if not specified)
- `position`: Bounding box coordinates (x0, y0, x1, y1)

## 🔧 Requirements

- Python 3.8+
- PyMuPDF (fitz) >= 1.23.0
- Streamlit >= 1.28.0 (for web app only)

## 🌐 Deploy Your Own Instance

### Deploy to Streamlit Cloud (Free)

1. Fork this repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click "New app" and select your forked repo
5. Set `app.py` as the main file
6. Click "Deploy"

Your app will be live in ~2 minutes!

## 🔒 Privacy

- **Web App**: Files are processed in server memory and immediately discarded after processing. No files are stored.
- **Command Line**: All processing happens locally on your machine.

## 🌍 Language Support

The tool automatically detects and properly renders:
- English
- Chinese (Simplified & Traditional) / 简体中文、繁体中文
- Japanese / 日本語
- Korean / 한국어

## 📄 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

Made with ❤️ using [PyMuPDF](https://pymupdf.readthedocs.io/) and [Streamlit](https://streamlit.io/)