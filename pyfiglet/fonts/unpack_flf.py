import os
import zipfile
import sys

pth = os.path.dirname(os.path.abspath(sys.argv[0]))

if __name__ == '__main__':
    for f in os.listdir(pth):
        file_pth = os.path.join(pth, f)
        if (
            os.path.isfile(file_pth) and
            f.lower().endswith((".flf", ".tlf")) and
            zipfile.is_zipfile(file_pth)
        ):
            print("Unpacking %s..." % file_pth)
            try:
                os.rename(file_pth, file_pth + '.zip')
                with zipfile.ZipFile(file_pth + '.zip', 'r') as z:
                    data = z.read(z.getinfo(z.infolist()[0].filename))
                with open(file_pth, "wb") as f:
                    f.write(data)
                os.remove(file_pth + '.zip')
                print("    Success!")
            except Exception as e:
                print(e)
