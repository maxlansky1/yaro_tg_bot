"""
Конфигурационный файл для сборщика документации Sphinx.

Этот файл содержит все настройки, необходимые для кастомизации входных и выходных данных Sphinx.
Он выполняется как код на Python во время сборки, при этом текущая директория устанавливается как директория конфигурации.
"""

import os
import sys

# Добавляет родительскую директорию в системный путь, чтобы Sphinx мог найти исходные модули
# для автодокументации. Это позволяет Sphinx импортировать модули проекта из корневой директории.
sys.path.insert(0, os.path.abspath(".."))


# Информация о проекте для документации
project = "projectTemplate"
copyright = "2025, maxlansky"
author = "maxlansky"
release = "0.1"

# Настройки для работы с PlantUML и рендеринга UML-диаграмм.
# В GitHub Actions используется путь /usr/local/bin/plantuml/plantuml.jar, а для Windows — C:\\plantuml\\plantuml.jar.
if "GITHUB_ACTIONS" in os.environ:
    plantuml = "java -jar /usr/local/bin/plantuml/plantuml.jar"
elif os.name == "nt":  # Для Windows
    plantuml = r"java -jar C:\plantuml\plantuml.jar"
else:
    raise OSError("Unsupported OS")

plantuml_output_format = "svg"
plantuml_latex_output_format = "svg"


# Список расширений Sphinx
extensions = [
    "sphinx.ext.autodoc",  # автодока из docstring'ов
    "sphinx.ext.viewcode",  # ссылки на исходники
    "sphinx.ext.napoleon",  # Google/NumPy стиль docstring'ов
    "sphinx.ext.githubpages",  # позволяет использовать стили sphinx при хостинге доков на github pages
    "sphinx_autodoc_typehints",  # type hints в сигнатурах
    "myst_parser",  # поддержка Markdown (.md)
    "sphinx.ext.todo",  # поддержка TODO
    "sphinx.ext.coverage",  # проверяет покрытие документации
    "sphinx.ext.ifconfig",  # условные директивы в документации
    "sphinx_copybutton",  # добавляет кнопку скопировать код в документацию
    "sphinxcontrib.plantuml",  # добавляет поддержку plantuml
    "sphinx_rtd_theme",  # переключает на красивую тему
    "sphinx_togglebutton",  # позволяет создавать разворачиваемые списки
]

# Настройки по умолчанию для расширения autodoc, которое автоматически извлекает docstring'и
autodoc_default_options = {
    "members": True,
    "undoc-members": False,  # Не показывать недокументированные члены
    "private-members": False,  # Не показывать приватные методы (_method)
    "special-members": False,  # Не показывать __init__, __str__ и т.д.
    "inherited-members": False,  # Показывать унаследованные методы
    "show-inheritance": True,  # Показывать иерархию наследования
}

# Настройки для myst_parser
myst_enable_extensions = []

myst_heading_anchors = 6  # автоматически генерирует ссылки на заголовки (все 6 уровней)

# Настройки для обработки исходных файлов, шаблонов, исключений и вывода HTML
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

language = "ru"

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "version_selector": True,  # Показать версию документации
}

html_static_path = ["_static"]

plantuml_output_format = "svg_img"
