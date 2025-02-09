import sys
import numpy as np
import platform

def check_numpy_installation():
    print("Python Version:", sys.version)
    print("Platform:", platform.platform())
    print("NumPy Version:", np.__version__)
    print("NumPy Configuration:")
    print("- Compiler:", np.show_config())
    
    try:
        print("\nNumPy Basic Test:")
        test_array = np.array([1, 2, 3])
        print("Test Array:", test_array)
        print("Array Type:", type(test_array))
    except Exception as e:
        print("Error in NumPy test:", str(e))

if __name__ == "__main__":
    check_numpy_installation()
