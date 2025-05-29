//
//  swift_counterTests.swift
//  swift_counterTests
//
//  Created by An Tran on 27/3/25.
//

import XCTest
@testable import swift_counter

class ContentViewModelTests: XCTestCase {

    func testIncrement() {
        let viewModel = ContentViewModel()
        viewModel.increment()
        XCTAssertEqual(viewModel.counter, 1)
    }

}
