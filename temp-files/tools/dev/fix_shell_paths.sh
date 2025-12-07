#!/bin/bash
# Fix hardcoded paths in shell scripts

OLD_PATH="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Fixing hardcoded paths in shell scripts..."
echo "Old path: $OLD_PATH"
echo "New path: Dynamic path resolution"
echo ""

# Find all shell scripts with the old path
FILES=$(grep -rl "$OLD_PATH" --include="*.sh" .)

if [ -z "$FILES" ]; then
    echo "No files with hardcoded paths found"
    exit 0
fi

COUNT=0

for file in $FILES; do
    echo "Fixing $file..."

    # Replace hardcoded PROJECT_ROOT/PROJECT_DIR/WORK_DIR with dynamic path
    sed -i.bak "s|PROJECT_ROOT=\"$OLD_PATH\"|PROJECT_ROOT=\"\$( cd \"\$( dirname \"\${BASH_SOURCE[0]}\" )/../..\" \&\& pwd )\"|g" "$file"
    sed -i.bak "s|PROJECT_DIR=\"$OLD_PATH\"|PROJECT_DIR=\"\$( cd \"\$( dirname \"\${BASH_SOURCE[0]}\" )/../..\" \&\& pwd )\"|g" "$file"
    sed -i.bak "s|WORK_DIR=\"$OLD_PATH\"|WORK_DIR=\"\$( cd \"\$( dirname \"\${BASH_SOURCE[0]}\" )/../..\" \&\& pwd )\"|g" "$file"

    # Replace bare cd commands
    sed -i.bak "s|cd $OLD_PATH|cd \"\$( cd \"\$( dirname \"\${BASH_SOURCE[0]}\" )/../..\" \&\& pwd )\"|g" "$file"

    # Remove backup files
    rm -f "${file}.bak"

    COUNT=$((COUNT + 1))
done

echo ""
echo "Fixed $COUNT files"
