#!/bin/bash
set -e

# Usage: ./scripts/release.sh [major|minor|patch]

BUMP_TYPE=$1
if [ -z "$BUMP_TYPE" ]; then
    echo "Usage: $0 [major|minor|patch]"
    exit 1
fi

# Ensure git is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "Error: Working directory not clean. Commit changes first."
    exit 1
fi

# Get current version (assuming stored in VERSION file or extracting from package.json/setup.py)
# For this project, we'll use a VERSION file at root.
if [ ! -f VERSION ]; then
    echo "0.1.0" > VERSION
fi

CURRENT_VERSION=$(cat VERSION)
echo "Current Version: $CURRENT_VERSION"

# Semver bump logic (simplified)
IFS='.' read -r -a parts <<< "$CURRENT_VERSION"
major=${parts[0]}
minor=${parts[1]}
patch=${parts[2]}

if [ "$BUMP_TYPE" == "major" ]; then
    major=$((major + 1))
    minor=0
    patch=0
elif [ "$BUMP_TYPE" == "minor" ]; then
    minor=$((minor + 1))
    patch=0
elif [ "$BUMP_TYPE" == "patch" ]; then
    patch=$((patch + 1))
else
    echo "Invalid bump type: $BUMP_TYPE"
    exit 1
fi

NEW_VERSION="$major.$minor.$patch"
echo "New Version: $NEW_VERSION"

# Update VERSION file
echo "$NEW_VERSION" > VERSION

# Update Frontend package.json
# Using sed for simplicity (jq/npm version is better but requires env setup)
# Assuming "version": "..." exists
sed -i "s/"version": "$CURRENT_VERSION"/"version": "$NEW_VERSION"/" frontend/package.json

# Commit and Tag
git add VERSION frontend/package.json
git commit -m "chore(release): bump version to $NEW_VERSION"
git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"

echo "Release v$NEW_VERSION created and tagged."
echo "Building Docker images..."

# Build Docker images with new tag
docker-compose build
docker tag arcoresyncbridge-backend:latest arcoresyncbridge-backend:$NEW_VERSION
docker tag arcoresyncbridge-frontend:latest arcoresyncbridge-frontend:$NEW_VERSION

echo "Images built. To push:"
echo "git push origin main --tags"
echo "docker push arcoresyncbridge-backend:$NEW_VERSION"
echo "docker push arcoresyncbridge-frontend:$NEW_VERSION"
