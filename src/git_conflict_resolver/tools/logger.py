import logging

logger = logging.getLogger("git_conflict_ai")
logger.setLevel(logging.INFO)

# Prevent adding multiple handlers if reimported
if not logger.handlers:
    file_handler = logging.FileHandler("ai_git_resolution.log")
    file_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
