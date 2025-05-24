//
//  ObjCViewControllerWrapper.swift
//  swift_counter
//
//  Created by Tran Binh An on 3/4/25.
//

import Foundation
import SwiftUI

struct ObjCViewControllerWrapper: UIViewControllerRepresentable {
    // Create and return the ObjCViewController instance
    func makeUIViewController(context: Context) -> ObjCViewController {
        return ObjCViewController()
    }

    // Update the view controller if needed (not used in this case)
    func updateUIViewController(_ uiViewController: ObjCViewController, context: Context) {
        // No updates needed for now
    }
}
