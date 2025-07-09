from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
from typing import Type, List
import subprocess
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


class GitConflictResolverInput(BaseModel):
    file_path: str = Field(..., description="Path to the file to resolve")
    keyword: str = Field(default="WEBBAR", description="Keyword to prioritize when resolving conflicts")


class GitConflictResolverTool(BaseTool):
    name: str = "Git Conflict Resolver"
    description: str = "Resolves Git conflicts using a keyword or interactive user input."
    args_schema: Type[BaseModel] = GitConflictResolverInput

    _auto_resolved: List[str] = PrivateAttr(default_factory=list)
    _user_resolved: List[str] = PrivateAttr(default_factory=list)
    _manual_edit_in_place: List[str] = PrivateAttr(default_factory=list)
    _keyword: str = PrivateAttr(default="WEBBAR")

    def _run(self, file_path: str, keyword: str = "WEBBAR") -> str:
        self._keyword = keyword
        self._resolve_conflicts_in_file(file_path)
        return self.generate_summary()

    def _resolve_conflicts_in_file(self, file_path: str):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        resolved_lines = []
        i = 0
        while i < len(lines):
            if lines[i].startswith("<<<<<<<"):
                current_block, incoming_block = [], []
                i += 1

                while i < len(lines) and not lines[i].startswith("======="):
                    current_block.append(lines[i])
                    i += 1
                i += 1  # skip =======

                while i < len(lines) and not lines[i].startswith(">>>>>>>"):
                    incoming_block.append(lines[i])
                    i += 1
                i += 1  # skip >>>>>>>

                current_text = "".join(current_block)
                incoming_text = "".join(incoming_block)

                current_has = self._keyword in current_text
                incoming_has = self._keyword in incoming_text

                if current_has and not incoming_has:
                    resolved_lines.extend(current_block)
                    self._auto_resolved.append(file_path)
                elif incoming_has and not current_has:
                    resolved_lines.extend(incoming_block)
                    self._auto_resolved.append(file_path)
                else:
                    self._prompt_user_resolution(
                        file_path, resolved_lines,
                        current_block, incoming_block,
                        current_text, incoming_text
                    )
                    self._user_resolved.append(file_path)
            else:
                resolved_lines.append(lines[i])
                i += 1

        if file_path not in self._manual_edit_in_place:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(resolved_lines)
        else:
            print(f"🛑 Skipped overwriting {file_path} — manual edit required.")

    def _prompt_user_resolution(
        self,
        file_path: str,
        resolved_lines: List[str],
        current_block: List[str],
        incoming_block: List[str],
        current_text: str,
        incoming_text: str
    ):
        print(f"\n🔀 Conflict in: {file_path}")
        print("======= Current Block =======")
        print(current_text)
        print("======= Incoming Block =======")
        print(incoming_text)
        print("Choose how to resolve:")
        print("1. Accept current block")
        print("2. Accept incoming block")
        print("3. Accept both blocks")
        print("4. Manual resolve (open in VS Code)")

        choice = input("Your choice (1–4): ").strip()

        if choice == "1":
            resolved_lines.extend(current_block)
        elif choice == "2":
            resolved_lines.extend(incoming_block)
        elif choice == "3":
            resolved_lines.extend(current_block + incoming_block)
        else:
            # Leave conflict markers and open editor
            resolved_lines.extend(["<<<<<<< CURRENT VERSION\n"])
            resolved_lines.extend(current_block)
            resolved_lines.append("=======\n")
            resolved_lines.extend(incoming_block)
            resolved_lines.append(">>>>>>> INCOMING VERSION\n")

            self._manual_edit_in_place.append(file_path)
            try:
                print(f"🖊️ Opening {file_path} in VS Code...")
                subprocess.run(f'code -n "{file_path}"', shell=True, check=False)
            except Exception as e:
                print(f"⚠️ Could not open VS Code: {e}")

    def generate_summary(self) -> str:
        summary = "# Git Conflict Resolution Summary\n\n"

        summary += "## ✅ Automatically Resolved (keyword matched)\n"
        for file in self._auto_resolved:
            summary += f"- {file}\n"

        summary += "\n## 👤 Resolved by User Input\n"
        for file in self._user_resolved:
            summary += f"- {file}\n"

        summary += "\n## ✍️ Manual Edits In-Place (conflict kept)\n"
        for file in self._manual_edit_in_place:
            summary += f"- {file}\n"

        summary += "\n---\nNext steps:\n- Open unresolved files in your editor\n- `git add` and `git commit`\n"
        return summary
