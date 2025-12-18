# PDF Annotation Flattener

📄 将 PDF 中的批注（高亮、便签、删除线等）固化到页面上，并生成汇总页，方便分享和打印。

Flatten PDF annotations (highlights, notes, strikeouts, etc.) onto pages and generate summary pages for easy sharing.

## ✨ Features

- ✅ Supports multiple annotation types: highlights, strikeouts, underlines, sticky notes, caret, rectangles, etc.
- ✅ Preserves visual marks on original pages with numbered markers
- ✅ Auto-generates summary pages after each annotated page
- ✅ Works with PDFs from Adobe Acrobat, Mac Preview, and other PDF editors
- ✅ Privacy-friendly: files are processed in memory and not stored

## 🚀 Usage

### Option 1: Web App (Online)

Visit the online app: **[Your Streamlit App URL]**

Simply upload your PDF and download the processed file.

### Option 2: Command Line (Local)

For batch processing or offline use.

#### Installation

```bash
pip install pymupdf
```

#### Basic Usage

```bash
# Process a PDF (output: input_commented.pdf)
python flatten_pdf.py paper.pdf

# Specify output filename
python flatten_pdf.py paper.pdf output.pdf

# Or use -o flag
python flatten_pdf.py paper.pdf -o output.pdf

# Quiet mode (no console output)
python flatten_pdf.py paper.pdf -q
```

#### Examples

```bash
# Process a research paper
python flatten_pdf.py research_paper.pdf

# Process with custom output name
python flatten_pdf.py draft.pdf final_with_comments.pdf

# Batch process multiple files
for f in *.pdf; do python flatten_pdf.py "$f"; done
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
| Note | 📝 | Sticky notes / comments |
| Highlight | 🟡 | Highlighted text |
| Strikeout | ~~text~~ | Strikethrough text |
| Underline | <u>text</u> | Underlined text |
| Insert | ▲ | Caret / insertion point |
| Rectangle | □ | Rectangle markup |
| Ellipse | ○ | Circle / ellipse markup |
| Line | / | Line markup |
| Drawing | ✏️ | Freehand ink annotations |
| Text Box | 📄 | Free text annotations |

## 📁 Project Structure

```
pdf-annotation-flattener/
├── app.py              # Streamlit web application
├── flatten_pdf.py      # Command line tool
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## 🖼️ Output Format

### Original Page
- Visual marks (highlights, strikeouts, etc.) are preserved
- Red numbered circles are added next to each annotation

### Summary Page (auto-generated after each annotated page)
- **Number**: Corresponds to the marker on the original page
- **Type**: Annotation type (Highlight, Note, Strikeout, etc.)
- **Quoted Text**: The text that was annotated (gray background)
- **Comment**: The reviewer's comment (blue background)

Example:
```
┌─────────────────────────────────────┐
│  Page 1 - Comments Summary (5 items) │
├─────────────────────────────────────┤
│ ① [Highlight]                        │
│   "original text that was highlighted"│
│   This needs to be revised...        │
├─────────────────────────────────────┤
│ ② [Strikeout]                        │
│   "text that was struck out"         │
│   (no comment)                       │
└─────────────────────────────────────┘
```

## 🔧 Requirements

- Python 3.8+
- PyMuPDF (fitz) >= 1.23.0
- Streamlit >= 1.28.0 (for web app only)

## 📦 Installation for Development

```bash
# Clone the repository
git clone https://github.com/yourusername/pdf-annotation-flattener.git
cd pdf-annotation-flattener

# Install dependencies
pip install -r requirements.txt

# Run tests
python flatten_pdf.py test.pdf
```

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

## 📄 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📮 Feedback

If you encounter any issues or have suggestions, please open an issue on GitHub.

---

Made with ❤️ using [PyMuPDF](https://pymupdf.readthedocs.io/) and [Streamlit](https://streamlit.io/)
