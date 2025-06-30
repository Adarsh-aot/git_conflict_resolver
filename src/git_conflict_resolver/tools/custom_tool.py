from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
import os
from typing import Type, List

class GitConflictFinderInput(BaseModel):
    """Input schema for GitConflictFinderTool."""
    repo_path: str = Field(..., description="Path to the repository where conflicts need to be found.", path='{directory}')

class GitConflictFinderTool(BaseTool):
    name: str = "Git Conflict Finder"
    description: str = "A tool that finds git conflicts in a repository."
    args_schema: Type[BaseModel] = GitConflictFinderInput

    def _run(self, repo_path: str) -> str:
        conflicted_files = self._find_conflicted_files(repo_path)
        return f"Found conflicts in {len(conflicted_files)} files: {conflicted_files}"

    def _find_conflicted_files(self, repo_path: str) -> List[str]:
        conflicted_files = []
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.git') or '.git' in root:
                    continue
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if '<<<<<<<' in content:
                            conflicted_files.append(file_path)
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
        return conflicted_files

class GitConflictResolverInput(BaseModel):
    file_path: str = Field(..., description="Path to the file with git conflicts.")
    keyword: str = Field(default="WEBBAR", description="Keyword to prioritize in resolving conflicts.")

class GitConflictResolverTool(BaseTool):
    name: str = "Git Conflict Resolver"
    description: str = "Resolves git conflicts using a keyword or prompts the user if necessary."
    args_schema: Type[BaseModel] = GitConflictResolverInput

    _auto_resolved: list = PrivateAttr(default_factory=list)
    _user_resolved: list = PrivateAttr(default_factory=list)
    _keyword: str = PrivateAttr(default="WEBBAR")

    def _run(self, file_path: str, keyword: str = "WEBBAR") -> str:
        self._keyword = keyword
        self._resolve_conflicts_in_file(file_path)
        return self.generate_summary()

    def _resolve_conflicts_in_file(self, file_path: str):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        resolved_lines = []
        i = 0
        while i < len(lines):
            if lines[i].startswith('<<<<<<<'):
                current_block = []
                incoming_block = []
                i += 1

                while i < len(lines) and not lines[i].startswith('======='):
                    current_block.append(lines[i])
                    i += 1
                i += 1  # skip =======
                while i < len(lines) and not lines[i].startswith('>>>>>>>'):
                    incoming_block.append(lines[i])
                    i += 1
                i += 1  # skip >>>>>>>

                current_text = ''.join(current_block)
                incoming_text = ''.join(incoming_block)

                if self._keyword in current_text:
                    resolved_lines.extend(current_block)
                    self._auto_resolved.append(file_path)
                elif self._keyword in incoming_text:
                    resolved_lines.extend(incoming_block)
                    self._auto_resolved.append(file_path)
                else:
                    # User interaction
                    print(f"\nConflict in {file_path}:")
                    print("======= Current Block =======")
                    print(current_text)
                    print("======= Incoming Block =======")
                    print(incoming_text)
                    print("======= Options =======")
                    print("1. Accept current block")
                    print("2. Accept incoming block")
                    print("3. Accept both blocks")
                    print("4. Manually resolve")

                    choice = input("Choose option (1-4): ").strip()

                    if choice == '1':
                        resolved_lines.extend(current_block)
                    elif choice == '2':
                        resolved_lines.extend(incoming_block)
                    elif choice == '3':
                        resolved_lines.extend(current_block + incoming_block)
                    elif choice == '4':
                        print("\n======= Full Conflict Block =======")
                        print("".join(current_block + ['=======\n'] + incoming_block))
                        manual_input = input("Paste your manual resolution here:\n")
                        resolved_lines.append(manual_input + '\n')
                    else:
                        print("Invalid choice. Defaulting to keeping both.")
                        resolved_lines.extend(current_block + ['=======\n'] + incoming_block)

                    self._user_resolved.append(file_path)
            else:
                resolved_lines.append(lines[i])
                i += 1

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(resolved_lines)

    def generate_summary(self) -> str:
        summary = "# Git Conflict Resolution Summary\n\n"

        summary += "## Automatically Resolved (Keyword found)\n"
        for file in set(self._auto_resolved):
            summary += f"- {file}\n"

        summary += "\n## Resolved by User Input\n"
        for file in set(self._user_resolved):
            summary += f"- {file}\n"

        return summary
