"""ACM (sigconf-style) two-column Word helpers, shared by the report builders (copied from Deliverable 1)."""
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

HERE = Path(__file__).parent
FIG = HERE.parent.parent / "figures"

SERIF, SANS = "Times New Roman", "Arial"
BODY_PT, SMALL_PT = 9.5, 8

doc = Document()

# ---------- page: US Letter, ACM text block 7 x 9.25 in ----------
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
sec.left_margin = sec.right_margin = Inches(0.75)
sec.top_margin, sec.bottom_margin = Inches(0.8), Inches(0.9)

normal = doc.styles["Normal"]
normal.font.name = SERIF
normal.font.size = Pt(BODY_PT)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), SERIF)
normal.paragraph_format.space_after = Pt(0)
normal.paragraph_format.line_spacing = 1.0
normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

for name, size in [("Heading 1", 9.5), ("Heading 2", 9.5)]:
    st = doc.styles[name]
    st.font.name = SANS
    st.element.rPr.rFonts.set(qn("w:asciiTheme"), "")
    st.element.rPr.rFonts.set(qn("w:hAnsiTheme"), "")
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.italic = False
    st.font.color.rgb = None
    st.paragraph_format.space_before = Pt(9 if name == "Heading 1" else 6)
    st.paragraph_format.space_after = Pt(3)
    st.paragraph_format.keep_with_next = True


def set_columns(section, num, space_in=0.33):
    cols = section._sectPr.find(qn("w:cols"))
    if cols is None:
        cols = OxmlElement("w:cols")
        section._sectPr.append(cols)
    cols.set(qn("w:num"), str(num))
    cols.set(qn("w:space"), str(int(space_in * 1440)))


def add_runs(p, text, size=None, font=None):
    """Add text with **bold** and *italic* markup."""
    for part in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text):
        if not part:
            continue
        if part.startswith("**"):
            r = p.add_run(part[2:-2])
            r.bold = True
        elif part.startswith("*"):
            r = p.add_run(part[1:-1])
            r.italic = True
        else:
            r = p.add_run(part)
        if size:
            r.font.size = Pt(size)
        if font:
            r.font.name = font
    return p


def para(text, indent=True, size=None, align=None, after=0, before=0, font=None):
    p = doc.add_paragraph()
    add_runs(p, text, size, font)
    pf = p.paragraph_format
    pf.first_line_indent = Inches(0.13) if indent else None
    pf.space_after, pf.space_before = Pt(after), Pt(before)
    if align is not None:
        p.alignment = align
    return p


def h1(text):
    return doc.add_heading(text.upper(), level=1)


def h2(text):
    return doc.add_heading(text, level=2)


def bullets(items):
    for it in items:
        p = doc.add_paragraph(style="List Bullet")
        add_runs(p, it)
        p.paragraph_format.space_after = Pt(1)
        for r in p.runs:
            r.font.size = Pt(BODY_PT)


def border(cell, edges):
    tcPr = cell._tc.get_or_add_tcPr()
    b = OxmlElement("w:tcBorders")
    for edge, sz in edges.items():
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), str(sz))
        e.set(qn("w:color"), "000000")
        b.append(e)
    tcPr.append(b)


def caption(text, before=4, after=2):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(SMALL_PT)
    r.font.name = SANS
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(before), Pt(after)
    return p


def fix_widths(t, widths_in):
    """Fixed layout + explicit grid, so Word and LibreOffice both keep the column widths."""
    tblPr = t._tbl.tblPr
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tblPr.append(lay)
    tw = OxmlElement("w:tblW")
    tw.set(qn("w:w"), str(int(sum(widths_in) * 1440)))
    tw.set(qn("w:type"), "dxa")
    for old in tblPr.findall(qn("w:tblW")):
        tblPr.remove(old)
    tblPr.append(tw)
    for col, w in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), widths_in):
        col.set(qn("w:w"), str(int(w * 1440)))
    for row in t.rows:
        for c, w in zip(row.cells, widths_in):
            c.width = Inches(w)


def table(caption_text, rows, widths_in, size=SMALL_PT):
    """ACM style: caption above, rules only at top, under the header and at the bottom."""
    caption(caption_text, before=6).paragraph_format.keep_with_next = True
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    last = len(rows) - 1
    fix_widths(t, widths_in)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.cell(i, j)
            c.width = Inches(widths_in[j])
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.keep_with_next = i < last
            add_runs(p, val, size)
            if i == 0:
                for r in p.runs:
                    r.bold = True
                border(c, {"top": 8, "bottom": 4})
            elif i == last:
                border(c, {"bottom": 8})
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def figure(name, width_in, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(FIG / name), width=Inches(width_in))
    caption(text, after=6)


def page_numbers(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    for tag, text in [("begin", None), (None, "PAGE"), ("end", None)]:
        el = OxmlElement("w:fldChar" if tag else "w:instrText")
        if tag:
            el.set(qn("w:fldCharType"), tag)
        else:
            el.set(qn("xml:space"), "preserve")
            el.text = text
        run._r.append(el)
    run.font.size = Pt(SMALL_PT)


COL_W = 3.33  # column width in inches

