import os


class FileClassifier:
    """Decides which category a file belongs to based on its extension."""

    DEFAULT_CATEGORIES = {
        "Images":    [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff", ".ico"],
        "Documents": [".pdf", ".doc", ".docx", ".txt", ".odt", ".rtf", ".xls", ".xlsx",
                      ".ppt", ".pptx", ".csv", ".md"],
        "Audio":     [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
        "Video":     [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
        "Archives":  [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
        "Code":      [".py", ".java", ".c", ".cpp", ".cs", ".js", ".ts", ".html", ".css",
                      ".php", ".rb", ".go", ".rs", ".sh", ".bat", ".sql", ".json", ".xml"],
        "Executables": [".exe", ".msi", ".apk", ".dmg", ".deb", ".rpm"],
        "Fonts":     [".ttf", ".otf", ".woff", ".woff2"],
    }

    OTHER_FOLDER = "Other"

    def __init__(self, categories=None):
        # allow custom rules but keep defaults if nothing is passed
        self.categories = categories if categories else self.DEFAULT_CATEGORIES
        self._ext_map = self._build_extension_map()

    def _build_extension_map(self):
        # flatten the dict so lookup is O(1)
        mapping = {}
        for folder, extensions in self.categories.items():
            for ext in extensions:
                mapping[ext.lower()] = folder
        return mapping

    def classify(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        return self._ext_map.get(ext, self.OTHER_FOLDER)

    def add_rule(self, folder_name, extensions):
        """Add or extend a category at runtime."""
        if folder_name not in self.categories:
            self.categories[folder_name] = []
        for ext in extensions:
            ext = ext.lower()
            if not ext.startswith("."):
                ext = "." + ext
            if ext not in self.categories[folder_name]:
                self.categories[folder_name].append(ext)
            self._ext_map[ext] = folder_name
