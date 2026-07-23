import os
import ultralytics
v = ultralytics.__version__
p = os.path.join(os.path.dirname(ultralytics.__file__), 'cfg', 'default.yaml')
ce = os.path.exists(p)
import yaml
with open(p) as yf:
    data = yaml.safe_load(yf)
fs = 'fuse_score' in str(data)
ha = 'half' in str(data)
qu = 'quantize' in str(data)
check_path = os.path.join(os.getcwd(), 'check_exists.txt')
with open(check_path, 'w') as f:
    f.write(f"VERSION:{v} CONFIG_EXISTS:{ce} fuse_score:{fs} half:{ha} quantize:{qu}\n")