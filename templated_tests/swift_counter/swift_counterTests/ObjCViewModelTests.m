//
//  ObjCViewModelTests.m
//  swift_counterTests
//
//  Created by Tran Binh An on 3/4/25.
//

#import <XCTest/XCTest.h>
#import "ObjCViewModel.h"
#import "ObjCViewModelTests.h"

@implementation ObjCViewModelTests

- (void)testExample {
    ObjCViewModel *viewModel = [[ObjCViewModel alloc] init];
    XCTAssertNotNil(viewModel, @"ViewModel should not be nil");
}

@end
