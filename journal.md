# Jan 16th 2021

Basic setup for terminal initialization.

Main difficulty was to figure out how to put initialization into separate
functions. Passing stdout around does not work because the borrow checker
prevents passing mutable references in multiple functions. The basic hack is to
"re-create" stdout in the deinit function through the std::io::stdout function.
