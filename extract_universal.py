#!/usr/bin/env python3
"""Script principal para extração universal"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.universal_extractor import main

if __name__ == "__main__":
    main()