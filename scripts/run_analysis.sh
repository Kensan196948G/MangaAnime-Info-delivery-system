#!/bin/bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
python3 .extract_sections.py > /tmp/analysis_output.txt 2>&1
cat /tmp/analysis_output.txt
