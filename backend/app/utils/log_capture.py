import logging
from collections import deque
from datetime import datetime

# In-memory queue to store the latest logs
# 500 should be plenty for a single LLM run
_llm_log_queue = deque(maxlen=500)

class MemoryLogHandler(logging.Handler):
    def emit(self, record):
        # Format the log record
        try:
            msg = self.format(record)
            timestamp = datetime.fromtimestamp(record.created).isoformat()
            
            # Append to the right of the deque
            _llm_log_queue.append({
                "timestamp": timestamp,
                "level": record.levelname,
                "logger": record.name,
                "message": msg
            })
        except Exception:
            self.handleError(record)

def get_recent_llm_logs() -> list:
    """Return all logs currently in the queue as a list of dicts."""
    return list(_llm_log_queue)

def clear_llm_logs():
    """Clear the log queue."""
    _llm_log_queue.clear()

def setup_llm_log_capture():
    """Attach the MemoryLogHandler to specific LLM loggers."""
    handler = MemoryLogHandler()
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    
    # We specifically want to capture logs from llm_agent, llm_service, and llm_tools
    loggers_to_capture = [
        "app.services.llm_agent",
        "app.services.llm_service",
        "app.services.llm_tools"
    ]
    
    for logger_name in loggers_to_capture:
        l = logging.getLogger(logger_name)
        l.setLevel(logging.INFO)
        l.addHandler(handler)
