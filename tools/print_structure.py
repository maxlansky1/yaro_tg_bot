"""Вывод структуры проекта в консоль в виде дерева каталогов.

Модуль предоставляет функции для рекурсивного обхода директорий проекта
и красивого вывода его структуры с фильтрацией служебных файлов и папок.
"""

import os

# Папки, которые нужно игнорировать
IGNORE_FOLDERS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "_build",
    "_static",
    "_templates",
    ".ruff_cache",
}

# Файлы и расширения, которые нужно игнорировать
IGNORE_FILES = {
    ".DS_Store",
    ".pyc",  # Скомпилированные Python-файлы
    ".pyo",
    ".pyd",
    ".mo",
    ".log",
    ".tmp",
    "~",  # Временные файлы редакторов
}


def should_ignore(name, is_dir):
    """Определяет, нужно ли игнорировать файл или директорию при выводе.

    Args:
        name (str): Имя файла или директории.
        is_dir (bool): Флаг, указывающий является ли элемент директорией.

    Returns:
        bool: True если элемент нужно игнорировать, False если нужно включить в вывод.
    """

    if is_dir:
        return name in IGNORE_FOLDERS
    else:
        # Игнорируем по имени или по расширению
        if name in IGNORE_FILES:
            return True
        _, ext = os.path.splitext(name)
        return ext in IGNORE_FILES or name.startswith(".")
    return False


def print_tree(start_path, prefix=""):
    """Рекурсивно выводит структуру каталогов в виде ASCII-дерева.

    Args:
        start_path (str): Путь к корневой директории для вывода.
        prefix (str): Префикс для отступов (используется при рекурсивных вызовах).

    Side Effects:
        Выводит в stdout дерево каталогов с использованием символов псевдографики.

    Note:
        Автоматически обрабатывает ошибки доступа к директориям.
    """
    try:
        entries = sorted(os.listdir(start_path))
    except PermissionError:
        print(f"{prefix}└── [Нет доступа]")
        return

    filtered_entries = []
    for entry in entries:
        full_path = os.path.join(start_path, entry)
        is_dir = os.path.isdir(full_path)
        if not should_ignore(entry, is_dir):
            filtered_entries.append((entry, is_dir))

    for i, (entry, is_dir) in enumerate(filtered_entries):
        path = os.path.join(start_path, entry)
        is_last = i == len(filtered_entries) - 1

        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{entry}" + ("/" if is_dir else ""))

        if is_dir:
            new_prefix = "    " if is_last else "│   "
            print_tree(path, prefix + new_prefix)


if __name__ == "__main__":
    project_root = os.getcwd()  # Текущая директория
    root_name = os.path.basename(project_root) + "/"

    print(root_name)
    print()
    print_tree(project_root)
