#!/usr/bin/env python3
"""
Database Integrity Checker and Fixer for MangaAnime-Info-delivery-system

This script performs comprehensive database integrity checks and fixes:
1. Validates works and releases table relationships
2. Identifies orphaned releases (work_id pointing to non-existent works)
3. Creates missing work entries from releases data
4. Removes duplicate works
5. Updates work_id references in releases table
6. Provides detailed reports on the integrity status

Author: Backend API Developer Agent
Date: 2025-09-03
"""

import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_integrity_fix.log'),
        logging.StreamHandler()
    ]
)

class DatabaseIntegrityFixer:
    def __init__(self, db_path: str = 'db.sqlite3'):
        """Initialize with database path."""
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connect to SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            logging.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logging.error(f"Failed to connect to database: {e}")
            raise
            
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed")
            
    def get_database_stats(self) -> Dict[str, int]:
        """Get current database statistics."""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Count works
        cursor.execute("SELECT COUNT(*) as count FROM works")
        stats['works_count'] = cursor.fetchone()['count']
        
        # Count releases
        cursor.execute("SELECT COUNT(*) as count FROM releases")
        stats['releases_count'] = cursor.fetchone()['count']
        
        # Count orphaned releases (work_id not in works table)
        cursor.execute("""
            SELECT COUNT(*) as count FROM releases r
            LEFT JOIN works w ON r.work_id = w.id
            WHERE w.id IS NULL
        """)
        stats['orphaned_releases'] = cursor.fetchone()['count']
        
        # Count works without releases
        cursor.execute("""
            SELECT COUNT(*) as count FROM works w
            LEFT JOIN releases r ON w.id = r.work_id
            WHERE r.work_id IS NULL
        """)
        stats['works_without_releases'] = cursor.fetchone()['count']
        
        # Max work_id in releases
        cursor.execute("SELECT MAX(work_id) as max_work_id FROM releases")
        result = cursor.fetchone()
        stats['max_work_id_in_releases'] = result['max_work_id'] if result['max_work_id'] else 0
        
        # Max id in works
        cursor.execute("SELECT MAX(id) as max_id FROM works")
        result = cursor.fetchone()
        stats['max_id_in_works'] = result['max_id'] if result['max_id'] else 0
        
        return stats
        
    def find_orphaned_releases(self) -> List[Dict]:
        """Find releases that reference non-existent works."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT r.id, r.work_id, r.release_type, r.number, r.platform, r.source, r.source_url
            FROM releases r
            LEFT JOIN works w ON r.work_id = w.id
            WHERE w.id IS NULL
            ORDER BY r.work_id
        """)
        
        orphaned = []
        for row in cursor.fetchall():
            orphaned.append(dict(row))
            
        return orphaned
        
    def find_missing_works(self) -> Dict[int, List[Dict]]:
        """Find work_ids that are referenced in releases but don't exist in works."""
        orphaned_releases = self.find_orphaned_releases()
        
        # Group orphaned releases by work_id
        missing_works = {}
        for release in orphaned_releases:
            work_id = release['work_id']
            if work_id not in missing_works:
                missing_works[work_id] = []
            missing_works[work_id].append(release)
            
        return missing_works
        
    def extract_title_from_source_url(self, source_url: str) -> Optional[str]:
        """Extract potential title from source URL."""
        if not source_url:
            return None
            
        # Simple heuristics for common anime/manga sites
        url_lower = source_url.lower()
        
        # Extract from common patterns
        if 'anilist.co' in url_lower:
            parts = source_url.split('/')
            if len(parts) > 4:
                return parts[4].replace('-', ' ').title()
                
        if 'myanimelist.net' in url_lower:
            parts = source_url.split('/')
            for part in parts:
                if not part.isdigit() and len(part) > 3:
                    return part.replace('_', ' ').replace('-', ' ').title()
                    
        return None
        
    def create_work_from_releases(self, work_id: int, releases: List[Dict]) -> Optional[str]:
        """Create a work entry based on release information."""
        # Try to determine title from various sources
        potential_titles = []
        work_type = 'anime'  # Default
        
        for release in releases:
            # Extract title from source URL
            title_from_url = self.extract_title_from_source_url(release.get('source_url', ''))
            if title_from_url:
                potential_titles.append(title_from_url)
                
            # Determine type from platform or source
            if release.get('platform'):
                platform = release['platform'].lower()
                if any(manga_keyword in platform for manga_keyword in ['manga', 'comic', 'book']):
                    work_type = 'manga'
                    
            if release.get('source'):
                source = release['source'].lower()
                if any(manga_keyword in source for manga_keyword in ['manga', 'comic', 'book']):
                    work_type = 'manga'
                    
        # Choose the most common title or generate one
        if potential_titles:
            title = max(set(potential_titles), key=potential_titles.count)
        else:
            # Generate a placeholder title
            title = f"Unknown Work {work_id}"
            
        # Insert the work
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO works (id, title, type, created_at)
                VALUES (?, ?, ?, ?)
            """, (work_id, title, work_type, datetime.now().isoformat()))
            
            self.conn.commit()
            logging.info(f"Created work entry: ID={work_id}, Title='{title}', Type='{work_type}'")
            return title
            
        except Exception as e:
            logging.error(f"Failed to create work entry for ID {work_id}: {e}")
            return None
            
    def find_duplicate_works(self) -> List[Tuple[str, List[int]]]:
        """Find works with duplicate titles."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT title, GROUP_CONCAT(id) as ids, COUNT(*) as count
            FROM works
            GROUP BY LOWER(title)
            HAVING count > 1
            ORDER BY count DESC
        """)
        
        duplicates = []
        for row in cursor.fetchall():
            title = row['title']
            ids = [int(x) for x in row['ids'].split(',')]
            duplicates.append((title, ids))
            
        return duplicates
        
    def merge_duplicate_works(self, title: str, work_ids: List[int]) -> int:
        """Merge duplicate works by updating releases to reference the first work_id."""
        if len(work_ids) < 2:
            return work_ids[0]
            
        # Keep the first work_id, merge others into it
        primary_work_id = min(work_ids)
        duplicate_ids = [wid for wid in work_ids if wid != primary_work_id]
        
        cursor = self.conn.cursor()
        
        try:
            # Update releases to point to primary work
            for duplicate_id in duplicate_ids:
                cursor.execute("""
                    UPDATE releases SET work_id = ? WHERE work_id = ?
                """, (primary_work_id, duplicate_id))
                
                logging.info(f"Updated releases from work_id {duplicate_id} to {primary_work_id}")
                
            # Delete duplicate work entries
            cursor.execute("""
                DELETE FROM works WHERE id IN ({})
            """.format(','.join('?' * len(duplicate_ids))), duplicate_ids)
            
            self.conn.commit()
            
            logging.info(f"Merged duplicates for '{title}': kept ID {primary_work_id}, removed {duplicate_ids}")
            return primary_work_id
            
        except Exception as e:
            logging.error(f"Failed to merge duplicates for '{title}': {e}")
            self.conn.rollback()
            return primary_work_id
            
    def fix_integrity_issues(self) -> Dict[str, int]:
        """Fix all identified integrity issues."""
        logging.info("Starting database integrity fixes...")
        
        results = {
            'works_created': 0,
            'duplicates_merged': 0,
            'orphaned_releases_fixed': 0
        }
        
        # 1. Find and create missing works
        missing_works = self.find_missing_works()
        logging.info(f"Found {len(missing_works)} missing work entries")
        
        for work_id, releases in missing_works.items():
            title = self.create_work_from_releases(work_id, releases)
            if title:
                results['works_created'] += 1
                results['orphaned_releases_fixed'] += len(releases)
                
        # 2. Find and merge duplicate works
        duplicates = self.find_duplicate_works()
        logging.info(f"Found {len(duplicates)} sets of duplicate works")
        
        for title, work_ids in duplicates:
            self.merge_duplicate_works(title, work_ids)
            results['duplicates_merged'] += len(work_ids) - 1
            
        logging.info("Database integrity fixes completed")
        return results
        
    def generate_report(self, before_stats: Dict, after_stats: Dict, fix_results: Dict) -> str:
        """Generate a comprehensive integrity report."""
        report = []
        report.append("=" * 60)
        report.append("DATABASE INTEGRITY ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Before/After comparison
        report.append("DATABASE STATISTICS COMPARISON:")
        report.append("-" * 40)
        report.append(f"Works count:           {before_stats['works_count']:>6} → {after_stats['works_count']:>6}")
        report.append(f"Releases count:        {before_stats['releases_count']:>6} → {after_stats['releases_count']:>6}")
        report.append(f"Orphaned releases:     {before_stats['orphaned_releases']:>6} → {after_stats['orphaned_releases']:>6}")
        report.append(f"Works without releases:{before_stats['works_without_releases']:>6} → {after_stats['works_without_releases']:>6}")
        report.append("")
        
        # Fix results
        report.append("FIXES APPLIED:")
        report.append("-" * 40)
        report.append(f"Works created:         {fix_results['works_created']:>6}")
        report.append(f"Duplicates merged:     {fix_results['duplicates_merged']:>6}")
        report.append(f"Orphaned releases fixed: {fix_results['orphaned_releases_fixed']:>6}")
        report.append("")
        
        # Integrity status
        if after_stats['orphaned_releases'] == 0:
            report.append("✅ DATABASE INTEGRITY: EXCELLENT")
            report.append("   All releases have valid work references")
        else:
            report.append("⚠️  DATABASE INTEGRITY: ISSUES REMAIN")
            report.append(f"   {after_stats['orphaned_releases']} orphaned releases still exist")
            
        if after_stats['works_without_releases'] > 0:
            report.append(f"ℹ️  {after_stats['works_without_releases']} works have no releases (this may be normal)")
            
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
        
    def run_full_integrity_check(self) -> str:
        """Run complete integrity check and fix process."""
        try:
            self.connect()
            
            # Get initial stats
            before_stats = self.get_database_stats()
            logging.info("Initial database statistics collected")
            
            # Fix integrity issues
            fix_results = self.fix_integrity_issues()
            
            # Get final stats
            after_stats = self.get_database_stats()
            logging.info("Final database statistics collected")
            
            # Generate report
            report = self.generate_report(before_stats, after_stats, fix_results)
            
            # Save report to file
            report_filename = f"integrity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(report)
                
            logging.info(f"Integrity report saved to: {report_filename}")
            return report
            
        except Exception as e:
            logging.error(f"Integrity check failed: {e}")
            raise
        finally:
            self.close()

def main():
    """Main execution function."""
    print("MangaAnime Database Integrity Checker & Fixer")
    print("=" * 50)
    
    try:
        fixer = DatabaseIntegrityFixer()
        report = fixer.run_full_integrity_check()
        
        print(report)
        
    except Exception as e:
        print(f"Error: {e}")
        logging.error(f"Main execution failed: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())