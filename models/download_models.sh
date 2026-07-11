#!/usr/bin/env bash
set -euo pipefail

# Download pre-trained model artifacts for Argus ML Inference API.
# These files are excluded from the git repository via .gitignore.
#
# Usage:
#   ./download_models.sh              # Download from GitHub Releases
#   ./download_models.sh --dir /path  # Download to a custom directory

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${SCRIPT_DIR}"
REPO="AyoubHamrouni/Argus"
RELEASE_TAG="${ARGUS_MODEL_TAG:-latest}"

MODELS=(
    "random_forest_ids.pkl"
    "xgboost_ids.pkl"
    "decision_tree_ids.pkl"
    "scaler.pkl"
    "label_encoder.pkl"
    "feature_names.pkl"
)

while [[ $# -gt 0 ]]; do
    case $1 in
        --dir)
            TARGET_DIR="$2"
            shift 2
            ;;
        --tag)
            RELEASE_TAG="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--dir <directory>] [--tag <release-tag>]"
            echo ""
            echo "Download pre-trained ML model artifacts for Argus."
            echo ""
            echo "Options:"
            echo "  --dir <path>    Target directory (default: models/)"
            echo "  --tag <tag>     GitHub release tag (default: latest)"
            echo "  -h, --help      Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

mkdir -p "$TARGET_DIR"

echo "Downloading Argus model artifacts..."
echo "  Repository: $REPO"
echo "  Release: $RELEASE_TAG"
echo "  Target: $TARGET_DIR"
echo ""

if [[ "$RELEASE_TAG" == "latest" ]]; then
    DOWNLOAD_URL="https://github.com/$REPO/releases/latest/download"
else
    DOWNLOAD_URL="https://github.com/$REPO/releases/download/$RELEASE_TAG"
fi

FAILED=0
for model in "${MODELS[@]}"; do
    if [[ -f "$TARGET_DIR/$model" ]]; then
        echo "  [skip] $model (already exists)"
        continue
    fi

    echo -n "  [download] $model ... "
    if curl -sSfL "$DOWNLOAD_URL/$model" -o "$TARGET_DIR/$model" 2>/dev/null; then
        echo "ok"
    else
        echo "FAILED"
        FAILED=$((FAILED + 1))
    fi
done

echo ""

if [[ $FAILED -gt 0 ]]; then
    echo "Warning: $FAILED model(s) failed to download."
    echo "You can manually download them from:"
    echo "  https://github.com/$REPO/releases"
    exit 1
fi

echo "All models downloaded successfully to $TARGET_DIR"
echo "Expected features: 77 (CICIDS2017 network flow features)"
