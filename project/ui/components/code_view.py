import streamlit as st
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter


def render_code_snippet(code: str, lang: str = "python"):
    return render_code_snippet_with_highlight(code, lang=lang, highlight_lines=None)


def render_code_snippet_with_highlight(code: str, lang: str = "python", highlight_lines: list = None, highlight_map: dict = None):
    """Render code with optional line highlights.

    `highlight_lines` is a list of line numbers to highlight with a default color.
    `highlight_map` is a dict of line->hex color to use for specific line highlights.
    """
    lexer = get_lexer_by_name(lang, stripall=True)
    formatter = HtmlFormatter(style="friendly", full=False, noclasses=True)
    html = highlight(code, lexer, formatter)
    if highlight_lines or highlight_map:
        lines = html.splitlines()
        new_lines = []
        for i, line in enumerate(lines, start=1):
            color = None
            if highlight_map and i in highlight_map:
                color = highlight_map[i]
            elif highlight_lines and i in highlight_lines:
                color = "rgba(255,200,0,0.15)"
            if color:
                new_lines.append(f"<div style='background: {color}; padding:2px'>{line}</div>")
            else:
                new_lines.append(line)
        html = "\n".join(new_lines)
    st.markdown(html, unsafe_allow_html=True)
