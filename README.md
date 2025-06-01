# pixelpet
pixelpet

# POSTGRE SQL

```sql
-- Users table
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    discord_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pets table
CREATE TABLE pets (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(discord_id),
    name VARCHAR(100) NOT NULL DEFAULT 'PixelPet',
    birth_time TIMESTAMP NOT NULL,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    stage VARCHAR(20) DEFAULT 'egg',
    level INTEGER DEFAULT 1,
    experience INTEGER DEFAULT 0,
    
    -- Core stats
    hunger INTEGER DEFAULT 80 CHECK (hunger >= 0 AND hunger <= 100),
    happiness INTEGER DEFAULT 80 CHECK (happiness >= 0 AND happiness <= 100),
    cleanliness INTEGER DEFAULT 80 CHECK (cleanliness >= 0 AND cleanliness <= 100),
    health INTEGER DEFAULT 100 CHECK (health >= 0 AND health <= 100),
    energy INTEGER DEFAULT 100 CHECK (energy >= 0 AND energy <= 100),
    discipline INTEGER DEFAULT 50 CHECK (discipline >= 0 AND discipline <= 100),
    
    -- Status flags
    is_sick BOOLEAN DEFAULT FALSE,
    is_sleeping BOOLEAN DEFAULT FALSE,
    sleep_time TIMESTAMP NULL,
    
    -- Care tracking
    last_fed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_cleaned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    care_mistakes INTEGER DEFAULT 0,
    
    -- Currency and items
    coins INTEGER DEFAULT 10,
    
    -- Game stats
    games_won INTEGER DEFAULT 0,
    games_lost INTEGER DEFAULT 0,
    training_sessions INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Items table
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    price INTEGER NOT NULL,
    description TEXT,
    category VARCHAR(20) NOT NULL
);

-- Pet items (inventory)
CREATE TABLE pet_items (
    id SERIAL PRIMARY KEY,
    pet_id INTEGER REFERENCES pets(id),
    item_id INTEGER REFERENCES items(id),
    quantity INTEGER DEFAULT 0,
    UNIQUE(pet_id, item_id)
);

-- Game sessions for tracking mini-games
CREATE TABLE game_sessions (
    id SERIAL PRIMARY KEY,
    pet_id INTEGER REFERENCES pets(id),
    game_type VARCHAR(50) NOT NULL,
    result VARCHAR(20) NOT NULL, -- 'win', 'lose', 'draw'
    experience_gained INTEGER DEFAULT 0,
    coins_gained INTEGER DEFAULT 0,
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better performance
CREATE INDEX idx_pets_user_id ON pets(user_id);
CREATE INDEX idx_pets_last_update ON pets(last_update);
CREATE INDEX idx_game_sessions_pet_id ON game_sessions(pet_id);
CREATE INDEX idx_pet_items_pet_id ON pet_items(pet_id);
```