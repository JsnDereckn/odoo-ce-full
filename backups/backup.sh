# vars
BACKUP_DIR=//home/containers/brainbc/backups/
ODOO_DATABASE=brainbc
ADMIN_PASSWORD=BrainBC2024*!

mkdir -p ${BACKUP_DIR}

curl -X POST \
-F "master_pwd=${ADMIN_PASSWORD}" \
-F "name=${ODOO_DATABASE}" \
-F "backup_format=zip" \
-o ${BACKUP_DIR}/${ODOO_DATABASE}_$(date +%u).zip \
http://localhost:8001/web/database/backup