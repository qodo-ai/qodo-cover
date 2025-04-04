#!/bin/sh

set -e

rm -rf ./.report
rm -rf ./.derivedData

echo "Running tests ..."

xcodebuild clean test \
    -project swift_counter.xcodeproj \
    -scheme swift_counter \
    -destination 'platform=iOS Simulator,name=iPhone 16 Pro' \
    -enableCodeCoverage YES \
    -derivedDataPath ./.derivedData > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "xcodebuild failed. Exiting."
    exit 1
fi

slather