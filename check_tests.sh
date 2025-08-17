#!/bin/bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
python3 -m pytest tests/ --tb=no -q 2>&1 | grep FAILED
echo "Exit code: $?"