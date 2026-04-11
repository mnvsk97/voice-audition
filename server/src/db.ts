import Database from 'better-sqlite3';
import { resolve } from 'path';

const DB_PATH = process.env.VOICE_AUDITION_CATALOG_DB_PATH
  || resolve(import.meta.dirname, '../../catalog/voice_catalog.db');

let _db: Database.Database | null = null;

export function db(): Database.Database {
  if (!_db) {
    _db = new Database(DB_PATH, { readonly: true });
  }
  return _db;
}
