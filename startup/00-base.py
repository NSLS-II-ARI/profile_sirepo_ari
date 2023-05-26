import datetime

import databroker
import matplotlib.pyplot as plt
import nslsii
from ophyd.utils import make_dir_tree
from sirepo_bluesky.shadow_handler import ShadowFileHandler
from sirepo_bluesky.srw_handler import SRWFileHandler

nslsii.configure_base(get_ipython().user_ns, "local")

try:
    databroker.assets.utils.install_sentinels(db.reg.config, version=1)
except Exception:
    pass

db.reg.register_handler("srw", SRWFileHandler, overwrite=True)
db.reg.register_handler("shadow", ShadowFileHandler, overwrite=True)
db.reg.register_handler("SIREPO_FLYER", SRWFileHandler, overwrite=True)

plt.ion()

root_dir = "/tmp/sirepo-bluesky-data"
_ = make_dir_tree(datetime.datetime.now().year, base_path=root_dir)
