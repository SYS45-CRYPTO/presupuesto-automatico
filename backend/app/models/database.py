from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost/construction_budgets")
SYNC_DATABASE_URL = os.getenv("SYNC_DATABASE_URL", "postgresql://postgres:password@localhost/construction_budgets")

# Engine asíncrono para operaciones
async_engine = create_async_engine(DATABASE_URL, echo=True)

# Engine síncrono para migraciones
sync_engine = create_engine(SYNC_DATABASE_URL.replace("+asyncpg", ""), echo=True)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

# Dependency para obtener sesión de BD
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()