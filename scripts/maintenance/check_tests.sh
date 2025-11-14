#!/bin/bash
cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
python3 -m pytest tests/ --tb=no -q 2>&1 | grep FAILED
echo "Exit code: $?"