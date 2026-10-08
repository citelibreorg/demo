echo "[INIT DB] Creating database $INIT_DATABASE_NAME on host $INIT_DATABASE_HOST for app user $INIT_APP_USER"
mariadb --user=root -h $INIT_DATABASE_HOST -e "create database $INIT_DATABASE_NAME"

echo "[INIT DB] process init dump or sql files"
for filename in /sql/*.sql; do
  echo "[INIT DB] process file $filename"
  mariadb --user=root -h $INIT_DATABASE_HOST -D $INIT_DATABASE_NAME < $filename
done

echo "[INIT DB] Grant all privileges on $INIT_DATABASE_NAME.* TO '$INIT_APP_USER'@'%'"
mariadb --user=root -h $INIT_DATABASE_HOST -e "GRANT ALL PRIVILEGES ON $INIT_DATABASE_NAME.* TO '$INIT_APP_USER'@'%'"