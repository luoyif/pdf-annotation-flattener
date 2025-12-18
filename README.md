# PDF 批注固化工具 (PDF Annotation Flattener)

将 PDF 中的批注（高亮、便签、删除线等）固化到页面上，方便分享和打印。

## 功能特点

- ✅ 支持多种批注类型：高亮、删除线、下划线、便签、插入符号、矩形框等
- ✅ 在原文上保留视觉标记 + 红色编号
- ✅ 自动生成批注汇总页
- ✅ 完全在浏览器中使用，无需安装软件
- ✅ 文件不存储，保护隐私

## 在线使用

访问：[你的 Streamlit Cloud URL]

## 本地运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行应用

```bash
streamlit run app.py
```

### 3. 打开浏览器

访问 http://localhost:8501

## 部署到 Streamlit Cloud（免费）

### 步骤 1: 准备 GitHub 仓库

1. 在 GitHub 创建新仓库
2. 上传以下文件：
   - `app.py`
   - `requirements.txt`
   - `README.md`（可选）

### 步骤 2: 部署到 Streamlit Cloud

1. 访问 [share.streamlit.io](https://share.streamlit.io)
2. 使用 GitHub 账号登录
3. 点击 "New app"
4. 选择你的仓库和 `app.py` 文件
5. 点击 "Deploy"

等待几分钟，你的应用就会上线！

## 项目结构

```
streamlit-app/
├── app.py              # 主应用代码
├── requirements.txt    # Python 依赖
└── README.md          # 说明文档
```

## 技术栈

- **Streamlit**: Web 界面框架
- **PyMuPDF (fitz)**: PDF 处理库

## 支持的批注类型

| 类型 | 英文名 | 支持 |
|------|--------|------|
| 便签 | Note/Text | ✅ |
| 高亮 | Highlight | ✅ |
| 删除线 | Strikeout | ✅ |
| 下划线 | Underline | ✅ |
| 插入 | Caret | ✅ |
| 矩形框 | Rectangle | ✅ |
| 椭圆 | Ellipse | ✅ |
| 手绘 | Ink | ✅ |
| 线条 | Line | ✅ |
| 文本框 | FreeText | ✅ |

## License

MIT License
