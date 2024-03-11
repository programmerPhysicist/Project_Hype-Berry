import os
import sys
rel_path = os.path.dirname(os.path.realpath(__file__))
dir_path = os.path.join(rel_path, "../source")
src_path = os.path.abspath(dir_path)
sys.path.insert(0, src_path)

dir_path = os.path.join(rel_path, "fixtures")
src_path = os.path.abspath(dir_path)
sys.path.append(src_path)