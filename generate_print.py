import re
import os
import sys

# Pokusíme se importovat WeasyPrint
try:
    from weasyprint import HTML
except ImportError:
    print("Chyba: Knihovna 'weasyprint' není nainstalována.")
    print("Nainstaluj ji příkazem: pip3 install weasyprint")
    sys.exit(1)

# Konfigurace
SOURCE_DIR = "./songs"
OUTPUT_DIR = "./print_pdf"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Gentium+Book+Plus:ital,wght@0,400;0,700;1,400;1,700&display=swap" rel="stylesheet">
    <style>
        /* Definice strany pro WeasyPrint */
        @page {{
            size: A4;
            margin: 2.5cm 2cm 2.5cm 2cm;
            
            /* Automatické číslování stránek v patce */
            @bottom-center {{
                content: "Page " counter(page);
                font-family: 'Gentium Book Plus', serif;
                font-size: 9pt;
                color: #888;
                border-top: 0.5pt solid #eee;
                width: 100%;
                padding-top: 10pt;
            }}
        }}

        body {{
            font-family: 'Gentium Book Plus', serif;
            line-height: 1.6;
            color: #1a1a1a;
            font-size: 11pt;
        }}
        
        .header {{
            border-bottom: 2px solid #4a3b32;
            margin-bottom: 30pt;
            padding-bottom: 10pt;
        }}
        .chapter-label {{ text-transform: uppercase; letter-spacing: 1pt; font-size: 10pt; color: #666; }}
        h1 {{ margin: 5pt 0; font-size: 22pt; }}
        
        .author-subtitle {{
            font-size: 13pt;
            font-style: italic;
            color: #555;
            margin-top: 5pt;
        }}
        
        .lecture-title {{
            font-size: 20pt;
            font-style: bold;
            color: #000;
            margin: 0 0 30pt 0;
            padding-top: 10pt;
            border-bottom: 1px solid #4a3b32;
            page-break-before: always;
        }}

        .lecture-title.first-lecture-title {{
            page-break-before: avoid;
            margin-top: 20pt;
        }}

        .verse-block {{
            margin-bottom: 45pt;
            page-break-before: always;
            page-break-inside: avoid;
        }}

        .verse-block.first-verse {{
            page-break-before: avoid;
        }}
        
        .verse-number {{
            font-weight: bold;
            color: #000;
            border-bottom: 1px solid #f4bf7f;
            margin-bottom: 12pt;
            font-size: 14pt;
            text-transform: uppercase;
        }}
        .devanagari {{
            font-size: 15pt;
            margin-bottom: 10pt;
            line-height: 1.4;
            color: #000;
        }}
        .iast {{
            font-style: normal;
            font-size: 17pt;
            color: #000;
            margin-bottom: 14pt;
        }}
        .glossary {{
            font-size: 14pt;
            color: #000;
            margin-bottom: 14pt;
            text-align: justify;
            border-left: 0px solid #f0e6da;
            padding-left: 0pt;
            line-height: 1.6;
        }}
        .glossary b {{ font-weight: 700; }}
        .translation {{
            font-size: 17pt;
            font-weight: 700;
            color: #000;
            border-left: 4px solid #f4bf7f;
            padding-left: 7pt;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="chapter-label">{category}</div>
        <h1>{title}</h1>
        <div class="author-subtitle">Lectures by Swami Sarvapriyananda</div>
    </div>
    {content}
</body>
</html>
"""

def parse_pro_file(content):
    title_match = re.search(r'{title:\s*(.*?)}', content)
    title = title_match.group(1) if title_match else "Bhagavad Gita"
    category_match = re.search(r'{category:\s*(.*?)}', content)
    category = category_match.group(1) if category_match else ""
    
    verse_matches = re.finditer(r'{sov:(?P<num>.*?)}(?P<body>.*?){eot}', content, re.DOTALL)
    
    html_verses = ""
    for idx, match in enumerate(verse_matches):
        v_num = match.group('num').strip()
        body = match.group('body')
        
        sanskrit_part_match = re.search(r'(.*?){eov}', body, re.DOTALL)
        sanskrit_part = sanskrit_part_match.group(1).strip() if sanskrit_part_match else ""
        sanskrit_part = re.sub(r'https?://\S+', '', sanskrit_part).strip()
        sanskrit_blocks = [b.strip() for b in sanskrit_part.split('\n\n') if b.strip()]
        
        devanagari = sanskrit_blocks[0] if len(sanskrit_blocks) > 0 else ""
        iast = sanskrit_blocks[1] if len(sanskrit_blocks) > 1 else ""
        glossary = sanskrit_blocks[2] if len(sanskrit_blocks) > 2 else ""
        
        formatted_glossary = re.sub(r'(^|(?<=;\s))([^—;]+?)(?=\s*[—]|(?:\s+-\s*))', r'<b>\2</b>', glossary)
        
        translation_match = re.search(r'{sot}(.*)', body, re.DOTALL)
        translation = translation_match.group(1).strip() if translation_match else ""

        verse_classes = "verse-block first-verse" if idx == 0 else "verse-block"

        html_verses += f"""
        <div class="{verse_classes}">
            <div class="verse-number">{v_num}</div>
            <div class="devanagari">{devanagari.replace('|', '।').replace('\n', '<br>')}</div>
            <div class="iast">{iast.replace('\n', '<br>')}</div>
            <div class="glossary">{formatted_glossary.replace('\n', ' ')}</div>
            <div class="translation">{translation}</div>
        </div>
        """
    return title, category, html_verses

# HLAVNÍ PROCES
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

for root, dirs, files in os.walk(SOURCE_DIR):
    if root == SOURCE_DIR: continue

    files.sort()
    chapter_verses_html = ""
    chapter_category = ""
    folder_name = os.path.basename(root)
    lecture_index = 0

    for file_name in files:
        if file_name.endswith(".pro"):
            file_path = os.path.join(root, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                raw_content = f.read()
                try:
                    t, cat, verses_html = parse_pro_file(raw_content)
                    
                    # Cesta pro uložení
                    rel_subfolder = os.path.relpath(root, SOURCE_DIR)
                    target_dir = os.path.join(OUTPUT_DIR, rel_subfolder)
                    if not os.path.exists(target_dir): os.makedirs(target_dir)
                    
                    # 1. Generování HTML
                    full_html = HTML_TEMPLATE.format(title=t, category=cat, content=verses_html)
                    html_path = os.path.join(target_dir, file_name.replace(".pro", ".html"))
                    with open(html_path, "w", encoding="utf-8") as out:
                        out.write(full_html)
                    
                    # 2. Generování PDF (WeasyPrint)
                    pdf_path = os.path.join(target_dir, file_name.replace(".pro", ".pdf"))
                    HTML(string=full_html).write_pdf(pdf_path)
                    
                    print(f"OK: {file_name} -> HTML & PDF")

                    # Přidání do celku kapitoly
                    lecture_title_classes = "lecture-title first-lecture-title" if lecture_index == 0 else "lecture-title"
                    lecture_heading = f"<div class='{lecture_title_classes}'>{t}</div>"
                    chapter_verses_html += lecture_heading + verses_html
                    lecture_index += 1
                    if not chapter_category: chapter_category = cat

                except Exception as e:
                    print(f"CHYBA v {file_name}: {e}")

    # 3. Generování celku kapitoly (HTML i PDF)
    if chapter_verses_html:
        match = re.search(r'\d+', folder_name)
        chapter_num = str(int(match.group())) if match else folder_name
        full_title = f"Bhagavad Gita - Chapter {chapter_num}"
        
        chapter_html = HTML_TEMPLATE.format(title=full_title, category=chapter_category, content=chapter_verses_html)
        
        # Uložit HTML kapitoly
        c_html_path = os.path.join(target_dir, f"Full_Chapter_{chapter_num}.html")
        with open(c_html_path, "w", encoding="utf-8") as out:
            out.write(chapter_html)
            
        # Uložit PDF kapitoly
        c_pdf_path = os.path.join(target_dir, f"Full_Chapter_{chapter_num}.pdf")
        HTML(string=chapter_html).write_pdf(c_pdf_path)
        
        print(f"--- KAPITOLA {chapter_num} DOKONČENA ---")