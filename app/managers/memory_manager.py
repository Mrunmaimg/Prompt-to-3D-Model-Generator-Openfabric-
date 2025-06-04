import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
import os

class MemoryManager:
    """
    Manager class for handling storage
    """
    def __init__(self, db_path: str = "generations.db"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize SQLite database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS generations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        prompt TEXT NOT NULL,
                        enhanced_prompt TEXT,
                        image_path TEXT,
                        model_path TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT
                    )
                """)
                conn.commit()
        except Exception as e:
            logging.error(f"Error initializing database: {e}")
            
    def clear_database(self) -> bool:
        """
        Clear all records from the generations table and delete associated files
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT image_path, model_path FROM generations")
                file_paths = cursor.fetchall()
                
                # Delete all files
                for image_path, model_path in file_paths:
                    try:
                        if image_path and os.path.exists(image_path):
                            os.remove(image_path)
                            logging.info(f"Deleted image file: {image_path}")
                            
                        if model_path and os.path.exists(model_path):
                            os.remove(model_path)
                            logging.info(f"Deleted model file: {model_path}")
                    except Exception as e:
                        logging.error(f"Error deleting files: {e}")
                
                # Clear the database
                cursor.execute("DELETE FROM generations")
                conn.commit()
                
                # Clean up empty directories
                try:
                    for dir_path in ["outputs/images", "outputs/models"]:
                        if os.path.exists(dir_path) and not os.listdir(dir_path):
                            os.rmdir(dir_path)
                            logging.info(f"Removed empty directory: {dir_path}")
                except Exception as e:
                    logging.error(f"Error cleaning directories: {e}")
                
            return True
        except Exception as e:
            logging.error(f"Error clearing database: {e}")
            return False
            
    def delete_generation(self, generation_id: int) -> bool:
        """
        Delete a specific generation by ID and its associated files
        
        Args:
            generation_id (int): ID of the generation to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT image_path, model_path FROM generations WHERE id = ?",
                    (generation_id,)
                )
                result = cursor.fetchone()
                
                if result:
                    image_path, model_path = result
                    deleted_files = []
                    
                    # Delete image
                    if image_path and os.path.exists(image_path):
                        try:
                            os.remove(image_path)
                            deleted_files.append(image_path)
                            logging.info(f"Deleted image file: {image_path}")
                        except Exception as e:
                            logging.error(f"Error deleting image file {image_path}: {e}")
                    
                    # Delete model 
                    if model_path and os.path.exists(model_path):
                        try:
                            os.remove(model_path)
                            deleted_files.append(model_path)
                            logging.info(f"Deleted model file: {model_path}")
                        except Exception as e:
                            logging.error(f"Error deleting model file {model_path}: {e}")
                    
                    # Delete database record
                    cursor.execute("DELETE FROM generations WHERE id = ?", (generation_id,))
                    conn.commit()
                    
                    try:
                        for file_path in deleted_files:
                            dir_path = os.path.dirname(file_path)
                            if os.path.exists(dir_path) and not os.listdir(dir_path):
                                os.rmdir(dir_path)
                                logging.info(f"Removed empty directory: {dir_path}")
                    except Exception as e:
                        logging.error(f"Error cleaning directories: {e}")
                    
                    return True
                return False
        except Exception as e:
            logging.error(f"Error deleting generation {generation_id}: {e}")
            return False
            
    def save_generation(
        self,
        prompt: str,
        enhanced_prompt: str,
        image_path: Optional[str] = None,
        model_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Save a new generation to the database
        
        Args:
            prompt (str): Original user prompt
            enhanced_prompt (str): Enhanced prompt used for generation
            image_path (Optional[str]): Path to saved image file
            model_path (Optional[str]): Path to saved 3D model file
            metadata (Optional[Dict[str, Any]]): Additional metadata
            
        Returns:
            int: ID of the saved generation
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO generations 
                    (prompt, enhanced_prompt, image_path, model_path, metadata)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        prompt,
                        enhanced_prompt,
                        image_path,
                        model_path,
                        json.dumps(metadata) if metadata else None
                    )
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logging.error(f"Error saving generation: {e}")
            return -1
            
    def get_generations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve recent generations
        
        Args:
            limit (int): Maximum number of generations to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of generation records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM generations ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error retrieving generations: {e}")
            return []
            
    def search_generations(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search generations by prompt
        
        Args:
            search_term (str): Term to search for in prompts
            
        Returns:
            List[Dict[str, Any]]: List of matching generation records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM generations 
                    WHERE prompt LIKE ? OR enhanced_prompt LIKE ?
                    ORDER BY created_at DESC
                    """,
                    (f"%{search_term}%", f"%{search_term}%")
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error searching generations: {e}")
            return []
            
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the database structure and contents
        
        Returns:
            Dict[str, Any]: Dictionary containing database information
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("PRAGMA table_info(generations)")
                table_info = [dict(row) for row in cursor.fetchall()]
                
                cursor.execute("SELECT * FROM generations ORDER BY created_at DESC")
                entries = [dict(row) for row in cursor.fetchall()]
                
                for entry in entries:
                    if entry['model_path'] and os.path.exists(entry['model_path']):
                        entry['status'] = 'Complete'
                    elif entry['image_path'] and os.path.exists(entry['image_path']):
                        entry['status'] = 'Image Only'
                    else:
                        entry['status'] = 'Incomplete'
                
                return {
                    'total_entries': len(entries),
                    'table_info': table_info,
                    'entries': entries
                }
        except Exception as e:
            logging.error(f"Error getting database info: {e}")
            return {
                'total_entries': 0,
                'table_info': [],
                'entries': []
            }
            
    def get_edit_history(self, generation_id: int) -> List[Dict[str, Any]]:
        """
        Get the edit history for a specific generation
        
        Args:
            generation_id (int): ID of the generation
            
        Returns:
            List[Dict[str, Any]]: List of edits in chronological order
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get original generation
                cursor.execute(
                    """
                    SELECT * FROM generations WHERE id = ?
                    """,
                    (generation_id,)
                )
                original = dict(cursor.fetchone())
                
                # Get all related edits from metadata
                cursor.execute(
                    """
                    SELECT * FROM generations 
                    WHERE json_extract(metadata, '$.edit_history.original_prompt') = ?
                    ORDER BY created_at ASC
                    """,
                    (original['prompt'],)
                )
                edits = [dict(row) for row in cursor.fetchall()]
                
                history = [{
                    'type': 'original',
                    'prompt': original['prompt'],
                    'enhanced_prompt': original['enhanced_prompt'],
                    'timestamp': original['created_at']
                }]
                
                for edit in edits:
                    metadata = json.loads(edit['metadata']) if edit['metadata'] else {}
                    edit_history = metadata.get('edit_history', {})
                    history.append({
                        'type': 'edit',
                        'prompt': edit['prompt'],
                        'enhanced_prompt': edit['enhanced_prompt'],
                        'previous_prompt': edit_history.get('previous_enhanced_prompt'),
                        'timestamp': edit['created_at']
                    })
                
                return history
        except Exception as e:
            logging.error(f"Error getting edit history: {e}")
            return []
            
    def get_latest_context(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent similar generation context
        
        Args:
            prompt (str): Current prompt to find context for
            
        Returns:
            Optional[Dict[str, Any]]: Most recent similar generation or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Simple keyword matching for now, potential of improvement with proper text similarity search (e.g. FAISS, embeddings)
                words = set(prompt.lower().split())
                placeholders = ','.join('?' * len(words))
                like_conditions = ' OR '.join(
                    f'LOWER(prompt) LIKE ?' for _ in words
                )
                
                query = f"""
                    SELECT *, 
                    COUNT(*) as match_count
                    FROM generations 
                    WHERE {like_conditions}
                    GROUP BY id
                    ORDER BY match_count DESC, created_at DESC
                    LIMIT 1
                """
                
                cursor.execute(
                    query,
                    [f'%{word}%' for word in words]
                )
                
                result = cursor.fetchone()
                if result:
                    return dict(result)
                return None
                
        except Exception as e:
            logging.error(f"Error getting latest context: {e}")
            return None 