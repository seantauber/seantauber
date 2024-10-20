from .base_agent import BaseAgent
from datetime import datetime

class ArchiveAgent(BaseAgent):
    """
    Archive Agent: Archives editor's notes over time.
    """
    def __init__(self, archive_file: str = 'EDITOR_SUMMARIES.md'):
        super().__init__(name="ArchiveAgent")
        self.archive_file = archive_file

    def execute(self, editors_note: str):
        """
        Archives the provided editor's note to the changelog markdown file.
        
        Parameters:
            editors_note (str): The content of the editor's note to be archived.
        """
        current_date = datetime.now().strftime("%Y-%m-%d")
        entry = f"## {current_date}\n\n{editors_note}\n\n---\n\n"
        try:
            with open(self.archive_file, 'a') as f:
                f.write(entry)
            print(f"Archived editor's note to {self.archive_file}.")
        except Exception as e:
            print(f"ArchiveAgent Error archiving note: {e}")
            raise e
