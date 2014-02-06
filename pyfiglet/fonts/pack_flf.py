import os
import zipfile
import sys

pth = os.path.dirname(os.path.abspath(sys.argv[0]))

if __name__ == '__main__':
    for f in os.listdir(pth):
        file_pth = os.path.join(pth, f)
        if (
            os.path.isfile(file_pth) and
            f.lower().endswith(".flf") and
            not zipfile.is_zipfile(file_pth)
        ):
            print("Packing %s..." % file_pth)
            try:
                with zipfile.ZipFile(f + '.zip', 'w', zipfile.ZIP_DEFLATED) as z:
                    z.write(file_pth)
                os.remove(file_pth)
                os.rename(f + '.zip', file_pth)
                print("    Success!")
            except Exception as e:
                print(e)
