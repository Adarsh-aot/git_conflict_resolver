import os
import re

class GitConflictResolverTool:
    def __init__(self, repo_path='.'):
        self.repo_path = repo_path
        self.keyword = 'WEBBAR'
        self.auto_resolved = []
        self.user_resolved = []

    def run(self, _: str) -> str:
        conflicted_files = self._find_conflicted_files()
        for file_path in conflicted_files:
            self._resolve_conflicts_in_file(file_path)

        return f"Conflicts resolved in {len(conflicted_files)} files."

    def _find_conflicted_files(self):
        conflicted_files = []
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith('.git') or '.git' in root:
                    continue
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if '<<<<<<<' in content:
                        conflicted_files.append(file_path)
        return conflicted_files

    def _resolve_conflicts_in_file(self, file_path):
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
                i += 1
                while i < len(lines) and not lines[i].startswith('>>>>>>>'):
                    incoming_block.append(lines[i])
                    i += 1
                i += 1

                current_text = ''.join(current_block)
                incoming_text = ''.join(incoming_block)

                if self.keyword in current_text:
                    resolved_lines.extend(current_block)
                    self.auto_resolved.append(file_path)
                elif self.keyword in incoming_text:
                    resolved_lines.extend(incoming_block)
                    self.auto_resolved.append(file_path)
                else:
                    print(f"\nConflict in {file_path}:")
                    print("======= Current Block =======")
                    print(current_text)
                    print("======= Incoming Block =======")
                    print(incoming_text)
                    choice = input("Select (1) Current, (2) Incoming, (3) Both: ")

                    if choice == '1':
                        resolved_lines.extend(current_block)
                    elif choice == '2':
                        resolved_lines.extend(incoming_block)
                    else:
                        resolved_lines.extend(current_block + incoming_block)

                    self.user_resolved.append(file_path)
            else:
                resolved_lines.append(lines[i])
                i += 1

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(resolved_lines)

    def generate_summary(self):
        summary = "# Git Conflict Resolution Summary\n\n"

        summary += "## Automatically Resolved (Keyword 'WEBBAR' Found)\n"
        for file in set(self.auto_resolved):
            summary += f"- {file}\n"

        summary += "\n## Resolved by User Input\n"
        for file in set(self.user_resolved):
            summary += f"- {file}\n"

        return summary
