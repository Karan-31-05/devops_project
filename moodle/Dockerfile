FROM php:8.1-apache

# Install PHP extensions required by Moodle
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpng-dev \
    libjpeg-dev \
    libfreetype6-dev \
    libicu-dev \
    libxml2-dev \
    libzip-dev \
    libldap2-dev \
    libssl-dev \
    libcurl4-openssl-dev \
    libonig-dev \
    libsodium-dev \
    zlib1g-dev \
    unzip \
    curl \
    cron \
    && docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install -j$(nproc) \
       gd \
       intl \
       mysqli \
       opcache \
       soap \
       zip \
       exif \
       sodium \
       xmlrpc \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# PHP configuration for Moodle
RUN { \
    echo 'max_execution_time = 300'; \
    echo 'memory_limit = 512M'; \
    echo 'post_max_size = 100M'; \
    echo 'upload_max_filesize = 100M'; \
    echo 'max_input_vars = 5000'; \
    echo 'date.timezone = Asia/Kolkata'; \
} > /usr/local/etc/php/conf.d/moodle.ini

# Enable opcache
RUN { \
    echo 'opcache.enable=1'; \
    echo 'opcache.memory_consumption=128'; \
    echo 'opcache.max_accelerated_files=10000'; \
    echo 'opcache.revalidate_freq=60'; \
} > /usr/local/etc/php/conf.d/opcache-recommended.ini

# Enable Apache mod_rewrite
RUN a2enmod rewrite

# Download and install Moodle 4.3
ENV MOODLE_VERSION=4.3.3
RUN curl -L https://download.moodle.org/download.php/direct/stable403/moodle-${MOODLE_VERSION}.tgz \
    -o /tmp/moodle.tgz \
    && tar -xzf /tmp/moodle.tgz -C /tmp \
    && rm -rf /var/www/html/* \
    && mv /tmp/moodle/* /var/www/html/ \
    && rm -rf /tmp/moodle /tmp/moodle.tgz \
    && chown -R www-data:www-data /var/www/html

# Create moodledata directory
RUN mkdir -p /var/www/moodledata && chown -R www-data:www-data /var/www/moodledata

# Cron job for Moodle
RUN echo "*/1 * * * * www-data /usr/local/bin/php /var/www/html/admin/cli/cron.php > /dev/null 2>&1" > /etc/cron.d/moodle-cron \
    && chmod 0644 /etc/cron.d/moodle-cron

# Startup script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
CMD ["apache2-foreground"]
