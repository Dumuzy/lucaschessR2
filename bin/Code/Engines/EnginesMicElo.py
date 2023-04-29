import glob
import os
import re
import sys

import Code
from Code import Util
from Code.Base.Constantes import ENG_MICGM, ENG_MICPER
from Code.Polyglots import Books


class DicMicElos:
    def __init__(self):
        self.variable = "DicMicElos"
        self.configuration = Code.configuration
        self._dic = self.configuration.read_variables(self.variable)

    def get_elo(self, alias):
        k = alias.lower()
        elo = None
        if k in self._dic:
            elo = self._dic[k]
        elif alias in self._dic:
            elo = self._dic[alias]
            del self._dic[alias]
            self._dic[k] = elo
            self.configuration.write_variables(self.variable, self._dic)
        return elo

    def dic(self):
        return self._dic

    def cambia_elo(self, clave_motor, nuevo_elo):
        clave_motor = clave_motor.lower()
        self._dic = self.configuration.read_variables(self.variable)
        if clave_motor in self._dic:
            old_elo = self._dic[clave_motor]
        else:
            old_elo = "?"

        sys.stderr.writeln(f"cambia_elo {clave_motor} {old_elo} -> {nuevo_elo}")
        self._dic[clave_motor] = nuevo_elo
        self.configuration.write_variables(self.variable, self._dic)


def add_abbrev(abbrevs, linea):
    linea = linea[5:].strip()
    x = re.split(r"\s\s+", linea)
    abbrevs.append(x)
    return abbrevs


def apply_abbrevs(abbrevs, linea):
    li = linea
    for abb in abbrevs:
        li = re.sub(abb[0], abb[1], li)
    sys.stderr.writeln("REPABBR MIC=" + li)
    return li


def read_mic_engines():
    configuration = Code.configuration
    intdir = Code.path_resource("IntFiles")
    file_list = sorted(glob.glob(intdir + "/mic_tourney*.eval"))
    abbrevs = []
    dd = {}
    for file in file_list:
        with open(file) as f:
            for linea in f:
                linea = linea.strip()
                if linea == "" or linea.startswith("#"):
                    if linea.startswith("#abb:"):  # it is a line defining an abbreviation.
                        abbrevs = add_abbrev(abbrevs, linea)
                    continue
                linea = linea.split("#", 1)[0]      # allow comments in line
                sys.stderr.writeln("READING MIC=" + linea)
                linea = apply_abbrevs(abbrevs, linea)
                dic = eval(linea)
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
    dme = DicMicElos()
    for eng in li:
        elo = dme.get_elo(eng.alias)
        if elo:
            eng.elo = elo

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
