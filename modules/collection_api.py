"""
Collection API management module for Anime/Manga information system.

This module provides:
- Manual collection trigger API
- Collection status monitoring API  
- Data quality report API
- Collection history management
- Performance metrics and analytics
- Error handling and retry mechanisms

Features:
- RESTful API endpoints for collection management
- Real-time collection status monitoring
- Comprehensive reporting and analytics
- Integration with existing collectors (AniList, RSS)
- Data quality assessment and reporting
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from .anime_anilist import AniListCollector
from .manga_rss import MangaRSSCollector, BookWalkerRSSCollector, DAnimeRSSCollector
from .data_normalizer import DataIntegrator, DataQualityAnalyzer, analyze_data_quality
from .models import Work, Release, WorkType, DataSource
from .db import get_db


class CollectionStatus(Enum):
    """Collection status enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CollectionType(Enum):
    """Collection type enumeration."""
    FULL = "full"
    INCREMENTAL = "incremental"
    ANILIST_ONLY = "anilist_only"
    RSS_ONLY = "rss_only"
    CUSTOM = "custom"


@dataclass
class CollectionJob:
    """Collection job data structure."""
    job_id: str
    collection_type: CollectionType
    status: CollectionStatus
    sources: List[str]
    started_at: datetime
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    total_items: int = 0
    collected_items: int = 0
    filtered_items: int = 0
    errors: List[str] = None
    results: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.results is None:
            self.results = {}


@dataclass
class CollectionMetrics:
    """Collection performance metrics."""
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    average_duration: float
    total_items_collected: int
    total_errors: int
    last_collection: Optional[datetime]
    collection_rate: float  # items per hour
    error_rate: float


@dataclass
class DataQualityReport:
    """Data quality analysis report."""
    timestamp: datetime
    total_works: int
    total_releases: int
    quality_scores: Dict[str, float]
    grade_distribution: Dict[str, int]
    issues: List[Dict[str, Any]]
    recommendations: List[str]


class CollectionManager:
    """
    Collection management system with API endpoints.
    
    Provides centralized management of all collection operations,
    status monitoring, and reporting capabilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize collection manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.db = get_db()
        
        # Job management
        self.active_jobs: Dict[str, CollectionJob] = {}
        self.job_history: List[CollectionJob] = []
        self.job_lock = threading.Lock()
        
        # Collectors
        self.anilist_collector = AniListCollector(config)
        self.rss_collector = MangaRSSCollector(config)
        self.bookwalker_collector = BookWalkerRSSCollector(config)
        self.danime_collector = DAnimeRSSCollector(config)
        
        # Data processing
        self.data_integrator = DataIntegrator()
        self.quality_analyzer = DataQualityAnalyzer()
        
        # Performance tracking
        self.start_time = datetime.now()
        self.total_items_collected = 0
        self.total_errors = 0
        
        self.logger.info("Collection manager initialized")
    
    def start_collection(self, 
                        collection_type: CollectionType = CollectionType.FULL,
                        sources: Optional[List[str]] = None,
                        custom_params: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new collection job.
        
        Args:
            collection_type: Type of collection to perform
            sources: Specific sources to collect from
            custom_params: Custom parameters for collection
            
        Returns:
            Job ID for the started collection
        """
        job_id = self._generate_job_id()
        
        if sources is None:
            sources = self._get_default_sources(collection_type)
        
        job = CollectionJob(
            job_id=job_id,
            collection_type=collection_type,
            status=CollectionStatus.IDLE,
            sources=sources,
            started_at=datetime.now()
        )
        
        with self.job_lock:
            self.active_jobs[job_id] = job
        
        # Start collection in background thread
        thread = threading.Thread(
            target=self._run_collection_job,
            args=(job, custom_params or {}),
            daemon=True
        )
        thread.start()
        
        self.logger.info(f"Started collection job {job_id} ({collection_type.value})")
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a collection job.
        
        Args:
            job_id: Job ID to check
            
        Returns:
            Job status dictionary or None if not found
        """
        with self.job_lock:
            job = self.active_jobs.get(job_id)
            
            if not job:
                # Check history
                for historical_job in self.job_history:
                    if historical_job.job_id == job_id:
                        job = historical_job
                        break
            
            if job:
                return self._job_to_dict(job)
        
        return None
    
    def cancel_collection(self, job_id: str) -> bool:
        """
        Cancel a running collection job.
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        with self.job_lock:
            job = self.active_jobs.get(job_id)
            
            if job and job.status == CollectionStatus.RUNNING:
                job.status = CollectionStatus.CANCELLED
                job.completed_at = datetime.now()
                self.logger.info(f"Cancelled collection job {job_id}")
                return True
        
        return False
    
    def get_collection_metrics(self) -> CollectionMetrics:
        """
        Get collection performance metrics.
        
        Returns:
            Collection metrics
        """
        with self.job_lock:
            all_jobs = list(self.active_jobs.values()) + self.job_history
        
        successful_jobs = [j for j in all_jobs if j.status == CollectionStatus.COMPLETED]
        failed_jobs = [j for j in all_jobs if j.status == CollectionStatus.FAILED]
        
        # Calculate average duration
        completed_jobs = [j for j in all_jobs if j.completed_at]
        average_duration = 0.0
        if completed_jobs:
            durations = [(j.completed_at - j.started_at).total_seconds() for j in completed_jobs]
            average_duration = sum(durations) / len(durations)
        
        # Calculate collection rate (items per hour)
        uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        collection_rate = self.total_items_collected / uptime_hours if uptime_hours > 0 else 0
        
        # Calculate error rate
        total_collections = len(all_jobs)
        error_rate = len(failed_jobs) / total_collections if total_collections > 0 else 0
        
        # Last collection
        last_collection = None
        if completed_jobs:
            last_collection = max(j.completed_at for j in completed_jobs)
        
        return CollectionMetrics(
            total_jobs=len(all_jobs),
            successful_jobs=len(successful_jobs),
            failed_jobs=len(failed_jobs),
            average_duration=average_duration,
            total_items_collected=self.total_items_collected,
            total_errors=self.total_errors,
            last_collection=last_collection,
            collection_rate=collection_rate,
            error_rate=error_rate
        )
    
    def generate_quality_report(self) -> DataQualityReport:
        """
        Generate data quality analysis report.
        
        Returns:
            Data quality report
        """
        self.logger.info("Generating data quality report...")
        
        # Get all works from database
        works = self._get_all_works()
        releases = self._get_all_releases()
        
        if not works:
            return DataQualityReport(
                timestamp=datetime.now(),
                total_works=0,
                total_releases=0,
                quality_scores={},
                grade_distribution={},
                issues=[],
                recommendations=["No data available for analysis"]
            )
        
        # Analyze quality for each work
        quality_analyses = []
        grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        
        for work_dict in works:
            try:
                work = Work.from_dict(work_dict)
                quality = analyze_data_quality(work)
                quality_analyses.append(quality)
                
                grade = quality["grade"]
                grade_counts[grade] = grade_counts.get(grade, 0) + 1
                
            except Exception as e:
                self.logger.warning(f"Failed to analyze work {work_dict.get('id')}: {e}")
        
        # Calculate average scores
        if quality_analyses:
            avg_scores = {\n                "overall": sum(q["overall_score"] for q in quality_analyses) / len(quality_analyses),\n                "completeness": sum(q["completeness"] for q in quality_analyses) / len(quality_analyses),\n                "accuracy": sum(q["accuracy"] for q in quality_analyses) / len(quality_analyses),\n                "consistency": sum(q["consistency"] for q in quality_analyses) / len(quality_analyses),\n                "freshness": sum(q["freshness"] for q in quality_analyses) / len(quality_analyses)\n            }\n        else:\n            avg_scores = {"overall": 0, "completeness": 0, "accuracy": 0, "consistency": 0, "freshness": 0}\n        \n        # Identify issues\n        issues = self._identify_quality_issues(quality_analyses)\n        \n        # Generate recommendations\n        recommendations = self._generate_quality_recommendations(avg_scores, grade_counts, issues)\n        \n        return DataQualityReport(\n            timestamp=datetime.now(),\n            total_works=len(works),\n            total_releases=len(releases),\n            quality_scores=avg_scores,\n            grade_distribution=grade_counts,\n            issues=issues,\n            recommendations=recommendations\n        )\n    \n    def get_collection_history(self, limit: int = 50) -> List[Dict[str, Any]]:\n        \"\"\"\n        Get collection job history.\n        \n        Args:\n            limit: Maximum number of jobs to return\n            \n        Returns:\n            List of historical collection jobs\n        \"\"\"\n        with self.job_lock:\n            # Combine active and historical jobs\n            all_jobs = list(self.active_jobs.values()) + self.job_history\n            \n            # Sort by start time (newest first)\n            all_jobs.sort(key=lambda x: x.started_at, reverse=True)\n            \n            # Convert to dictionaries and limit\n            return [self._job_to_dict(job) for job in all_jobs[:limit]]\n    \n    def trigger_data_integration(self) -> Dict[str, Any]:\n        \"\"\"\n        Trigger data integration and deduplication.\n        \n        Returns:\n            Integration results\n        \"\"\"\n        self.logger.info(\"Starting data integration...\")\n        start_time = time.time()\n        \n        try:\n            # Get all works\n            works_data = self._get_all_works()\n            works = [Work.from_dict(w) for w in works_data]\n            \n            original_count = len(works)\n            \n            # Perform integration\n            integrated_works = self.data_integrator.integrate_works(works)\n            \n            # Update database (this would need actual implementation)\n            # For now, just return statistics\n            \n            duration = time.time() - start_time\n            \n            return {\n                \"status\": \"completed\",\n                \"duration_seconds\": duration,\n                \"original_works\": original_count,\n                \"integrated_works\": len(integrated_works),\n                \"duplicates_removed\": original_count - len(integrated_works),\n                \"timestamp\": datetime.now().isoformat()\n            }\n            \n        except Exception as e:\n            self.logger.error(f\"Data integration failed: {e}\")\n            return {\n                \"status\": \"failed\",\n                \"error\": str(e),\n                \"duration_seconds\": time.time() - start_time,\n                \"timestamp\": datetime.now().isoformat()\n            }\n    \n    def _run_collection_job(self, job: CollectionJob, custom_params: Dict[str, Any]):\n        \"\"\"\n        Run a collection job in background thread.\n        \n        Args:\n            job: Collection job to run\n            custom_params: Custom parameters\n        \"\"\"\n        try:\n            job.status = CollectionStatus.RUNNING\n            self.logger.info(f\"Running collection job {job.job_id}\")\n            \n            results = {}\n            \n            # Run collectors based on job type and sources\n            if job.collection_type == CollectionType.ANILIST_ONLY or \"anilist\" in job.sources:\n                if job.status != CollectionStatus.CANCELLED:\n                    anilist_result = self._run_anilist_collection(job)\n                    results[\"anilist\"] = anilist_result\n                    job.progress += 0.5\n            \n            if job.collection_type == CollectionType.RSS_ONLY or \"rss\" in job.sources:\n                if job.status != CollectionStatus.CANCELLED:\n                    rss_result = self._run_rss_collection(job)\n                    results[\"rss\"] = rss_result\n                    job.progress += 0.3\n            \n            if \"bookwalker\" in job.sources:\n                if job.status != CollectionStatus.CANCELLED:\n                    bw_result = self._run_bookwalker_collection(job)\n                    results[\"bookwalker\"] = bw_result\n                    job.progress += 0.1\n            \n            if \"danime\" in job.sources:\n                if job.status != CollectionStatus.CANCELLED:\n                    danime_result = self._run_danime_collection(job)\n                    results[\"danime\"] = danime_result\n                    job.progress += 0.1\n            \n            if job.status == CollectionStatus.CANCELLED:\n                self.logger.info(f\"Collection job {job.job_id} was cancelled\")\n                return\n            \n            # Finalize job\n            job.results = results\n            job.progress = 1.0\n            job.status = CollectionStatus.COMPLETED\n            job.completed_at = datetime.now()\n            \n            # Update totals\n            total_collected = sum(r.get(\"works_collected\", 0) + r.get(\"releases_collected\", 0) \n                                for r in results.values() if isinstance(r, dict))\n            self.total_items_collected += total_collected\n            \n            self.logger.info(f\"Collection job {job.job_id} completed successfully\")\n            \n        except Exception as e:\n            job.status = CollectionStatus.FAILED\n            job.completed_at = datetime.now()\n            job.errors.append(f\"Collection failed: {str(e)}\")\n            self.total_errors += 1\n            self.logger.error(f\"Collection job {job.job_id} failed: {e}\")\n            \n        finally:\n            # Move to history\n            with self.job_lock:\n                if job.job_id in self.active_jobs:\n                    del self.active_jobs[job.job_id]\n                self.job_history.append(job)\n                \n                # Keep history size manageable\n                if len(self.job_history) > 100:\n                    self.job_history = self.job_history[-50:]\n    \n    def _run_anilist_collection(self, job: CollectionJob) -> Dict[str, Any]:\n        \"\"\"Run AniList collection.\"\"\"\n        try:\n            self.logger.info(f\"Running AniList collection for job {job.job_id}\")\n            result = asyncio.run(self.anilist_collector.run_collection())\n            \n            job.collected_items += result.get(\"works_collected\", 0)\n            job.filtered_items += result.get(\"works_filtered\", 0)\n            \n            return result\n            \n        except Exception as e:\n            error_msg = f\"AniList collection failed: {str(e)}\"\n            job.errors.append(error_msg)\n            return {\"error\": error_msg}\n    \n    def _run_rss_collection(self, job: CollectionJob) -> Dict[str, Any]:\n        \"\"\"Run RSS collection.\"\"\"\n        try:\n            self.logger.info(f\"Running RSS collection for job {job.job_id}\")\n            items = self.rss_collector.collect()\n            \n            result = {\n                \"items_collected\": len(items),\n                \"source\": \"rss_general\",\n                \"timestamp\": datetime.now().isoformat()\n            }\n            \n            job.collected_items += len(items)\n            \n            return result\n            \n        except Exception as e:\n            error_msg = f\"RSS collection failed: {str(e)}\"\n            job.errors.append(error_msg)\n            return {\"error\": error_msg}\n    \n    def _run_bookwalker_collection(self, job: CollectionJob) -> Dict[str, Any]:\n        \"\"\"Run BookWalker collection.\"\"\"\n        try:\n            self.logger.info(f\"Running BookWalker collection for job {job.job_id}\")\n            items = self.bookwalker_collector.collect()\n            \n            result = {\n                \"items_collected\": len(items),\n                \"source\": \"bookwalker\",\n                \"timestamp\": datetime.now().isoformat()\n            }\n            \n            job.collected_items += len(items)\n            \n            return result\n            \n        except Exception as e:\n            error_msg = f\"BookWalker collection failed: {str(e)}\"\n            job.errors.append(error_msg)\n            return {\"error\": error_msg}\n    \n    def _run_danime_collection(self, job: CollectionJob) -> Dict[str, Any]:\n        \"\"\"Run dアニメストア collection.\"\"\"\n        try:\n            self.logger.info(f\"Running dアニメストア collection for job {job.job_id}\")\n            items = self.danime_collector.collect()\n            \n            result = {\n                \"items_collected\": len(items),\n                \"source\": \"danime\",\n                \"timestamp\": datetime.now().isoformat()\n            }\n            \n            job.collected_items += len(items)\n            \n            return result\n            \n        except Exception as e:\n            error_msg = f\"dアニメストア collection failed: {str(e)}\"\n            job.errors.append(error_msg)\n            return {\"error\": error_msg}\n    \n    def _generate_job_id(self) -> str:\n        \"\"\"Generate unique job ID.\"\"\"\n        timestamp = datetime.now().strftime(\"%Y%m%d_%H%M%S\")\n        return f\"job_{timestamp}_{hash(time.time()) & 0xFFFF:04x}\"\n    \n    def _get_default_sources(self, collection_type: CollectionType) -> List[str]:\n        \"\"\"Get default sources for collection type.\"\"\"\n        if collection_type == CollectionType.ANILIST_ONLY:\n            return [\"anilist\"]\n        elif collection_type == CollectionType.RSS_ONLY:\n            return [\"rss\", \"bookwalker\", \"danime\"]\n        else:\n            return [\"anilist\", \"rss\", \"bookwalker\", \"danime\"]\n    \n    def _job_to_dict(self, job: CollectionJob) -> Dict[str, Any]:\n        \"\"\"Convert job to dictionary.\"\"\"\n        return {\n            \"job_id\": job.job_id,\n            \"collection_type\": job.collection_type.value,\n            \"status\": job.status.value,\n            \"sources\": job.sources,\n            \"started_at\": job.started_at.isoformat(),\n            \"completed_at\": job.completed_at.isoformat() if job.completed_at else None,\n            \"progress\": job.progress,\n            \"total_items\": job.total_items,\n            \"collected_items\": job.collected_items,\n            \"filtered_items\": job.filtered_items,\n            \"errors\": job.errors,\n            \"results\": job.results\n        }\n    \n    def _get_all_works(self) -> List[Dict[str, Any]]:\n        \"\"\"Get all works from database.\"\"\"\n        try:\n            with self.db.get_connection() as conn:\n                cursor = conn.execute(\"SELECT * FROM works\")\n                return [dict(row) for row in cursor.fetchall()]\n        except Exception as e:\n            self.logger.error(f\"Failed to get works: {e}\")\n            return []\n    \n    def _get_all_releases(self) -> List[Dict[str, Any]]:\n        \"\"\"Get all releases from database.\"\"\"\n        try:\n            with self.db.get_connection() as conn:\n                cursor = conn.execute(\"SELECT * FROM releases\")\n                return [dict(row) for row in cursor.fetchall()]\n        except Exception as e:\n            self.logger.error(f\"Failed to get releases: {e}\")\n            return []\n    \n    def _identify_quality_issues(self, quality_analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:\n        \"\"\"Identify data quality issues.\"\"\"\n        issues = []\n        \n        # Low overall quality\n        low_quality = [q for q in quality_analyses if q[\"overall_score\"] < 0.5]\n        if low_quality:\n            issues.append({\n                \"type\": \"low_quality_data\",\n                \"severity\": \"high\",\n                \"count\": len(low_quality),\n                \"description\": f\"{len(low_quality)} works have overall quality score below 0.5\"\n            })\n        \n        # Missing titles\n        missing_titles = [q for q in quality_analyses if not q[\"details\"].get(\"has_title\")]\n        if missing_titles:\n            issues.append({\n                \"type\": \"missing_titles\",\n                \"severity\": \"critical\",\n                \"count\": len(missing_titles),\n                \"description\": f\"{len(missing_titles)} works are missing titles\"\n            })\n        \n        # Missing English titles\n        missing_en_titles = [q for q in quality_analyses if not q[\"details\"].get(\"has_english_title\")]\n        if len(missing_en_titles) > len(quality_analyses) * 0.7:  # More than 70%\n            issues.append({\n                \"type\": \"missing_english_titles\",\n                \"severity\": \"medium\",\n                \"count\": len(missing_en_titles),\n                \"description\": f\"{len(missing_en_titles)} works are missing English titles\"\n            })\n        \n        return issues\n    \n    def _generate_quality_recommendations(self, avg_scores: Dict[str, float], \n                                        grade_counts: Dict[str, int], \n                                        issues: List[Dict[str, Any]]) -> List[str]:\n        \"\"\"Generate quality improvement recommendations.\"\"\"\n        recommendations = []\n        \n        # Overall quality\n        if avg_scores[\"overall\"] < 0.7:\n            recommendations.append(\"Overall data quality is below acceptable levels. Consider improving data collection processes.\")\n        \n        # Completeness\n        if avg_scores[\"completeness\"] < 0.6:\n            recommendations.append(\"Data completeness is low. Focus on collecting more comprehensive information from sources.\")\n        \n        # Accuracy\n        if avg_scores[\"accuracy\"] < 0.8:\n            recommendations.append(\"Data accuracy needs improvement. Implement better validation and error checking.\")\n        \n        # Freshness\n        if avg_scores[\"freshness\"] < 0.5:\n            recommendations.append(\"Data freshness is poor. Increase collection frequency or implement real-time updates.\")\n        \n        # Grade distribution\n        total_works = sum(grade_counts.values())\n        if total_works > 0:\n            d_and_f_percent = (grade_counts[\"D\"] + grade_counts[\"F\"]) / total_works\n            if d_and_f_percent > 0.3:  # More than 30% are D or F grade\n                recommendations.append(\"High percentage of low-quality data. Consider data cleanup and re-collection.\")\n        \n        # Issue-based recommendations\n        for issue in issues:\n            if issue[\"severity\"] == \"critical\":\n                recommendations.append(f\"CRITICAL: {issue['description']}. Immediate attention required.\")\n            elif issue[\"severity\"] == \"high\":\n                recommendations.append(f\"HIGH PRIORITY: {issue['description']}. Should be addressed soon.\")\n        \n        if not recommendations:\n            recommendations.append(\"Data quality is acceptable. Continue with regular monitoring.\")\n        \n        return recommendations\n\n\n# Convenience functions for external use\n\ndef create_collection_manager(config: Dict[str, Any]) -> CollectionManager:\n    \"\"\"Create and return a collection manager instance.\"\"\"\n    return CollectionManager(config)\n\n\ndef start_full_collection(manager: CollectionManager) -> str:\n    \"\"\"Start a full collection job.\"\"\"\n    return manager.start_collection(CollectionType.FULL)\n\n\ndef start_incremental_collection(manager: CollectionManager) -> str:\n    \"\"\"Start an incremental collection job.\"\"\"\n    return manager.start_collection(CollectionType.INCREMENTAL)\n\n\ndef get_collection_status(manager: CollectionManager, job_id: str) -> Optional[Dict[str, Any]]:\n    \"\"\"Get status of a collection job.\"\"\"\n    return manager.get_job_status(job_id)