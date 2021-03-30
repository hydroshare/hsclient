from hsclient.hydroshare import HydroShare
import os

hs = HydroShare()
hs.sign_in()

res = hs.resource("7561aa12fd824ebb8edbee05af19b910")
for root, directories, files in os.walk("."):
    root = root[2:]
    file_paths = [os.path.join(root, f) for f in files if f[0] != "." and f.endswith(".ipynb")]
    if not res.file(folder=root):
        res.folder_create(root)
    res.file_upload(*file_paths, destination_path=root)
    break
