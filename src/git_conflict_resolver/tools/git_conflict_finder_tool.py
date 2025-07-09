from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, List
import os

class GitConflictFinderInput(BaseModel):
    """Input schema for GitConflictFinderTool."""
    file_list_path: str = Field(..., description="Path to the file containing list of file paths to scan.")

class GitConflictFinderTool(BaseTool):
    name: str = "Git Conflict Finder"
    description: str = "Scans files listed in a .txt file and finds Git merge conflicts."
    args_schema: Type[BaseModel] = GitConflictFinderInput

    def _run(self, file_list_path: str) -> str:
        conflicted_files = self._find_conflicted_files(file_list_path)
        if not conflicted_files:
            return "✅ No conflicts found in any of the listed files."
        return f"⚠️ Found conflicts in {len(conflicted_files)} files:\n" + "\n".join(conflicted_files)

    def _find_conflicted_files(self, file_list_path: str) -> List[str]:
        conflicted_files = []

        if not os.path.exists(file_list_path):
            return [f"❌ File list not found: {file_list_path}"]

        with open(file_list_path, 'r', encoding='utf-8') as f:
            file_paths = [line.strip('- ').strip() for line in f if line.strip()]

        for path in file_paths:
            if not os.path.isfile(path):
                print(f"⚠️ Skipping: {path} (not a valid file)")
                continue
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.read()
                    if '<<<<<<<' in content and '=======' in content and '>>>>>>>' in content:
                        conflicted_files.append(path)
            except Exception as e:
                print(f"❌ Error reading {path}: {e}")

        return conflicted_files
