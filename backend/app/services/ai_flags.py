# app/services/ai_flags.py

import os

USE_LOCAL_AI = os.getenv("USE_LOCAL_AI", "false").lower() == "true"
