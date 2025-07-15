import aiomysql
from aiogram import types
from config import config
import logging
from typing import List, Optional, Dict

class Database:
    def __init__(self):
        self.pool = None
        self.logger = logging.getLogger(__name__)

    async def connect(self):
        try:
            self.pool = await aiomysql.create_pool(**config.DB_CONFIG)
            self.logger.info("✅ Успешное подключение к БД")
        except Exception as e:
            self.logger.error(f"❌ Ошибка подключения к БД: {e}")
            raise

    async def close(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.logger.info("Соединение с БД закрыто")

    async def save_user(self, user: types.User):
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        INSERT INTO users (user_id, username, first_name, last_name)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        username = VALUES(username),
                        last_activity = NOW()
                    """, (user.id, user.username, user.first_name, user.last_name))
                    await conn.commit()
                    self.logger.info(f"Пользователь {user.id} сохранен")
        except Exception as e:
            self.logger.error(f"Ошибка сохранения пользователя: {e}")
            raise

    async def save_mood(self, user_id: int, mood_value: int):
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        INSERT INTO mood_entries (user_id, mood_value)
                        VALUES (%s, %s)
                    """, (user_id, mood_value))
                    await conn.commit()
                    self.logger.info(f"Настроение пользователя {user_id} сохранено")
        except Exception as e:
            self.logger.error(f"Ошибка сохранения настроения: {e}")
            raise

    async def get_user_stats(self, user_id: int) -> Dict[str, float]:
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute("""
                        SELECT 
                            AVG(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) 
                            THEN mood_value END) as weekly_avg,
                            AVG(mood_value) as monthly_avg
                        FROM mood_entries 
                        WHERE user_id = %s
                    """, (user_id,))
                    result = await cursor.fetchone()
                    self.logger.info(f"Статистика для {user_id}: {result}")
                    return result or {'weekly_avg': 0, 'monthly_avg': 0}
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики: {e}")
            return {'weekly_avg': 0, 'monthly_avg': 0}

    async def get_all_users(self) -> List[int]:
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT user_id FROM users WHERE notifications_enabled = TRUE")
                    return [row[0] for row in await cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Ошибка получения пользователей: {e}")
            return []

    async def update_notification_settings(self, user_id: int, enabled: bool):
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        INSERT INTO users (user_id, notifications_enabled)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE
                        notifications_enabled = VALUES(notifications_enabled)
                    """, (user_id, enabled))
                    await conn.commit()
                    self.logger.info(f"Настройки уведомлений пользователя {user_id} обновлены")
        except Exception as e:
            self.logger.error(f"Ошибка обновления настроек уведомлений: {e}")
            raise

db = Database()







