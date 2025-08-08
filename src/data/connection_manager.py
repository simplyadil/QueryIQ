import psycopg2
from psycopg2 import pool
import json
from contextlib import contextmanager
import logging

class DatabaseConnectionManager:
    def __init__(self, config_path='config.json', min_conn=1, max_conn=10):
        # Load configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Initialize connection pool
        self.pool = pool.SimpleConnectionPool(
            min_conn,
            max_conn,
            **self.config
        )
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool with automatic cleanup."""
        conn = None
        try:
            conn = self.pool.getconn()
            conn.autocommit = True
            yield conn
        except Exception as e:
            self.logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self):
        """Get a cursor with automatic cleanup."""
        with self.get_connection() as conn:
            cursor = None
            try:
                cursor = conn.cursor()
                yield cursor
            finally:
                if cursor:
                    cursor.close()
    
    def execute_query(self, query, params=None):
        """Execute a query and return results."""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            try:
                return cursor.fetchall()
            except psycopg2.ProgrammingError:
                # No results to fetch (INSERT, UPDATE, DELETE)
                return None
    
    def execute_many(self, query, params_list):
        """Execute multiple queries with different parameters."""
        with self.get_cursor() as cursor:
            cursor.executemany(query, params_list)
    
    def close(self):
        """Close all connections in the pool."""
        if self.pool:
            self.pool.closeall()
            self.logger.info("Database connection pool closed") 