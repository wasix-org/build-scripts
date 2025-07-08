# There is not much we can test without a workign compiler, so we just test if we can import it and call a few functions
from cffi import FFI


ffi = FFI()
ffi.cdef("""
    int add(int a, int b);
    int multiply(int a, int b);
    extern int global_counter;
""")

ffi.set_source("_test_cffi",
"""
    int add(int a, int b) {
        return a + b;
    }

    int multiply(int a, int b) {
        return a * b;
    }

    int global_counter = 42;
""")