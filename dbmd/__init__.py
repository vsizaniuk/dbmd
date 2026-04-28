import os
import logging

from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

LOG_LEVEL = os.environ.get('MDDB_LOG_LEVEL', 'INFO')
WRITE_LOG_FILE = bool(int(os.environ.get('MDDB_WRITE_LOG_FILE', 0)))
LOG_FILE_NAME = f'mddb_{datetime.now().isoformat()}.log' if WRITE_LOG_FILE else None

logging.basicConfig(format='%(levelname)s:t:%(asctime)s:%(module)s.%(funcName)s:%(message)s',
                    level=LOG_LEVEL,
                    filename=LOG_FILE_NAME,
                    encoding='utf-8',
                    filemode='w')
