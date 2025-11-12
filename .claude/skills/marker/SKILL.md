---
name: marker-pdf-converter
description: Convert PDF files to clean, LLM-ready markdown using marker. Use when working with PDFs, document conversion, extracting content from PDFs, or when user asks to convert documents to markdown. Supports tables, equations, images, and multi-language OCR.
---

# Marker PDF to Markdown Converter

This skill enables conversion of PDF files (and other document formats) to clean, structured markdown using the marker tool.

## What Marker Does

Marker converts documents to markdown with high accuracy:
- Converts PDF, image, PPTX, DOCX, XLSX, HTML, EPUB files in all languages
- Formats tables, forms, equations, inline math, links, references, and code blocks
- Extracts and saves images
- Removes headers/footers/artifacts
- Preserves document structure

## Installation

Marker should be installed via pip:
```bash
pip install marker-pdf
```

For non-PDF documents, install with full dependencies:
```bash
pip install marker-pdf[full]
```

## Usage Instructions

### Basic Conversion

To convert a single PDF to markdown:
```bash
marker_single /path/to/file.pdf --output_dir /path/to/output
```

**Important**: The output directory should default to the same directory as the input PDF to keep markdown files beside their source PDFs.

### Recommended Workflow

When a user asks to convert a PDF:

1. **Identify the PDF file path** - Ask the user or search for PDF files if needed
2. **Determine output location** - Use the same directory as the PDF by default
3. **Run conversion** with appropriate options:
   ```bash
   marker_single /absolute/path/to/document.pdf --output_dir /absolute/path/to/same/directory
   ```
4. **Report results** - Inform the user of the created markdown file location

### Key Options

- `--output_dir PATH`: Directory for output files (default: same as PDF location)
- `--output_format [markdown|json|html|chunks]`: Output format (default: markdown)
- `--use_llm`: Use an LLM to improve accuracy (requires API key)
- `--force_ocr`: Force OCR on entire document, good for inline math
- `--page_range TEXT`: Process specific pages (e.g., "0,5-10,20")
- `--paginate_output`: Add page numbers to output
- `--debug`: Enable debug mode for troubleshooting

### Enhanced Quality

For highest accuracy, use LLM mode:
```bash
marker_single /path/to/file.pdf --use_llm --output_dir /path/to/output
```

This requires setting `GOOGLE_API_KEY` environment variable or using other LLM services (Ollama, Claude, OpenAI).

### Batch Conversion

To convert multiple PDFs in a folder:
```bash
marker /path/to/input/folder --output_dir /path/to/output
```

Options:
- `--workers N`: Number of parallel conversion workers

### Advanced Use Cases

**Extract tables only:**
```bash
marker_single file.pdf --use_llm --force_layout_block Table --converter_cls marker.converters.table.TableConverter --output_format json
```

**OCR only:**
```bash
marker_single file.pdf --converter_cls marker.converters.ocr.OCRConverter
```

**Force OCR for better math handling:**
```bash
marker_single file.pdf --force_ocr --use_llm
```

## Output Structure

### Markdown Output
- Image links (images saved in same folder)
- Formatted tables
- LaTeX equations (fenced with `$$`)
- Code blocks (triple backticks)
- Superscripts for footnotes

### File Naming
By default, marker creates:
- `filename.md` - The markdown output
- `filename_meta.json` - Metadata about the conversion
- `_page_N_Figure_M.jpeg` - Extracted images (in same directory)

## Troubleshooting

- **Garbled text**: Use `--force_ocr` to re-OCR the document
- **Out of memory**: Decrease `--workers` count or split PDFs
- **Poor accuracy**: Try `--use_llm` flag with appropriate API key
- **Complex layouts**: Use `--use_llm --force_ocr` for best results

## Environment Variables

- `TORCH_DEVICE`: Force specific torch device (e.g., `cuda`, `cpu`, `mps`)
- `GOOGLE_API_KEY`: Required for `--use_llm` with Gemini (default)

## Best Practices

1. **Always use absolute paths** for input and output directories
2. **Place output beside source PDF** by default for easy reference
3. **Check if marker is installed** before attempting conversion
4. **Inform user about LLM options** if accuracy is critical
5. **Report extracted image locations** so user knows where to find them
6. **Consider batch processing** for multiple PDFs in same directory

## Example Workflow

```bash
# Check if marker is installed
marker_single --help

# Convert a PDF with output in same directory
marker_single /home/user/documents/report.pdf --output_dir /home/user/documents

# High-quality conversion with LLM
marker_single /home/user/documents/technical-paper.pdf --output_dir /home/user/documents --use_llm --force_ocr

# Batch convert all PDFs in a folder
marker /home/user/documents/pdfs/ --output_dir /home/user/documents/pdfs/
```

## When to Use This Skill

Use this skill when:
- User asks to convert PDF to markdown
- User mentions "extract text from PDF"
- User wants to process document content
- User needs to work with PDF tables or equations
- User requests document parsing or analysis
- User says "convert", "parse", "extract" + mentions PDF or document
- Working with academic papers, reports, forms, presentations
- Need to extract structured data from documents

## Limitations

- Very complex nested layouts may not work perfectly
- Forms rendering may vary in quality
- Using `--use_llm` and `--force_ocr` solves most issues
- Requires Python 3.10+ and PyTorch installation
