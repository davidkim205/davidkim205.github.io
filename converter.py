import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

class MarkdownToHTMLConverter:
    
    def __init__(self):
        self.sections = []
        self.title = ""
        self.subtitle = ""
        
    def parse_markdown(self, md_content: str) -> Dict:
        lines = md_content.split('\n')
        
        # Extract title (first H1)
        idx = 0
        if lines and lines[0].startswith('# '):
            self.title = lines[0][2:].strip()
            idx = 1
        
        # Skip empty lines
        while idx < len(lines) and not lines[idx].strip():
            idx += 1
        
        # Extract subtitle (first non-empty paragraph after title)
        if idx < len(lines) and not lines[idx].startswith('#'):
            self.subtitle = lines[idx].strip()
            idx += 1
        
        # Parse sections - H2 sections contain H3 subsections
        current_section = None
        current_content = []
        
        while idx < len(lines):
            line = lines[idx]
            
            # H2 sections - create new main section
            if line.startswith('## '):
                # Save previous section
                if current_section:
                    self.sections.append({
                        'title': current_section,
                        'content': '\n'.join(current_content).strip(),
                        'level': 2
                    })
                
                current_section = line[3:].strip()
                current_content = []
            
            else:
                # Add all content (including H3 subsections) to current H2 section
                current_content.append(line)
            
            idx += 1
        
        # Add last section
        if current_section:
            self.sections.append({
                'title': current_section,
                'content': '\n'.join(current_content).strip(),
                'level': 2
            })
        
        return {
            'title': self.title,
            'subtitle': self.subtitle,
            'sections': self.sections
        }
    
    def convert_markdown_to_html(self, md_text: str) -> str:
        """Convert markdown text to HTML"""
        if not md_text.strip():
            return ""
        
        # First, handle tables and extract table captions
        html, table_captions = self.process_tables_with_captions(md_text)
        
        # Process line by line to handle lists and H3 headings properly
        lines = html.split('\n')
        result_blocks = []
        table_index = 0
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Skip empty lines
            if not line.strip():
                i += 1
                continue
            
            # Check for H3 subsection headings
            if line.strip().startswith('### '):
                h3_title = line.strip()[4:]
                result_blocks.append(f'<h3 class="title is-4 has-text-left">{h3_title}</h3>')
                i += 1
                continue
            # Figure / Table 문단 제목 중앙
            stripped = line.strip()
            text_to_check = stripped.lstrip('*').strip()
            # Figure 1, Table 2 등 번호가 있는 패턴만 매칭
            import re
            if re.match(r'^(Figure|Table)\s+\d+[\.:)]', text_to_check):
                formatted = self.apply_inline_formatting(stripped)
                result_blocks.append(f'<p class="has-text-centered">{formatted}</p>')
                i += 1
                continue

            if line.strip().startswith('#### '):
                h4_title = line.strip()[5:]
                result_blocks.append(f'<h4 class ="title is-5 has-text-left">{h4_title}</h4>')
                i += 1
                continue
            # 만약 마크다운 # 추가 시 이 행 아래에 추가
            # Markdown image: ![caption](src)
            image_match = re.match(r'!\[(.*?)\]\((.*?)\)', line.strip())
            if image_match:
                caption, img_src = image_match.groups()
                result_blocks.append(f'''
            <figure class="has-text-centered">
            <img src="{img_src}" alt="{caption}">
            </figure>
            ''')
                i += 1
                continue

            # Check if it's a table
            if line.strip().startswith('<div class="table-container">'):
                # Collect entire table
                table_html = []
                while i < len(lines) and not (lines[i].strip() == '</div>' and '</table>' in lines[i-1]):
                    table_html.append(lines[i])
                    i += 1
                if i < len(lines):
                    table_html.append(lines[i])  # Add closing </div>
                    i += 1
                
                result_blocks.append('\n'.join(table_html))
                
                # table 제목 중앙 
                if table_index < len(table_captions) and table_captions[table_index]:
                    result_blocks.append(f'<p class="has-text-centered">{self.apply_inline_formatting(table_captions[table_index])}</p>')
                table_index += 1
                continue
            
            # Check if it's a list item
            if line.strip().startswith(('* ', '- ')):
                list_lines = []

                while i < len(lines):
                    current = lines[i].strip()

                    if current.startswith(('* ', '- ')):
                        list_lines.append(lines[i])
                        i += 1

                    elif current and not current.startswith(('#', '|', 'Table ')):
                        # 리스트 본문 continuation
                        list_lines.append(lines[i])
                        i += 1

                    elif not current:
                        i += 1
                        break

                    else:
                        break

                result_blocks.append(self.process_list_lines(list_lines))
                continue

            # Regular paragraph
            formatted = self.apply_inline_formatting(line.strip())
            result_blocks.append(f'<p>{formatted}</p>')


            i += 1

        return '\n'.join(result_blocks)
            

    def process_list_lines(self, lines: List[str]) -> str:
        """Process list lines into a single <ul> block"""
        result = ['<ul>']
        current_item_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith(('* ', '- ')):
                # Save previous item if exists
                if current_item_lines:
                    result.append(self._render_list_item(current_item_lines))
                    current_item_lines = []
                
                # Start new item (remove '* ' prefix)
                current_item_lines.append(stripped[2:])
            
            elif stripped:
                # Continuation of current list item
                current_item_lines.append(stripped)
        
        # Save last item
        if current_item_lines:
            result.append(self._render_list_item(current_item_lines))        
        result.append('</ul>')
        return '\n'.join(result)
    
    def _render_list_item(self, lines: List[str]) -> str:
        parts = []
        for i, line in enumerate(lines):
            formatted = self.apply_inline_formatting(line)
            if i == 0:
                parts.append(formatted)
            else:
                parts.append(f'<p>{formatted}</p>')
            
        return f'  <li>{"".join(parts)}</li>'
    
    def apply_inline_formatting(self, text: str) -> str:
        """Apply inline markdown formatting"""

        # Code
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>',text)
        
        # Bold
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        
        # Italic: *italic* or _italic_ -> <em>italic</em>
        # 주의: 굵게(**) 처리를 먼저 한 뒤에 기울임체(*)를 처리해야 겹치지 않습니다.
        text = re.sub(r'\*([^\*]+)\*', r'<em>\1</em>', text)
        text = re.sub(r'_([^_]+)_', r'<em>\1</em>', text)

        # Links
        text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
        
        return text
    
    def process_tables_with_captions(self, text: str) -> Tuple[str, List[str]]:
        """Process markdown tables into HTML and extract captions"""
        lines = text.split('\n')
        result = []
        captions = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this is a table line (starts with |)
            if line.strip().startswith('|') and '|' in line:
                table_lines = []
                
                # Collect all consecutive table lines
                while i < len(lines) and lines[i].strip().startswith('|'):
                    table_lines.append(lines[i])
                    i += 1
                
                # Check for caption on next non-empty line
                caption = ""
                while i < len(lines):
                    next_line = lines[i].strip()
                    if not next_line:
                        i += 1
                        continue
                    # Check if it's a table caption (starts with "Table" or "[Table")
                    if next_line.startswith('Table ') or next_line.startswith('[Table'):
                        caption = next_line
                        i += 1
                    break
                
                # Convert table if we have at least 3 lines (header, separator, body)
                if len(table_lines) >= 3:
                    table_html = self.create_html_table(table_lines)
                    result.append(table_html)
                    captions.append(caption)
                else:
                    result.extend(table_lines)
                
                continue
            
            result.append(line)
            i += 1
        
        return '\n'.join(result), captions
    
    def create_html_table(self, table_lines: List[str]) -> str:
        """Create HTML table from markdown table lines"""
        table_html = []
        table_html.append('<div class="table-container">')
        table_html.append('  <table class="table is-bordered is-striped is-fullwidth">')
        
        # Parse header (first line)
        header_line = table_lines[0]
        raw_header_cells = header_line.split('|')
        # 맨 앞과 맨 뒤만 제거
        if len(raw_header_cells) > 0 and raw_header_cells[0].strip() == '':
            raw_header_cells = raw_header_cells[1:]
        if len(raw_header_cells) > 0 and raw_header_cells[-1].strip() == '':
            raw_header_cells = raw_header_cells[:-1]

        header_cells = [cell.strip() for cell in raw_header_cells]
        num_cols = len(header_cells)
        table_html.append('    <thead>')
        table_html.append('      <tr>')
        for cell in header_cells:
            formatted = self.apply_inline_formatting(cell)
            table_html.append(f'        <th class="has-text-left">{formatted}</th>')
        table_html.append('      </tr>')
        table_html.append('    </thead>')
        
        # Parse body (skip separator line at index 1)
        # Parse body
        table_html.append('    <tbody>')
        for line in table_lines[2:]:
            #정렬 구문 라인 건너뛰기
            stripped = line.strip()
            if all(c in '|:-\t ' for c in stripped) and ':' in stripped:
                continue
        
            raw_cells = line.split('|')
            if len(raw_cells) > 0 and raw_cells[0].strip() == '':
                raw_cells = raw_cells[1:]
            if len(raw_cells) > 0 and raw_cells[-1].strip() == '':
                raw_cells = raw_cells[:-1]

            cells = [cell.strip() for cell in raw_cells[:num_cols]]
            if len(cells) < num_cols:
                cells.extend([''] * (num_cols - len(cells)))

            table_html.append('      <tr>')
            for cell in cells:
                formatted = self.apply_inline_formatting(cell)
                table_html.append(
                    f'        <td class="has-text-left">{formatted}</td>'
                )
            table_html.append('      </tr>')
        table_html.append('    </tbody>')

        
        table_html.append('  </table>')
        table_html.append('</div>')
        
        return '\n'.join(table_html)
    
    def generate_html(self, data: Dict, output_path: str = None) -> str:
        """Generate complete HTML document"""
        
        # Build title with subtitle
        full_title = data['title']
        if data['subtitle']:
            full_title = f"{data['title']}: {data['subtitle']}"
        
        html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{data['title']}</title>
    <meta name="description" content="{data['subtitle']}">
    <meta name="keywords" content="{data['title']}">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bulma/0.9.3/css/bulma.min.css">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Google+Sans|Noto+Sans|Castoro">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    <style>
        .logo {{
            font-size: 24px;
            font-weight: bold;
        }}
        .footer-social {{
            display: flex;
            justify-content: center;
            gap: 10px;
        }}
        .footer-social a {{
            color: #fff;
            padding: 10px;
            border-radius: 50%;
            background-color: #4a4a4a;
        }}
        .table-container {{
            margin: 20px 0;
        }}
    </style>
</head>
<body>
<header class="navbar">
    <div class="navbar-brand">
        <a class="navbar-item logo" href="/">Research Blog</a>
    </div>
</header>


<section class="hero">
  <div class="hero-body">
    <div class="container is-max-desktop">
      <div class="columns is-centered">
        <div class="column has-text-centered">
          <h1 class="title is-1 publication-title">{full_title}</h1>

          <div class="column has-text-centered">
              <div class="is-size-5 publication-authors">
                <span class="author-block">
                  <a href="#">Authors</a>
                </span>
              </div>
          </div>

          <div class="column has-text-centered">
            <div class="publication-links">
              <!-- Dataset Link. -->
              <span class="link-block">
                <a href="#"
                  class="external-link button is-normal is-rounded is-dark">
                  <span class="icon">
                      <i class="far fa-images"></i>
                  </span>
                  <span>Dataset</span>
                  </a>
              </span>
              <!-- Paper Link. -->
              <span class="link-block">
                <a href="#"
                   class="external-link button is-normal is-rounded is-dark">
                  <span class="icon">
                      <i class="fas fa-file-pdf"></i>
                  </span>
                  <span>Paper</span>
                </a>
              </span>
              <!-- Code Link. -->
              <span class="link-block">
                <a href="#"
                  class="external-link button is-normal is-rounded is-dark">
                  <span class="icon">
                      <i class="fab fa-github"></i>
                  </span>
                  <span>Code</span>
                  </a>
              </span>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</section>

'''
        
        # Generate sections
        for section in data['sections']:
            # All sections use h2 with is-3 (since subsections are now handled within content)
            section_html = f'''
<section class="section">
  <div class="container is-max-desktop">
    <div class="columns is-centered has-text-centered">
      <div class="column is-four-fifths">
        <h2 class="title is-3 has-text-left">{section['title']}</h2>

        <div class="content has-text-justified">
{self.convert_markdown_to_html(section['content'])}
        </div>

      </div>
    </div>
  </div>
</section>
'''
            html_template += section_html
        
        # Footer
        html_template += '''

<footer class="footer">
    <div class="content has-text-centered">
        <p>
            <strong>Research Blog</strong> by <a href="#">Author</a>.
        </p>
    </div>
</footer>
</body>
</html>'''
        
        return html_template
    
    def convert_file(self, input_file: str, output_file: str = None):
        """Convert a markdown file to HTML"""
        # Read markdown file
        md_path = Path(input_file)
        if not md_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {input_file}")
        
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Parse and convert
        data = self.parse_markdown(md_content)
        html_content = self.generate_html(data)
        
        # Determine output file
        if output_file is None:
            output_file = md_path.stem + '.html'
        
        output_path = Path(output_file)
        
        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"+ Converted {input_file} -> {output_file}")
        return output_path


def main():
    """Main function for command-line usage"""
    if len(sys.argv) < 2:
        print("Usage: python converter.py <input.md> [output.html]")
        print("\nExample:")
        print("  python converter.py document.md")
        print("  python converter.py document.md output.html")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    converter = MarkdownToHTMLConverter()
    try:
        converter.convert_file(input_file, output_file)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()