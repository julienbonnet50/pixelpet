"""
Database configuration and management
Handles PostgreSQL connections with connection pooling
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
import asyncpg
from asyncpg import Pool
import redis
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, database_url: str, redis_url: str = "redis://localhost:6379"):
        self.database_url = database_url
        self.redis_url = redis_url
        self.pool: Optional[Pool] = None
        self.redis_client: Optional[redis.Redis] = None
        
    async def initialize(self):
        """Initialize database pool and Redis connection"""
        try:
            # Create PostgreSQL connection pool
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60,
                server_settings={
                    'application_name': 'tamagotchi_bot',
                }
            )
            
            # Initialize Redis client
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connections
            await self.health_check()
            logger.info("Database connections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def health_check(self) -> Dict[str, bool]:
        """Check database and Redis health"""
        health = {"postgresql": False, "redis": False}
        
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            health["postgresql"] = True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
        
        try:
            self.redis_client.ping()
            health["redis"] = True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
        
        return health
    
    async def close(self):
        """Close all connections"""
        if self.pool:
            await self.pool.close()
        if self.redis_client:
            self.redis_client.close()
        logger.info("Database connections closed")

class PetRepository:
    """Repository pattern for pet data operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.cache_ttl = 300  # 5 minutes
    
    async def get_pet_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get pet by Discord user ID with caching"""
        cache_key = f"pet:{user_id}"
        
        # Try cache first
        if self.db.redis_client:
            cached = self.db.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        
        # Query database
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT p.*, 
                       COALESCE(json_object_agg(i.name, pi.quantity) 
                                FILTER (WHERE i.name IS NOT NULL), '{}') as items
                FROM pets p
                LEFT JOIN pet_items pi ON p.id = pi.pet_id
                LEFT JOIN items i ON pi.item_id = i.id
                WHERE p.user_id = $1
                GROUP BY p.id
            """, user_id)
        
        if not row:
            return None
        
        pet_data = dict(row)
        pet_data['birth_time'] = pet_data['birth_time'].timestamp()
        pet_data['last_update'] = pet_data['last_update'].timestamp()
        
        # Cache the result
        if self.db.redis_client:
            self.db.redis_client.setex(
                cache_key, 
                self.cache_ttl, 
                json.dumps(pet_data, default=str)
            )
        
        return pet_data
    
    async def create_pet(self, user_id: int, name: str = "Tamagotchi") -> Dict[str, Any]:
        """Create a new pet"""
        async with self.db.pool.acquire() as conn:
            async with conn.transaction():
                # Create user if not exists
                await conn.execute("""
                    INSERT INTO users (discord_id, username) 
                    VALUES ($1, 'unknown') 
                    ON CONFLICT (discord_id) DO NOTHING
                """, user_id)
                
                # Create pet
                pet_id = await conn.fetchval("""
                    INSERT INTO pets (user_id, name, birth_time)
                    VALUES ($1, $2, NOW())
                    RETURNING id
                """, user_id, name)
                
                # Add default items
                await conn.execute("""
                    INSERT INTO pet_items (pet_id, item_id, quantity)
                    SELECT $1, id, 
                           CASE 
                               WHEN name = 'medicine' THEN 1
                               WHEN name = 'toy' THEN 1
                               ELSE 0
                           END
                    FROM items
                """, pet_id)
        
        # Clear cache
        if self.db.redis_client:
            self.db.redis_client.delete(f"pet:{user_id}")
        
        return await self.get_pet_by_user_id(user_id)
    
    async def update_pet(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """Update pet data"""
        if not updates:
            return False
        
        # Build dynamic update query
        set_clauses = []
        params = [user_id]
        param_index = 2
        
        for field, value in updates.items():
            if field in ['hunger', 'happiness', 'cleanliness', 'health', 'energy', 
                        'discipline', 'level', 'experience', 'coins', 'is_sick', 
                        'is_sleeping', 'care_mistakes', 'games_won', 'games_lost']:
                set_clauses.append(f"{field} = ${param_index}")
                params.append(value)
                param_index += 1
        
        if not set_clauses:
            return False
        
        set_clauses.append(f"last_update = NOW()")
        
        query = f"""
            UPDATE pets 
            SET {', '.join(set_clauses)}
            WHERE user_id = $1
        """
        
        async with self.db.pool.acquire() as conn:
            result = await conn.execute(query, *params)
        
        # Clear cache
        if self.db.redis_client:
            self.db.redis_client.delete(f"pet:{user_id}")
        
        return result != "UPDATE 0"
    
    async def update_pet_items(self, user_id: int, item_name: str, quantity_change: int):
        """Update pet item quantity"""
        async with self.db.pool.acquire() as conn:
            await conn.execute("""
                UPDATE pet_items 
                SET quantity = GREATEST(0, quantity + $3)
                FROM pets p, items i
                WHERE pet_items.pet_id = p.id 
                AND pet_items.item_id = i.id
                AND p.user_id = $1 
                AND i.name = $2
            """, user_id, item_name, quantity_change)
        
        # Clear cache
        if self.db.redis_client:
            self.db.redis_client.delete(f"pet:{user_id}")
    
    async def get_all_active_pets(self, hours_threshold: int = 72) -> List[Dict[str, Any]]:
        """Get all pets that need attention (for background tasks)"""
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT user_id, id, name, hunger, happiness, cleanliness, health, 
                       is_sick, last_update
                FROM pets 
                WHERE last_update > NOW() - INTERVAL '%s hours'
                ORDER BY last_update ASC
            """, hours_threshold)
        
        return [dict(row) for row in rows]
    
    async def record_game_session(self, user_id: int, game_type: str, 
                                result: str, exp_gained: int, coins_gained: int):
        """Record a game session"""
        async with self.db.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO game_sessions (pet_id, game_type, result, 
                                         experience_gained, coins_gained)
                SELECT p.id, $2, $3, $4, $5
                FROM pets p
                WHERE p.user_id = $1
            """, user_id, game_type, result, exp_gained, coins_gained)

class ShopRepository:
    """Repository for shop operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def get_shop_items(self) -> List[Dict[str, Any]]:
        """Get all available shop items with caching"""
        cache_key = "shop:items"
        
        if self.db.redis_client:
            cached = self.db.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM items ORDER BY category, price")
        
        items = [dict(row) for row in rows]
        
        # Cache for 1 hour
        if self.db.redis_client:
            self.db.redis_client.setex(cache_key, 3600, json.dumps(items))
        
        return items
    
    async def purchase_item(self, user_id: int, item_name: str, 
                          quantity: int) -> Dict[str, Any]:
        """Purchase items for a pet"""
        async with self.db.pool.acquire() as conn:
            async with conn.transaction():
                # Get item info and pet coins
                row = await conn.fetchrow("""
                    SELECT i.id, i.price, p.id as pet_id, p.coins
                    FROM items i, pets p
                    WHERE i.name = $1 AND p.user_id = $2
                """, item_name, user_id)
                
                if not row:
                    return {"success": False, "error": "Item or pet not found"}
                
                total_cost = row['price'] * quantity
                if row['coins'] < total_cost:
                    return {"success": False, "error": "Insufficient coins"}
                
                # Deduct coins
                await conn.execute("""
                    UPDATE pets SET coins = coins - $1 WHERE user_id = $2
                """, total_cost, user_id)
                
                # Add items (upsert)
                await conn.execute("""
                    INSERT INTO pet_items (pet_id, item_id, quantity)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (pet_id, item_id) 
                    DO UPDATE SET quantity = pet_items.quantity + $3
                """, row['pet_id'], row['id'], quantity)
        
        return {"success": True, "cost": total_cost}