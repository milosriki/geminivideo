const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: '../../.env' });

const schemaPath = path.join(__dirname, '../../database_schema.sql');
const schemaSql = fs.readFileSync(schemaPath, 'utf8');

const isLocal = process.env.DATABASE_URL && (process.env.DATABASE_URL.includes('localhost') || process.env.DATABASE_URL.includes('127.0.0.1'));

const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: isLocal ? false : { rejectUnauthorized: false }
});

async function runMigration() {
    console.log('🔌 Connecting to database...');
    try {
        const client = await pool.connect();
        console.log('✅ Connected!');

        console.log('🚀 Running migration...');
        await client.query(schemaSql);
        console.log('✅ Migration completed successfully!');

        client.release();
    } catch (err) {
        console.error('❌ Migration failed:', err);
        process.exit(1);
    } finally {
        await pool.end();
    }
}

runMigration();
