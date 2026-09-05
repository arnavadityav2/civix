SET search_path TO civix, public;

ALTER TABLE civix.person ADD COLUMN IF NOT EXISTS avatar_url TEXT NULL;
