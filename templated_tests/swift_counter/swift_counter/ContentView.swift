//
//  ContentView.swift
//  swift_counter
//
//  Created by An Tran on 27/3/25.
//

import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = ContentViewModel()

    var body: some View {
        VStack(spacing: 32) {
            Text("\(viewModel.counter)")
                .font(.title)
            HStack(spacing: 20) {
                Button("Increment+") {
                    viewModel.increment()
                }
                Button("Decrement-") {
                    viewModel.decrement()
                }
            }
        }
        .padding()
    }
}

#Preview {
    ContentView()
}
