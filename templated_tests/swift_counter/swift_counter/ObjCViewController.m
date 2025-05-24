//
//  ObjCViewController.m
//  swift_counter
//
//  Created by Tran Binh An on 3/4/25.
//

#import "ObjCViewController.h"
#import "ObjCViewModel.h"

@interface ObjCViewController ()

// Declare the view model and UI elements
@property (nonatomic, strong) ObjCViewModel *viewModel;
@property (nonatomic, strong) UILabel *counterLabel;

@end

@implementation ObjCViewController

- (void)viewDidLoad {
    [super viewDidLoad];
    // Set up the view controller's view
    self.view.backgroundColor = [UIColor whiteColor];
    
    // Initialize the view model
    self.viewModel = [[ObjCViewModel alloc] init];
    self.viewModel.counter = 0;
    
    // Add a label to display the counter
    self.counterLabel = [[UILabel alloc] initWithFrame:CGRectMake(50, 100, 300, 50)];
    self.counterLabel.text = [NSString stringWithFormat:@"Counter: %ld", (long)self.viewModel.counter];
    self.counterLabel.textAlignment = NSTextAlignmentCenter;
    self.counterLabel.font = [UIFont systemFontOfSize:24];
    [self.view addSubview:self.counterLabel];
    
    // Add a button to increase the counter
    UIButton *increaseButton = [UIButton buttonWithType:UIButtonTypeSystem];
    increaseButton.frame = CGRectMake(50, 200, 100, 50);
    [increaseButton setTitle:@"Increase" forState:UIControlStateNormal];
    [increaseButton addTarget:self action:@selector(increaseCounter) forControlEvents:UIControlEventTouchUpInside];
    [self.view addSubview:increaseButton];
    
    // Add a button to decrease the counter
    UIButton *decreaseButton = [UIButton buttonWithType:UIButtonTypeSystem];
    decreaseButton.frame = CGRectMake(200, 200, 100, 50);
    [decreaseButton setTitle:@"Decrease" forState:UIControlStateNormal];
    [decreaseButton addTarget:self action:@selector(decreaseCounter) forControlEvents:UIControlEventTouchUpInside];
    [self.view addSubview:decreaseButton];
}

// Method to increase the counter
- (void)increaseCounter {
    [self.viewModel increaseCounter];
    self.counterLabel.text = [NSString stringWithFormat:@"Counter: %ld", (long)self.viewModel.counter];
}

// Method to decrease the counter
- (void)decreaseCounter {
    [self.viewModel decreaseCounter];
    self.counterLabel.text = [NSString stringWithFormat:@"Counter: %ld", (long)self.viewModel.counter];
}

@end
