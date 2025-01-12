"""Bot launcher script."""

from src.main import main
import asyncio
import nest_asyncio

if __name__ == "__main__":
    nest_asyncio.apply()
    try:
        asyncio.run(main())
    finally:
        from src.core.user import save_user_data
        save_user_data() 
