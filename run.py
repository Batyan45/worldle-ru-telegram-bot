"""Bot launcher script."""

import sys
from pathlib import Path

# Add the src directory to Python path
src_path = str(Path(__file__).parent / "src")
sys.path.insert(0, src_path)

from main import main
import asyncio
import nest_asyncio

if __name__ == "__main__":
    nest_asyncio.apply()
    try:
        asyncio.run(main())
    finally:
        from core.user import save_user_data
        save_user_data() 