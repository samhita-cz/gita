import re
import os

# Konfigurace
SOURCE_DIR = "./songs"
OUTPUT_DIR = "./print_pdf"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Gentium+Book+Plus:ital,wght@0,400;0,700;1,400;1,700&display=swap" rel="stylesheet">
    <style>
        @page {{
            size: A4;
            margin: 2cm;
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
        
        /* Styl pro název přednášky uvnitř kapitoly */
        .lecture-title {{
            font-size: 18pt;
            color: #4a3b32;
            margin: 0 0 30pt 0;
            padding-top: 10pt;
            border-bottom: 1px solid #4a3b32;
            page-break-before: always;
        }}

        /* První název v dokumentu nepotřebuje prázdnou stránku před sebou */
        .lecture-title:first-of-type {{
            page-break-before: avoid;
            margin-top: 20pt;
        }}

        .verse-block {{
            margin-bottom: 45pt;
            page-break-inside: avoid;
        }}
        .verse-number {{
            font-weight: bold;
            color: #4a3b32;
            border-bottom: 1px solid #eee;
            margin-bottom: 12pt;
            font-size: 10pt;
            text-transform: uppercase;
        }}
        .devanagari {{
            font-size: 17pt;
            margin-bottom: 10pt;
            line-height: 1.4;
            color: #000;
        }}
        .iast {{
            font-style: italic;
            font-size: 11.5pt;
            color: #333;
            margin-bottom: 14pt;
        }}
        .glossary {{
            font-size: 9.5pt;
            color: #000;
            margin-bottom: 14pt;
            text-align: justify;
            border-left: 3px solid #f0e6da;
            padding-left: 12pt;
            line-height: 1.4;
        }}
        .glossary b {{ font-weight: 700; }}
        .translation {{
            font-size: 12pt;
            font-weight: 700;
            color: #000;
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
    for match in verse_matches:
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

        html_verses += f"""
        <div class="verse-block">
            <div class="verse-number">{v_num}</div>
            <div class="devanagari">{devanagari.replace('|', '।').replace('\n', '<br>')}</div>
            <div class="iast">{iast.replace('\n', '<br>')}</div>
            <div class="glossary">{formatted_glossary.replace('\n', ' ')}</div>
            <div class="translation">{translation}</div>
        </div>
        """
    return title, category, html_verses

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

for root, dirs, files in os.walk(SOURCE_DIR):
    if root == SOURCE_DIR:
        continue

    files.sort()
    
    chapter_verses_html = ""
    chapter_category = ""
    folder_name = os.path.basename(root)

    for file_name in files:
        if file_name.endswith(".pro"):
            file_path = os.path.join(root, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                raw_content = f.read()
                try:
                    t, cat, verses_html = parse_pro_file(raw_content)
                    
                    individual_html = HTML_TEMPLATE.format(title=t, category=cat, content=verses_html)
                    rel_subfolder = os.path.relpath(root, SOURCE_DIR)
                    target_dir = os.path.join(OUTPUT_DIR, rel_subfolder)
                    if not os.path.exists(target_dir): os.makedirs(target_dir)
                    
                    output_file = os.path.join(target_dir, file_name.replace(".pro", ".html"))
                    with open(output_file, "w", encoding="utf-8") as out:
                        out.write(individual_html)
                    
                    lecture_heading = f"<div class='lecture-title'>{t}</div>"
                    chapter_verses_html += lecture_heading + verses_html
                    if not chapter_category: chapter_category = cat

                except Exception as e:
                    print(f"Error in {file_name}: {e}")

    if chapter_verses_html:
        match = re.search(r'\d+', folder_name)
        chapter_num = str(int(match.group())) if match else folder_name
        full_chapter_title = f"Bhagavad Gita - Chapter {chapter_num}"
        
        full_html = HTML_TEMPLATE.format(title=full_chapter_title, category=chapter_category, content=chapter_verses_html)
        
        chapter_output_file = os.path.join(target_dir, f"Full_Chapter_{chapter_num}.html")
        with open(chapter_output_file, "w", encoding="utf-8") as out:
            out.write(full_html)
        print(f"--- GENERATED: {chapter_output_file} ---")