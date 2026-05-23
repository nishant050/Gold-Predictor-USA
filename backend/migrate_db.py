import sys
import logging
from app.database import engine, Base
from app.models.schemas import AppSetting

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

def run():
    logging.info("Creating any missing tables...")
    Base.metadata.create_all(bind=engine)
    logging.info("Done.")

if __name__ == "__main__":
    run()
