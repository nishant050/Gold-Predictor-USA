from app.utils.log_capture import setup_llm_log_capture, get_recent_llm_logs
import logging

setup_llm_log_capture()

l1 = logging.getLogger("app.services.llm_agent")
l1.info("Test agent info")
l1.error("Test agent error")

l2 = logging.getLogger("app.services.llm_service")
l2.info("Test service info")

logs = get_recent_llm_logs()
print("LOGS:", logs)
