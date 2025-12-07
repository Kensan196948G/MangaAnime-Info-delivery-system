import sqlite3 from 'sqlite3';
import { open, Database } from 'sqlite';
import path from 'path';
import fs from 'fs/promises';

export interface MemoryConfig {
  dbPath: string;
  inMemory: boolean;
  persistentStorage: boolean;
  cacheSizeMB: number;
  walMode: boolean;
  synchronous: 'OFF' | 'NORMAL' | 'FULL';
}

export interface MemoryEntry {
  id: string;
  category: string;
  key: string;
  value: any;
  metadata: Record<string, any>;
  timestamp: number;
  ttl?: number;
  priority: number;
}

export class SQLiteMemory {
  private db: Database | null = null;
  private config: MemoryConfig;
  private cache: Map<string, MemoryEntry> = new Map();
  private cleanupInterval: NodeJS.Timeout | null = null;

  constructor(config: Partial<MemoryConfig> = {}) {
    this.config = {
      dbPath: path.join(process.cwd(), '.claude', 'memory.db'),
      inMemory: false,
      persistentStorage: true,
      cacheSizeMB: 512,
      walMode: true,
      synchronous: 'NORMAL',
      ...config
    };
  }

  async initialize(): Promise<void> {
    const dbPath = this.config.inMemory ? ':memory:' : this.config.dbPath;
    
    // Ensure directory exists
    if (!this.config.inMemory) {
      await fs.mkdir(path.dirname(this.config.dbPath), { recursive: true });
    }

    this.db = await open({
      filename: dbPath,
      driver: sqlite3.Database
    });

    // Configure database
    await this.configureDatabase();
    
    // Create tables
    await this.createTables();
    
    // Start cleanup interval
    this.startCleanup();
    
    // Load persistent data into cache
    if (this.config.persistentStorage && !this.config.inMemory) {
      await this.loadCache();
    }
  }

  private async configureDatabase(): Promise<void> {
    if (!this.db) return;

    // Set cache size
    const cacheSizeKB = this.config.cacheSizeMB * 1024;
    await this.db.exec(`PRAGMA cache_size = -${cacheSizeKB}`);
    
    // Set WAL mode for better concurrency
    if (this.config.walMode) {
      await this.db.exec('PRAGMA journal_mode = WAL');
    }
    
    // Set synchronous mode
    await this.db.exec(`PRAGMA synchronous = ${this.config.synchronous}`);
    
    // Enable foreign keys
    await this.db.exec('PRAGMA foreign_keys = ON');
    
    // Optimize for speed
    await this.db.exec('PRAGMA temp_store = MEMORY');
    await this.db.exec('PRAGMA mmap_size = 30000000000');
  }

  private async createTables(): Promise<void> {
    if (!this.db) return;

    await this.db.exec(`
      CREATE TABLE IF NOT EXISTS memory (
        id TEXT PRIMARY KEY,
        category TEXT NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        metadata TEXT,
        timestamp INTEGER NOT NULL,
        ttl INTEGER,
        priority INTEGER DEFAULT 5,
        UNIQUE(category, key)
      );

      CREATE INDEX IF NOT EXISTS idx_memory_category ON memory(category);
      CREATE INDEX IF NOT EXISTS idx_memory_key ON memory(key);
      CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON memory(timestamp);
      CREATE INDEX IF NOT EXISTS idx_memory_priority ON memory(priority);

      CREATE TABLE IF NOT EXISTS memory_stats (
        category TEXT PRIMARY KEY,
        count INTEGER DEFAULT 0,
        total_size INTEGER DEFAULT 0,
        last_access INTEGER,
        access_count INTEGER DEFAULT 0
      );

      CREATE TABLE IF NOT EXISTS memory_relationships (
        source_id TEXT,
        target_id TEXT,
        relationship_type TEXT,
        weight REAL DEFAULT 1.0,
        created_at INTEGER,
        PRIMARY KEY (source_id, target_id, relationship_type),
        FOREIGN KEY (source_id) REFERENCES memory(id) ON DELETE CASCADE,
        FOREIGN KEY (target_id) REFERENCES memory(id) ON DELETE CASCADE
      );
    `);
  }

  async set(
    category: string,
    key: string,
    value: any,
    metadata: Record<string, any> = {},
    ttl?: number,
    priority: number = 5
  ): Promise<string> {
    if (!this.db) throw new Error('Database not initialized');

    const id = `${category}:${key}`;
    const timestamp = Date.now();
    const entry: MemoryEntry = {
      id,
      category,
      key,
      value,
      metadata,
      timestamp,
      ttl,
      priority
    };

    // Update cache
    this.cache.set(id, entry);

    // Persist to database
    await this.db.run(
      `INSERT OR REPLACE INTO memory 
       (id, category, key, value, metadata, timestamp, ttl, priority)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        id,
        category,
        key,
        JSON.stringify(value),
        JSON.stringify(metadata),
        timestamp,
        ttl,
        priority
      ]
    );

    // Update stats
    await this.updateStats(category);

    return id;
  }

  async get(category: string, key: string): Promise<any | null> {
    const id = `${category}:${key}`;
    
    // Check cache first
    if (this.cache.has(id)) {
      const entry = this.cache.get(id)!;
      if (!this.isExpired(entry)) {
        return entry.value;
      } else {
        this.cache.delete(id);
      }
    }

    if (!this.db) throw new Error('Database not initialized');

    // Load from database
    const row = await this.db.get(
      'SELECT * FROM memory WHERE id = ?',
      [id]
    );

    if (row) {
      const entry: MemoryEntry = {
        id: row.id,
        category: row.category,
        key: row.key,
        value: JSON.parse(row.value),
        metadata: JSON.parse(row.metadata || '{}'),
        timestamp: row.timestamp,
        ttl: row.ttl,
        priority: row.priority
      };

      if (!this.isExpired(entry)) {
        this.cache.set(id, entry);
        return entry.value;
      } else {
        await this.delete(category, key);
      }
    }

    return null;
  }

  async getByCategory(category: string): Promise<MemoryEntry[]> {
    if (!this.db) throw new Error('Database not initialized');

    const rows = await this.db.all(
      'SELECT * FROM memory WHERE category = ? ORDER BY priority DESC, timestamp DESC',
      [category]
    );

    return rows
      .map(row => ({
        id: row.id,
        category: row.category,
        key: row.key,
        value: JSON.parse(row.value),
        metadata: JSON.parse(row.metadata || '{}'),
        timestamp: row.timestamp,
        ttl: row.ttl,
        priority: row.priority
      }))
      .filter(entry => !this.isExpired(entry));
  }

  async delete(category: string, key: string): Promise<boolean> {
    if (!this.db) throw new Error('Database not initialized');

    const id = `${category}:${key}`;
    this.cache.delete(id);

    const result = await this.db.run(
      'DELETE FROM memory WHERE id = ?',
      [id]
    );

    return result.changes! > 0;
  }

  async search(query: string, limit: number = 10): Promise<MemoryEntry[]> {
    if (!this.db) throw new Error('Database not initialized');

    const rows = await this.db.all(
      `SELECT * FROM memory 
       WHERE key LIKE ? OR value LIKE ? OR metadata LIKE ?
       ORDER BY priority DESC, timestamp DESC
       LIMIT ?`,
      [`%${query}%`, `%${query}%`, `%${query}%`, limit]
    );

    return rows
      .map(row => ({
        id: row.id,
        category: row.category,
        key: row.key,
        value: JSON.parse(row.value),
        metadata: JSON.parse(row.metadata || '{}'),
        timestamp: row.timestamp,
        ttl: row.ttl,
        priority: row.priority
      }))
      .filter(entry => !this.isExpired(entry));
  }

  async addRelationship(
    sourceId: string,
    targetId: string,
    relationshipType: string,
    weight: number = 1.0
  ): Promise<void> {
    if (!this.db) throw new Error('Database not initialized');

    await this.db.run(
      `INSERT OR REPLACE INTO memory_relationships 
       (source_id, target_id, relationship_type, weight, created_at)
       VALUES (?, ?, ?, ?, ?)`,
      [sourceId, targetId, relationshipType, weight, Date.now()]
    );
  }

  async getRelated(id: string, relationshipType?: string): Promise<MemoryEntry[]> {
    if (!this.db) throw new Error('Database not initialized');

    let query = `
      SELECT m.* FROM memory m
      JOIN memory_relationships r ON (m.id = r.target_id OR m.id = r.source_id)
      WHERE (r.source_id = ? OR r.target_id = ?) AND m.id != ?
    `;
    
    const params: any[] = [id, id, id];
    
    if (relationshipType) {
      query += ' AND r.relationship_type = ?';
      params.push(relationshipType);
    }
    
    query += ' ORDER BY r.weight DESC, m.priority DESC';

    const rows = await this.db.all(query, params);

    return rows
      .map(row => ({
        id: row.id,
        category: row.category,
        key: row.key,
        value: JSON.parse(row.value),
        metadata: JSON.parse(row.metadata || '{}'),
        timestamp: row.timestamp,
        ttl: row.ttl,
        priority: row.priority
      }))
      .filter(entry => !this.isExpired(entry));
  }

  private isExpired(entry: MemoryEntry): boolean {
    if (!entry.ttl) return false;
    return Date.now() > entry.timestamp + entry.ttl;
  }

  private async updateStats(category: string): Promise<void> {
    if (!this.db) return;

    await this.db.run(
      `INSERT INTO memory_stats (category, count, last_access, access_count)
       VALUES (?, 1, ?, 1)
       ON CONFLICT(category) DO UPDATE SET
       count = count + 1,
       last_access = ?,
       access_count = access_count + 1`,
      [category, Date.now(), Date.now()]
    );
  }

  private async loadCache(): Promise<void> {
    if (!this.db) return;

    const rows = await this.db.all(
      'SELECT * FROM memory ORDER BY priority DESC, timestamp DESC LIMIT 1000'
    );

    rows.forEach(row => {
      const entry: MemoryEntry = {
        id: row.id,
        category: row.category,
        key: row.key,
        value: JSON.parse(row.value),
        metadata: JSON.parse(row.metadata || '{}'),
        timestamp: row.timestamp,
        ttl: row.ttl,
        priority: row.priority
      };

      if (!this.isExpired(entry)) {
        this.cache.set(row.id, entry);
      }
    });
  }

  private startCleanup(): void {
    this.cleanupInterval = setInterval(async () => {
      await this.cleanup();
    }, 60000); // Clean every minute
  }

  private async cleanup(): Promise<void> {
    if (!this.db) return;

    // Remove expired entries
    await this.db.run(
      'DELETE FROM memory WHERE ttl IS NOT NULL AND timestamp + ttl < ?',
      [Date.now()]
    );

    // Clean cache
    for (const [id, entry] of this.cache) {
      if (this.isExpired(entry)) {
        this.cache.delete(id);
      }
    }

    // Optimize database
    await this.db.exec('VACUUM');
  }

  async close(): Promise<void> {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
    }

    if (this.db) {
      await this.db.close();
      this.db = null;
    }

    this.cache.clear();
  }

  async getStats(): Promise<any> {
    if (!this.db) throw new Error('Database not initialized');

    const stats = await this.db.all('SELECT * FROM memory_stats');
    const totalEntries = await this.db.get('SELECT COUNT(*) as count FROM memory');
    const cacheSize = this.cache.size;

    return {
      totalEntries: totalEntries?.count || 0,
      cacheSize,
      categoryStats: stats,
      memoryUsage: process.memoryUsage()
    };
  }
}

export default SQLiteMemory;