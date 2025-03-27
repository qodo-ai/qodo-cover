#!/bin/sh

rm -rf ./.report
rm -rf ./.derivedData

xcodebuild clean test \
    -project swift_counter.xcodeproj \
    -scheme swift_counter \
    -destination 'platform=iOS Simulator,name=iPhone 16 Pro' \
    -enableCodeCoverage YES \
    -derivedDataPath ./.derivedData

slather