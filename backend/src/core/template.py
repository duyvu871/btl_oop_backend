from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates"

env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=select_autoescape(["html", "xml"]))


def render_email(template_base: str, context: dict):
    html_tpl = env.get_template(f"{template_base}.html")
    txt_tpl = env.get_template(f"{template_base}.txt")
    html = html_tpl.render(**context)
    text = txt_tpl.render(**context)
    return text, html
