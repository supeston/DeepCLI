import sys
import os
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, os.path.dirname(__file__))
from deepx.main import main
if __name__ == "__main__":
    main()
