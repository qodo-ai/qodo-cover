//
//  ObjCViewModel.h
//  swift_counter
//
//  Created by Tran Binh An on 3/4/25.
//

#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

@interface ObjCViewModel : NSObject

@property (nonatomic, assign) NSInteger counter;

// Methods to increase and decrease the counter
- (void)increaseCounter;
- (void)decreaseCounter;

@end

NS_ASSUME_NONNULL_END
