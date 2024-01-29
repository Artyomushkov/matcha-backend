CREATE TABLE IF NOT EXISTS profile (
    id UUID PRIMARY KEY NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(150),
    email VARCHAR(50) UNIQUE NOT NULL,
    firstName VARCHAR(50) NOT NULL,
    lastName VARCHAR(50) NOT NULL,
    dateOfBirth BIGINT,
    emailVerified BOOLEAN,
    gender VARCHAR(10),
    sexPref VARCHAR(10),
    biography VARCHAR(300),
    tagList TEXT[],
    mainImage VARCHAR(150),
    pictures TEXT[],
    GPSlat DOUBLE PRECISION,
    GPSlon DOUBLE PRECISION,
    isOnline BOOLEAN,
    lastSeen BIGINT,
    likedMe TEXT[],
    viewedMe TEXT[],
    liked TEXT[],
    viewed TEXT[],
    blacklist TEXT[],
    fameRating DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY NOT NULL,
    tag VARCHAR(50) UNIQUE NOT NULL
);

CREATE OR REPLACE FUNCTION array_intersection_count(arr1 TEXT[], arr2 TEXT[])
RETURNS INTEGER AS $$
DECLARE
    intersection_count INTEGER := 0;
    element TEXT;
BEGIN
    FOREACH element IN ARRAY arr1
    LOOP
        IF element = ANY(arr2) THEN
            intersection_count := intersection_count + 1;
        END IF;
    END LOOP;

    RETURN intersection_count;
END;
$$ LANGUAGE plpgsql;