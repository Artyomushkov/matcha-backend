cd /home/jamatchaserver/matcha-backend
git reset --hard HEAD
git pull
docker compose up -d --build --force-recreate matcha