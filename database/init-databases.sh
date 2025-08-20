#!/bin/bash
set -e

# Create multiple databases for AI Interviewer system
# This script is run during PostgreSQL container initialization

echo "=== AI Interviewer Database Initialization Script ==="
echo "Current user: $POSTGRES_USER"
echo "Default database: $POSTGRES_DB"
echo "Additional databases requested: $POSTGRES_MULTIPLE_DATABASES"

function create_database() {
    local database=$1
    echo "Creating database '$database' if it doesn't exist..."
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        SELECT 'CREATE DATABASE $database'
        WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$database')\gexec
EOSQL
    echo "✅ Database '$database' is ready."
}

function grant_privileges() {
    local database=$1
    local username=$2
    echo "Granting privileges on '$database' to '$username'..."
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        GRANT ALL PRIVILEGES ON DATABASE $database TO $username;
EOSQL
    echo "✅ Privileges granted on '$database' to '$username'"
}

# Always create ai_interviewer database for the application
echo "🔧 Creating AI Interviewer application database..."
create_database "ai_interviewer"
grant_privileges "ai_interviewer" "$POSTGRES_USER"

# Create additional databases if specified
if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
    echo "🔧 Creating additional databases: $POSTGRES_MULTIPLE_DATABASES"
    
    # Split the comma-separated list and create each database
    IFS=',' read -ra DATABASES <<< "$POSTGRES_MULTIPLE_DATABASES"
    for database in "${DATABASES[@]}"; do
        # Trim whitespace
        database=$(echo "$database" | xargs)
        
        # Skip if it's the default database or ai_interviewer (already created)
        if [ "$database" != "$POSTGRES_DB" ] && [ "$database" != "ai_interviewer" ]; then
            create_database "$database"
            grant_privileges "$database" "$POSTGRES_USER"
        else
            echo "ℹ️  Skipping '$database' (already exists or is default)"
        fi
    done
    
    echo "✅ Additional database initialization completed."
else
    echo "ℹ️  No additional databases specified."
fi

# List all databases for verification
echo "📋 Final database list:"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -c "\l"

echo "🎉 Database initialization script completed successfully!"