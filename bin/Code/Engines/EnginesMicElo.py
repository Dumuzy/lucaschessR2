import glob
import os
import sys

import Code
from Code import Util
from Code.Base.Constantes import ENG_MICGM, ENG_MICPER
from Code.Polyglots import Books


def read_mic_engines():
    configuration = Code.configuration
    intdir = Code.path_resource("IntFiles")
    file_list = sorted(glob.glob(intdir + "/mic_tourney*.eval"))

    dd = {}
    for file in file_list:
        with open(file) as f:
            for linea in f:
                dic = eval(linea.strip())
                alias = dic["ALIAS"]
                nom_base_engine = dic["ENGINE"]
                id_info = dic["IDINFO"]
                liinfo = [_F(x.strip()) for x in id_info.split("\n")]
                id_info = "\n".join(liinfo)
                elo = dic["ELO"]
                li_uci = [(d["name"], d["valor"]) for d in dic["LIUCI"]]
                book = None
                if "BOOK" in dic:
                    book = dic["BOOK"]

                engine = configuration.dic_engines.get(nom_base_engine)
                if engine:
                    eng = engine.clona()
                    eng.name = alias
                    eng.id_info = id_info
                    eng.alias = alias
                    eng.elo = elo
                    eng.liUCI = li_uci
                    eng.bookMaxply = None
                    eng.bookRR = None
                    if alias.isupper():  # These are the GM personalities.
                        eng.book = Code.path_resource("Openings", "Players", "%s.bin" % alias.lower())
                        eng.type = ENG_MICGM
                    elif book:
                        eng.book = Books.search_book(book)
                        if "BOOKMAXPLY" in dic:
                            eng.bookMaxply = dic["BOOKMAXPLY"]
                        else:
                            # A standard value depending on the engines elo is used. Defined in BookEx.
                            pass
                        if "BOOKRR" in dic:
                            eng.bookRR = dic["BOOKRR"]
                        eng.type = ENG_MICPER
                    else:
                        eng.book = None
                        eng.type = ENG_MICPER
                    eng.name = Util.primeras_mayuscula(alias)
                    eng.alias = eng.name
                    dd[eng.alias] = eng

    li = list(dd.values())
    li.sort(key=lambda uno: uno.elo)
    return li


def only_gm_engines():
    li = [mtl for mtl in read_mic_engines() if mtl.type == ENG_MICGM]
    li.sort(key=lambda uno: uno.name)
    return li


def all_engines():
    li = read_mic_engines()
    return li


def separated_engines():
    li = read_mic_engines()
    li_gm = []
    li_per = []
    for eng in li:
        if eng.type == ENG_MICGM:
            li_gm.append(eng)
        else:
            li_per.append(eng)
    return li_gm, li_per
