
-- Migration: Remove course_id from arena_exercise_progress and user_arena_profiles

-- ============================================
-- 1. arena_exercise_progress (deduplicate first)
-- ============================================

-- Create temp table with deduplication (keep latest updated_at)
CREATE TABLE arena_exercise_progress_dedup AS
SELECT *
FROM arena_exercise_progress
WHERE rowid IN (
    SELECT MAX(rowid)
    FROM arena_exercise_progress
    GROUP BY user_id, exercise_id
);

-- Create new table without course_id
CREATE TABLE arena_exercise_progress_new (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    exercise_id INTEGER NOT NULL,
    exercise_index INTEGER NOT NULL,
    is_completed BOOLEAN DEFAULT 0,
    is_correct BOOLEAN DEFAULT 0,
    is_unlocked BOOLEAN DEFAULT 0,
    stars_awarded INTEGER DEFAULT 0,
    stars_deducted INTEGER DEFAULT 0,
    saved_codes JSON DEFAULT '{}',
    current_language VARCHAR(20) DEFAULT 'python',
    first_attempt_at DATETIME,
    last_attempt_at DATETIME,
    correct_at DATETIME,
    attempt_count INTEGER DEFAULT 0,
    time_spent INTEGER,
    hint_used BOOLEAN DEFAULT 0,
    first_attempt_correct BOOLEAN,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, exercise_id)
);

INSERT INTO arena_exercise_progress_new (
    id, user_id, exercise_id, exercise_index, is_completed, is_correct, is_unlocked,
    stars_awarded, stars_deducted, saved_codes, current_language,
    first_attempt_at, last_attempt_at, correct_at, attempt_count,
    time_spent, hint_used, first_attempt_correct, created_at, updated_at
)
SELECT 
    id, user_id, exercise_id, exercise_index, is_completed, is_correct, is_unlocked,
    stars_awarded, stars_deducted, saved_codes, current_language,
    first_attempt_at, last_attempt_at, correct_at, attempt_count,
    time_spent, hint_used, first_attempt_correct, created_at, updated_at
FROM arena_exercise_progress_dedup;

DROP TABLE arena_exercise_progress;
DROP TABLE arena_exercise_progress_dedup;
ALTER TABLE arena_exercise_progress_new RENAME TO arena_exercise_progress;

CREATE INDEX idx_arena_progress_user ON arena_exercise_progress(user_id);
CREATE INDEX idx_arena_progress_user_index ON arena_exercise_progress(user_id, exercise_index);

-- ============================================
-- 2. user_arena_profiles (keep one per user)
-- ============================================

-- Create new table without course_id
CREATE TABLE user_arena_profiles_new (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL UNIQUE,
    total_score FLOAT DEFAULT 0.0,
    tier VARCHAR(20) DEFAULT 'bronze',
    rank INTEGER,
    sub_tier INTEGER DEFAULT 4,
    stars INTEGER DEFAULT 0,
    protection_remaining INTEGER DEFAULT 3,
    highest_tier VARCHAR(20),
    highest_sub_tier INTEGER,
    total_challenges INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    highest_difficulty INTEGER DEFAULT 0,
    best_streak INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    avg_accuracy FLOAT DEFAULT 0.0,
    behavior_embedding TEXT,
    avg_time_spent FLOAT DEFAULT 0.0,
    total_submissions INTEGER DEFAULT 0,
    total_time_spent INTEGER DEFAULT 0,
    last_challenge_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Keep first profile per user (by id, arbitrary)
INSERT INTO user_arena_profiles_new (
    id, user_id, total_score, tier, rank, sub_tier, stars,
    protection_remaining, highest_tier, highest_sub_tier,
    total_challenges, wins, losses, highest_difficulty,
    best_streak, current_streak, avg_accuracy,
    behavior_embedding, avg_time_spent, total_submissions,
    total_time_spent, last_challenge_at, created_at, updated_at
)
SELECT 
    id, user_id, total_score, tier, rank, sub_tier, stars,
    protection_remaining, highest_tier, highest_sub_tier,
    total_challenges, wins, losses, highest_difficulty,
    best_streak, current_streak, avg_accuracy,
    behavior_embedding, avg_time_spent, total_submissions,
    total_time_spent, last_challenge_at, created_at, updated_at
FROM user_arena_profiles
GROUP BY user_id;

DROP TABLE user_arena_profiles;
ALTER TABLE user_arena_profiles_new RENAME TO user_arena_profiles;

CREATE INDEX idx_arena_user ON user_arena_profiles(user_id);
CREATE INDEX idx_arena_score ON user_arena_profiles(total_score);
