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
    id UUID PRIMARY KEY NOT NULL,
    tag VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS chat (
    id UUID PRIMARY KEY NOT NULL,
    userOneId UUID NOT NULL,
    userTwoId UUID NOT NULL,
    dateCreated BIGINT
);

CREATE TABLE IF NOT EXISTS message (
    id UUID PRIMARY KEY NOT NULL,
    chatId UUID NOT NULL,
    authorId UUID NOT NULL,
    content VARCHAR(300),
    dateCreated BIGINT
);

CREATE TABLE IF NOT EXISTS notification (
    id UUID PRIMARY KEY NOT NULL,
    recipientId UUID NOT NULL,
    actorId UUID NOT NULL,
    type VARCHAR(50) NOT NULL,
    dateCreated BIGINT
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

CREATE OR REPLACE FUNCTION calculate_distance(lat1 FLOAT, lon1 FLOAT, lat2 FLOAT, lon2 FLOAT)
RETURNS FLOAT AS $$
DECLARE
    dLat FLOAT;
    dLon FLOAT;
    a FLOAT;
    c FLOAT;
    distance FLOAT;
BEGIN
    dLat := RADIANS(lat2 - lat1);
    dLon := RADIANS(lon2 - lon1);
    lat1 := RADIANS(lat1);
    lat2 := RADIANS(lat2);

    a := SIN(dLat / 2) * SIN(dLat / 2) + SIN(dLon / 2) * SIN(dLon / 2) * COS(lat1) * COS(lat2);
    c := 2 * ATAN2(SQRT(a), SQRT(1 - a));
    distance := 6371 * c; -- Radius of the Earth in kilometers (change if using miles)

    RETURN distance;
END;
$$ LANGUAGE PLPGSQL;
