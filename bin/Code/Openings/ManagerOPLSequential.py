import time

from Code import Manager
from Code import Util
from Code.Base import Game, Move
from Code.Base.Constantes import (
    ST_ENDGAME,
    ST_PLAYING,
    TB_CLOSE,
    TB_REINIT,
    TB_CONFIG,
    TB_HELP,
    TB_NEXT,
    TB_UTILITIES,
    TB_COMMENTS,
    GT_OPENING_LINES,
)
from Code.Engines import EngineResponse
from Code.Openings import OpeningLines, ManagerOPL
from Code.QT import Iconos
from Code.QT import QTUtil2


class ManagerOpeningLinesSequential(ManagerOPL.ManagerOpeningLines):
    show_comments = None

    def start(self, pathFichero):
        self.board.saveVisual()

        self.pathFichero = pathFichero
        dbop = OpeningLines.Opening(pathFichero)
        self.board.dbvisual_set_file(dbop.nom_fichero)
        self.reinicio(dbop)

    def reinicio(self, dbop):
        self.dbop = dbop
        self.game_type = GT_OPENING_LINES

        self.modo = "SEQUENTIAL"

        self.training = self.dbop.training()

        self.liGames = self.training["LIGAMES_SEQUENTIAL"]
        self.num_linea = self.training.get("NUMLINEA_SEQUENTIAL", 0)
        if self.num_linea >= len(self.liGames):
            self.num_linea = 0
        self.game_info = self.liGames[self.num_linea]
        self.li_pv = self.game_info["LIPV"]
        self.numPV = len(self.li_pv)

        self.calc_totalTiempo()

        self.dicFENm2 = self.training["DICFENM2"]
        self.dic_comments = self.dbop.dic_fen_comments()

        self.liMensBasic = []

        self.siAyuda = False
        self.board.dbvisual_set_show_always(False)

        self.game = Game.Game()

        self.hints = 9999  # Para que analice sin problemas

        self.is_human_side_white = self.training["COLOR"] == "WHITE"
        self.is_engine_side_white = not self.is_human_side_white

        self.tb_with_comments([TB_CLOSE, TB_HELP, TB_REINIT])

        self.main_window.activaJuego(True, False, siAyudas=False)
        self.set_dispatcher(self.player_has_moved)
        self.set_position(self.game.last_position)
        self.show_side_indicator(True)
        self.remove_hints()
        self.put_pieces_bottom(self.is_human_side_white)
        self.pgnRefresh(True)

        self.ponCapInfoPorDefecto()

        self.state = ST_PLAYING

        self.check_boards_setposition()

        self.errores = 0
        self.ini_time = time.time()
        self.muestraInformacion()
        self.play_next_move()

    def calc_totalTiempo(self):
        self.tm = 0
        for game_info in self.liGames:
            for tr in game_info["TRIES"]:
                self.tm += tr["TIME"]

    def get_help(self):
        self.siAyuda = True
        self.board.dbvisual_set_show_always(True)

        self.muestraAyuda()
        self.muestraInformacion()

    def muestraInformacion(self):
        li = []
        li.append("%s: %d/%d" % (_("Line"), self.num_linea + 1, len(self.liGames)))
        li.append("%s: %d" % (_("Errors"), self.errores))
        if self.siAyuda:
            li.append(_("Help activated"))
        self.set_label1("\n".join(li))

        tgm = 0
        for tr in self.game_info["TRIES"]:
            tgm += tr["TIME"]

        mens = "\n".join(self.liMensBasic)
        mens += "\n%s:\n    %s %s\n    %s %s" % (
            _("Working time"),
            time.strftime("%H:%M:%S", time.gmtime(tgm)),
            _("Current"),
            time.strftime("%H:%M:%S", time.gmtime(self.tm)),
            _("Total"),
        )

        self.set_label2(mens)

    def game_finished(self, is_complete):
        self.state = ST_ENDGAME
        tm = time.time() - self.ini_time
        li = [_("Line completed")]
        if self.siAyuda:
            li.append(_("Help activated"))
        if self.errores > 0:
            li.append("%s: %d" % (_("Errors"), self.errores))

        if is_complete:
            mensaje = "\n".join(li)
            self.message_on_pgn(mensaje)
        dictry = {"DATE": Util.today(), "TIME": tm, "AYUDA": self.siAyuda, "ERRORS": self.errores}
        self.game_info["TRIES"].append(dictry)

        sinError = self.errores == 0 and not self.siAyuda
        if is_complete:
            if sinError:
                self.game_info["NOERROR"] += 1
                self.training["NUMLINEA_SEQUENTIAL"] = self.num_linea + 1
                self.main_window.pon_toolbar((TB_CLOSE, TB_NEXT))
            else:
                self.game_info["NOERROR"] -= 1

                self.set_toolbar((TB_CLOSE, TB_REINIT, TB_CONFIG, TB_UTILITIES))
        else:
            if not sinError:
                self.game_info["NOERROR"] -= 1
        self.game_info["NOERROR"] = max(0, self.game_info["NOERROR"])

        self.pgnRefresh(self.is_human_side_white)

        self.state = ST_ENDGAME
        self.calc_totalTiempo()
        is_finished = self.num_linea + 1 >= len(self.liGames) and sinError and is_complete
        self.muestraInformacion()
        if is_finished:
            QTUtil2.message(
                self.main_window,
                "%s\n\n%s"
                % (_("Congratulations, goal achieved"), _("Next time you will start from the first position")),
            )
            self.training["NUMLINEA_SEQUENTIAL"] = 0

        self.dbop.setTraining(self.training)
        if is_finished:
            self.end_game()

    def muestraAyuda(self):
        pv = self.li_pv[len(self.game)]
        self.board.creaFlechaMov(pv[:2], pv[2:4], "mt80")
        fenm2 = self.game.last_position.fenm2()
        for pv1 in self.dicFENm2[fenm2]:
            if pv1 != pv:
                self.board.creaFlechaMov(pv1[:2], pv1[2:4], "ms40")

    def run_action(self, key):
        if key == TB_CLOSE:
            self.end_game()

        elif key == TB_REINIT:
            self.reiniciar()

        elif key == TB_CONFIG:
            self.configurar(siSonidos=True)

        elif key == TB_UTILITIES:
            self.utilities()

        elif key == TB_NEXT:
            self.reinicio(self.dbop)

        elif key == TB_HELP:
            self.get_help()

        elif key == TB_COMMENTS:
            self.change_comments()

        else:
            Manager.Manager.rutinaAccionDef(self, key)

    def final_x(self):
        return self.end_game()

    def end_game(self):
        self.dbop.close()
        self.board.restoreVisual()
        self.procesador.start()
        if self.modo == "static":
            self.procesador.openings_training_static(self.pathFichero)
        else:
            self.procesador.openings()
        return False

    def reiniciar(self):
        if len(self.game) > 0 and self.state != ST_ENDGAME:
            self.game_finished(False)
        self.main_window.activaInformacionPGN(False)
        self.reinicio(self.dbop)

    def play_next_move(self):
        self.muestraInformacion()
        if self.state == ST_ENDGAME:
            return

        self.state = ST_PLAYING

        self.human_is_playing = False
        self.put_view()

        is_white = self.game.last_position.is_white

        self.set_side_indicator(is_white)
        self.refresh()

        siRival = is_white == self.is_engine_side_white

        num_moves = len(self.game)
        if num_moves >= self.numPV:
            self.game_finished(True)
            return
        pv = self.li_pv[num_moves]

        if siRival:
            self.disable_all()

            self.rm_rival = EngineResponse.EngineResponse("Opening", self.is_engine_side_white)
            self.rm_rival.from_sq = pv[:2]
            self.rm_rival.to_sq = pv[2:4]
            self.rm_rival.promotion = pv[4:]

            self.rival_has_moved(self.rm_rival)
            self.play_next_move()

        else:
            self.activate_side(is_white)
            self.human_is_playing = True

    def player_has_moved(self, from_sq, to_sq, promotion=""):
        move = self.check_human_move(from_sq, to_sq, promotion)
        if not move:
            self.beepError()
            return False
        if promotion:
            pass
        pvSel = move.movimiento().lower()
        pvObj = self.li_pv[len(self.game)]

        if pvSel != pvObj:
            self.beepError()
            fenm2 = move.position_before.fenm2()
            li = self.dicFENm2.get(fenm2, set())
            if pvSel in li:
                mens = _("You have selected a correct move, but this line uses another one.")
                QTUtil2.mensajeTemporal(self.main_window, mens, 2, physical_pos="tb", background="#C3D6E8")
                self.sigueHumano()
                return False

            self.errores += 1
            mens = "%s: %d" % (_("Error"), self.errores)
            QTUtil2.mensajeTemporal(
                self.main_window, mens, 0.8, physical_pos="ad", background="#FF9B00", pmImagen=Iconos.pmError()
            )
            self.muestraInformacion()
            self.sigueHumano()
            return False

        self.move_the_pieces(move.liMovs)

        self.add_move(move, True)
        self.play_next_move()
        return True

    def rival_has_moved(self, engine_response):
        from_sq = engine_response.from_sq
        to_sq = engine_response.to_sq

        promotion = engine_response.promotion

        ok, mens, move = Move.get_game_move(self.game, self.game.last_position, from_sq, to_sq, promotion)
        if ok:
            self.add_move(move, False)
            self.move_the_pieces(move.liMovs, True)

            self.error = ""

            return True
        else:
            self.error = mens
            return False
