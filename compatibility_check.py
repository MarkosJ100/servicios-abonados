import sys
import platform

def check_compatibility():
    print("Python Version Details:")
    print(f"- Version: {sys.version}")
    print(f"- Implementation: {platform.python_implementation()}")
    print(f"- Platform: {platform.platform()}")

    try:
        import numpy as np
        print("\nNumPy Details:")
        print(f"- Version: {np.__version__}")
        print(f"- Configuration:")
        np.show_config()
    except ImportError:
        print("\nNumPy is not installed.")

    try:
        import pandas as pd
        print("\nPandas Details:")
        print(f"- Version: {pd.__version__}")
    except ImportError:
        print("\nPandas is not installed.")

    try:
        import scipy
        print("\nSciPy Details:")
        print(f"- Version: {scipy.__version__}")
    except ImportError:
        print("\nSciPy is not installed.")

if __name__ == "__main__":
    check_compatibility()
