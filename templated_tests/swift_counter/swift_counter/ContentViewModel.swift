//
//  ContentViewModel.swift
//  swift_counter
//
//  Created by An Tran on 27/3/25.
//

import Foundation

class ContentViewModel: ObservableObject {
    @Published var counter = 0
    
    func increment() {
        counter += 1
    }

    func decrement() {
        counter -= 1
        if counter < 0 {
            counter = 0
        }
    }
}

