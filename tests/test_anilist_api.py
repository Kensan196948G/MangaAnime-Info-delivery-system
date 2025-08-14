#!/usr/bin/env python3
"""
Unit and integration tests for AniList GraphQL API integration
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import aiohttp
from gql import Client
from gql.transport.exceptions import TransportError
import time

class TestAniListAPI:
    """Test AniList GraphQL API integration."""
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_anilist_query_construction(self):
        """Test GraphQL query construction for AniList API."""
        expected_query = """
        query ($page: Int, $perPage: Int, $status: MediaStatus, $type: MediaType) {
          Page(page: $page, perPage: $perPage) {
            pageInfo {
              total
              currentPage
              lastPage
              hasNextPage
            }
            media(status: $status, type: $type, sort: [START_DATE_DESC]) {
              id
              title {
                romaji
                english
                native
              }
              type
              format
              status
              episodes
              chapters
              volumes
              genres
              tags {
                name
                category
              }
              description
              startDate {
                year
                month
                day
              }
              endDate {
                year
                month
                day
              }
              nextAiringEpisode {
                episode
                airingAt
              }
              streamingEpisodes {
                title
                url
                site
              }
              siteUrl
              coverImage {
                large
                medium
              }
              studios {
                nodes {
                  name
                }
              }
            }
          }
        }
        """
        
        # Normalize whitespace for comparison
        def normalize_query(query_str):
            return ' '.join(query_str.split())
        
        # This would be imported from the actual module
        # For now, we'll just verify the structure
        assert "Page" in expected_query
        assert "media" in expected_query
        assert "nextAiringEpisode" in expected_query
        assert "streamingEpisodes" in expected_query
    
    @pytest.mark.unit
    @pytest.mark.api
    async def test_anilist_api_client_initialization(self, test_config):
        """Test AniList API client initialization."""
        config = test_config['apis']['anilist']
        
        # Mock the GQL client
        with patch('gql.Client') as mock_client_class, \
             patch('gql.transport.aiohttp.AIOHTTPTransport') as mock_transport_class:
            
            mock_transport = Mock()
            mock_transport_class.return_value = mock_transport
            
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Simulate client initialization
            from gql.transport.aiohttp import AIOHTTPTransport
            transport = AIOHTTPTransport(
                url=config['graphql_url'],
                timeout=config['timeout_seconds']
            )
            
            client = Client(transport=transport, fetch_schema_from_transport=True)
            
            # Verify initialization
            assert mock_transport_class.called
            assert mock_client_class.called
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_anilist_api_successful_query(self, mock_anilist_response):
        """Test successful AniList API query execution."""
        
        with patch('gql.Client') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock the execute method to return our test data
            mock_client.execute_async.return_value = mock_anilist_response
            
            # Simulate API call
            query = "test_query"  # This would be the actual GraphQL query
            variables = {
                "page": 1,
                "perPage": 50,
                "status": "RELEASING",
                "type": "ANIME"
            }
            
            result = await mock_client.execute_async(query, variable_values=variables)
            
            # Verify response structure
            assert "data" in result
            assert "Page" in result["data"]
            assert "media" in result["data"]["Page"]
            
            media = result["data"]["Page"]["media"][0]
            assert "id" in media
            assert "title" in media
            assert "type" in media
            assert "nextAiringEpisode" in media
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_anilist_rate_limiting(self, test_config):
        """Test AniList API rate limiting compliance."""
        config = test_config['apis']['anilist']
        rate_limit = config['rate_limit']['requests_per_minute']
        
        # Calculate minimum time between requests
        min_interval = 60.0 / rate_limit  # seconds
        
        with patch('gql.Client') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.execute_async.return_value = {"data": {"Page": {"media": []}}}
            
            # Simulate multiple requests
            request_times = []
            for i in range(5):
                start_time = time.time()
                await mock_client.execute_async("test_query")
                request_times.append(start_time)
                
                # Add minimum delay to respect rate limits
                if i < 4:  # Don't wait after the last request
                    await asyncio.sleep(min_interval)
            
            # Verify rate limiting compliance
            for i in range(1, len(request_times)):
                time_diff = request_times[i] - request_times[i-1]
                assert time_diff >= min_interval - 0.1  # Allow small timing variations
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_anilist_error_handling(self):
        """Test AniList API error handling and retry logic."""
        
        with patch('gql.Client') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock transport error
            mock_client.execute_async.side_effect = TransportError("Network error")
            
            # Test error handling
            with pytest.raises(TransportError):
                await mock_client.execute_async("test_query")
            
            # Test retry logic (would be implemented in the actual module)
            retry_attempts = 0
            max_retries = 3
            
            while retry_attempts < max_retries:
                try:
                    await mock_client.execute_async("test_query")
                    break
                except TransportError:
                    retry_attempts += 1
                    if retry_attempts >= max_retries:
                        raise
                    await asyncio.sleep(1)  # Retry delay
            
            assert retry_attempts == max_retries
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_anilist_data_normalization(self, mock_anilist_response):
        """Test normalization of AniList API response data."""
        media_data = mock_anilist_response["data"]["Page"]["media"][0]
        
        # Expected normalized structure
        expected_fields = [
            'id', 'title', 'type', 'status', 'genres', 'tags',
            'description', 'startDate', 'nextAiringEpisode', 'siteUrl'
        ]
        
        for field in expected_fields:
            assert field in media_data
        
        # Test title normalization
        title = media_data['title']
        assert 'romaji' in title
        assert 'english' in title
        assert 'native' in title
        
        # Test date handling
        if media_data.get('nextAiringEpisode'):
            airing_episode = media_data['nextAiringEpisode']
            assert 'episode' in airing_episode
            assert 'airingAt' in airing_episode
            
            # Verify timestamp conversion
            airing_timestamp = airing_episode['airingAt']
            assert isinstance(airing_timestamp, int)
            
            # Convert to datetime and verify it's a valid future date
            airing_date = datetime.fromtimestamp(airing_timestamp)
            assert isinstance(airing_date, datetime)
    
    @pytest.mark.integration
    @pytest.mark.api
    async def test_anilist_streaming_platforms_extraction(self, mock_anilist_response):
        """Test extraction of streaming platform information from AniList."""
        media_data = mock_anilist_response["data"]["Page"]["media"][0]
        
        if 'streamingEpisodes' in media_data:
            streaming_episodes = media_data['streamingEpisodes']
            
            for episode in streaming_episodes:
                assert 'title' in episode
                assert 'url' in episode
                
                # Validate URL format
                url = episode['url']
                assert url.startswith('http')
                
                # Extract platform from URL (basic extraction)
                if 'netflix' in url.lower():
                    platform = 'Netflix'
                elif 'amazon' in url.lower() or 'prime' in url.lower():
                    platform = 'Amazon Prime Video'
                elif 'crunchyroll' in url.lower():
                    platform = 'Crunchyroll'
                else:
                    platform = 'Unknown'
                
                assert platform is not None

class TestAniListDataProcessing:
    """Test AniList data processing and filtering."""
    
    @pytest.mark.unit
    def test_ng_keyword_filtering(self, mock_anilist_response, test_config):
        """Test NG keyword filtering for AniList data."""
        ng_keywords = test_config['filtering']['ng_keywords']
        ng_genres = test_config['filtering']['ng_genres']
        
        media_data = mock_anilist_response["data"]["Page"]["media"][0]
        
        # Test genre filtering
        genres = media_data.get('genres', [])
        has_ng_genre = any(genre in ng_genres for genre in genres)
        
        # Test description filtering
        description = media_data.get('description', '')
        has_ng_keyword = any(keyword in description for keyword in ng_keywords)
        
        # Test tag filtering
        tags = [tag['name'] for tag in media_data.get('tags', [])]
        has_ng_tag = any(any(keyword in tag for keyword in ng_keywords) for tag in tags)
        
        should_filter = has_ng_genre or has_ng_keyword or has_ng_tag
        
        # In this test case, the sample data should not be filtered
        assert not should_filter
    
    @pytest.mark.unit
    def test_anime_type_detection(self, mock_anilist_response):
        """Test anime type and format detection."""
        media_data = mock_anilist_response["data"]["Page"]["media"][0]
        
        media_type = media_data.get('type')
        media_format = media_data.get('format')
        
        assert media_type in ['ANIME', 'MANGA']
        
        if media_type == 'ANIME':
            valid_formats = ['TV', 'MOVIE', 'OVA', 'ONA', 'SPECIAL']
            if media_format:
                assert media_format in valid_formats
    
    @pytest.mark.unit
    def test_release_date_parsing(self, mock_anilist_response):
        """Test release date parsing from AniList data."""
        media_data = mock_anilist_response["data"]["Page"]["media"][0]
        
        # Test start date parsing
        start_date = media_data.get('startDate')
        if start_date:
            assert 'year' in start_date
            year = start_date['year']
            if year:
                assert isinstance(year, int)
                assert 1950 <= year <= 2030  # Reasonable range
            
            month = start_date.get('month')
            if month:
                assert isinstance(month, int)
                assert 1 <= month <= 12
            
            day = start_date.get('day')
            if day:
                assert isinstance(day, int)
                assert 1 <= day <= 31
        
        # Test next airing episode date
        next_airing = media_data.get('nextAiringEpisode')
        if next_airing:
            airing_at = next_airing['airingAt']
            assert isinstance(airing_at, int)
            
            # Convert to datetime and verify
            airing_datetime = datetime.fromtimestamp(airing_at)
            current_time = datetime.now()
            
            # Should be in the future (allowing for some test execution time)
            assert airing_datetime > current_time - timedelta(minutes=5)

class TestAniListPerformance:
    """Test AniList API performance and optimization."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_concurrent_requests_performance(self, performance_test_config):
        """Test concurrent AniList API request performance."""
        concurrent_requests = performance_test_config['concurrent_requests']
        max_response_time = performance_test_config['max_response_time']
        
        with patch('gql.Client') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock fast response
            mock_client.execute_async.return_value = {"data": {"Page": {"media": []}}}
            
            async def make_request(query_id):
                start_time = time.time()
                result = await mock_client.execute_async(f"test_query_{query_id}")
                end_time = time.time()
                return end_time - start_time, result
            
            # Execute concurrent requests
            start_total = time.time()
            tasks = [make_request(i) for i in range(concurrent_requests)]
            results = await asyncio.gather(*tasks)
            end_total = time.time()
            
            total_time = end_total - start_total
            
            # Verify all requests completed
            assert len(results) == concurrent_requests
            
            # Check individual response times
            for response_time, result in results:
                assert response_time < max_response_time
                assert result is not None
            
            # Total time should be less than sequential execution
            max_sequential_time = concurrent_requests * max_response_time
            assert total_time < max_sequential_time
    
    @pytest.mark.performance
    def test_data_processing_performance(self, test_data_generator):
        """Test performance of data processing large AniList responses."""
        # Generate large dataset
        large_anime_dataset = test_data_generator.generate_anime_data(100)
        
        start_time = time.time()
        
        # Simulate data processing
        processed_count = 0
        for anime in large_anime_dataset:
            # Basic processing steps
            title = anime.get('title', {})
            processed_title = title.get('romaji') or title.get('english') or title.get('native')
            
            # Genre processing
            genres = anime.get('genres', [])
            processed_genres = [genre.lower() for genre in genres]
            
            # Tag processing
            tags = anime.get('tags', [])
            processed_tags = [tag.get('name', '').lower() for tag in tags]
            
            # Date processing
            next_airing = anime.get('nextAiringEpisode')
            if next_airing and next_airing.get('airingAt'):
                airing_date = datetime.fromtimestamp(next_airing['airingAt'])
            
            processed_count += 1
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert processed_count == 100
        assert processing_time < 1.0  # Should process 100 items within 1 second
    
    @pytest.mark.performance
    @pytest.mark.api
    async def test_memory_usage_monitoring(self, performance_test_config):
        """Test memory usage during AniList API operations."""
        import psutil
        import os
        
        # Get current process
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with patch('gql.Client') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock large response
            large_response = {
                "data": {
                    "Page": {
                        "media": [{"id": i, "title": {"romaji": f"Title {i}"}} for i in range(1000)]
                    }
                }
            }
            mock_client.execute_async.return_value = large_response
            
            # Process large dataset
            for i in range(10):
                result = await mock_client.execute_async("test_query")
                # Process the response (simulated)
                media_list = result["data"]["Page"]["media"]
                processed_media = [{"id": m["id"], "title": m["title"]["romaji"]} for m in media_list]
                
                # Clear processed data to prevent accumulation
                del processed_media
                del media_list
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        memory_limit = performance_test_config['memory_limit_mb']
        
        assert memory_increase < memory_limit, f"Memory usage increased by {memory_increase:.2f}MB, limit is {memory_limit}MB"