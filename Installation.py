"""
Install the necessary Python modules to use SeisDown.

Author : Thibaut Céci (thi.ceci@gmail.com)
"""

import subprocess
import sys

def install_module(module):
    subprocess.check_call([sys.executable, "-m", "pip", "install", module])

install_module('obspy')
install_module('pandas')
install_module('tqdm')