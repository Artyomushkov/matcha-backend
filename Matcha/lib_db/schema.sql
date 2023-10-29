CREATE TABLE IF NOT EXISTS profile (
    id UUID PRIMARY KEY NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(150),
    email VARCHAR(50) UNIQUE NOT NULL,
    firstName VARCHAR(50) NOT NULL,
    lastName VARCHAR(50) NOT NULL,
    dateOfBirth INTEGER,
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
    lastSeen INTEGER,
    likedMe TEXT[],
    viewedMe TEXT[],
    liked TEXT[],
    viewed TEXT[],
    blacklist TEXT[],
    fameRating DOUBLE PRECISION
);