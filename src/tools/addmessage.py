import sys
import six
if six.PY2:
    from io import open

PATH = "/home/sparrow/EVE/logs/Chatlogs/TheCitadel_20401229_065150.txt"

def main():
    line = ""
    with open(PATH, "r", encoding="utf-16") as f:
        content = f.read()
        lines = content.split("\n")
        line = lines[-2].strip()
        line = line[:line.find(">")+1]
    line = line + " " + sys.argv[1] + "\n"
    with open(PATH, "a") as f:
        f.write(line.encode("utf-16"))



if __name__ == "__main__":
    main()

    
