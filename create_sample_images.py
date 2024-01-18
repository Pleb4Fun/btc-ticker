import logging

from btcticker.config import Config
from btcticker.ticker import Ticker

logger = logging.getLogger(__name__)


config = Config("home.admin/config.ini")

w = 176
h = 264

ticker = Ticker(config, w, h)
ticker.orientation = 0

ticker.setDaysAgo(3)
ticker.refresh()

mode_list = "fiat,height,satfiat,moscowtime,usd".split(",")
layout_list = (
    "all,fiat,fiatheight,big_one_row,one_number,big_two_rows,mempool,ohlc".split(",")
)
layout_list = ["big_one_row"]
layout_list = ["one_number"]
# layout_list = ["big_two_rows"]
# layout_list = ["mempool"]
layout_list = ["fiatheight"]
# layout_list = ["fiat"]
# layout_list = ["all"]
# layout_list = ["mempool"]
layout_list = ["ohlc"]
size_list = [
    (122, 250, 0),
    (176, 264, 0),
    (128, 296, 0),
    (480, 800, 0),
    (880, 528, 0),
    (528, 880, 0),
]

for w, h, o in size_list:
    ticker._change_size(w, h)
    ticker.orientation = o
    for layout in layout_list:
        for mode in mode_list:
            ticker.build(mirror=False, mode=mode, layout=layout)
            ticker.get_image().save(
                f"./sample_images/{w}_{h}_{o}_{mode}_{layout}.PNG", format="PNG"
            )
