#!/bin/bash
set -e

# Wait for database
echo "Waiting for MariaDB to be ready..."
while ! php -r "new mysqli('${MOODLE_DB_HOST}', '${MOODLE_DB_USER}', '${MOODLE_DB_PASS}', '', ${MOODLE_DB_PORT:-3306});" 2>/dev/null; do
    echo "  MariaDB not ready yet, waiting..."
    sleep 3
done
echo "MariaDB is ready!"

CONFIG_FILE="/var/www/html/config.php"

# Check if Moodle is already installed
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Installing Moodle..."
    
    cd /var/www/html
    
    php admin/cli/install.php \
        --lang=en \
        --wwwroot="${MOODLE_URL:-http://localhost:8080}" \
        --dataroot=/var/www/moodledata \
        --dbtype=mariadb \
        --dbhost="${MOODLE_DB_HOST}" \
        --dbport="${MOODLE_DB_PORT:-3306}" \
        --dbname="${MOODLE_DB_NAME}" \
        --dbuser="${MOODLE_DB_USER}" \
        --dbpass="${MOODLE_DB_PASS}" \
        --fullname="${MOODLE_SITE_NAME:-CSE Department LMS}" \
        --shortname="${MOODLE_SITE_SHORT:-CSE-LMS}" \
        --adminuser="${MOODLE_ADMIN_USER:-admin}" \
        --adminpass="${MOODLE_ADMIN_PASS:-Admin@1234}" \
        --adminemail="${MOODLE_ADMIN_EMAIL:-admin@college.edu}" \
        --agree-license \
        --non-interactive
    
    echo "Moodle installation complete!"
    
    # Enable web services via CLI
    echo "Enabling Web Services..."
    php admin/cli/cfg.php --name=enablewebservices --set=1
    php admin/cli/cfg.php --name=enablemobilewebservice --set=1
    
    echo "Web Services enabled!"
else
    echo "Moodle already installed, skipping installation."
fi

# Fix permissions
chown -R www-data:www-data /var/www/html /var/www/moodledata

# Start cron in background
service cron start 2>/dev/null || true

echo "Starting Apache..."
exec "$@"
