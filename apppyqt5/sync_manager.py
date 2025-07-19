# sync_manager.py

import os
import sys
import time
import json
import shutil
import logging
import sqlite3

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel
)
from app.database.oracle_connector import consulta_notas_oracle
from app.automation.web_automation import abrir_atividade

# ——————————————————————————————————————————————————————————————————————————————
# Configurações
NETWORK_ROOT = r"\\pfl-cps-file\Divisao_GD\web_automation_pp"
DB_PATH      = os.path.join(NETWORK_ROOT, "dados_sync.db")
LOG_PATH     = os.path.join(NETWORK_ROOT, "sync_manager.log")
SYNC_INTERVAL_SECONDS = 1 * 60  # 30 minutos
# ——————————————————————————————————————————————————————————————————————————————

# ——————————————————————————————————————————————————————————————————————————————
# Logger
logger = logging.getLogger("sync_manager")
logger.setLevel(logging.INFO)
fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(fh)
# ——————————————————————————————————————————————————————————————————————————————

# ——————————————————————————————————————————————————————————————————————————————
# Banco local (SQLite) — inicializa esquema
def init_db():
    os.makedirs(NETWORK_ROOT, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS sync_records (
        nr_atividade TEXT PRIMARY KEY,
        cd_projeto   TEXT,
        valores_site TEXT,
        arquivos     TEXT,
        file_sizes   TEXT,
        last_sync    TEXT,
        status       TEXT
    )
    """)
    conn.commit()
    conn.close()

# ——————————————————————————————————————————————————————————————————————————————

class SyncThread(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        logger.info("Sync thread started")
        self.log_signal.emit("👷‍♀️ Sync iniciado")
        init_db()

        while not self.isInterruptionRequested():
            try:
                notes = consulta_notas_oracle()
            except Exception as e:
                msg = f"Erro ao consultar notas: {e}"
                logger.error(msg)
                self.log_signal.emit(msg)
                break

            for note in notes:
                if self.isInterruptionRequested():
                    break

                nr   = str(note["NR_ATIVIDADE"])
                cd   = str(note["CD_PROJETO"])
                dest = os.path.join(NETWORK_ROOT, nr)

                # verifica existência e integridade mínima
                needs_sync = True
                if os.path.isdir(dest):
                    files = os.listdir(dest)
                    if files:
                        # todos maior que zero?
                        sizes = [os.path.getsize(os.path.join(dest, f)) for f in files]
                        if all(s > 0 for s in sizes):
                            needs_sync = False

                if not needs_sync:
                    msg = f"✔ Nota {nr} já está atualizada"
                    logger.info(msg)
                    self.log_signal.emit(msg)
                    continue

                # sincronizar
                msg = f"🔄 Sincronizando nota {nr}..."
                logger.info(msg)
                self.log_signal.emit(msg)

                try:
                    # baixa para pasta local (Downloads/<nr>)
                    local_folder, valores_site = abrir_atividade(nr, cd)

                    # prepara destino em rede
                    if os.path.exists(dest):
                        shutil.rmtree(dest)
                    shutil.move(local_folder, dest)

                    # coleta lista de arquivos e tamanhos
                    arquivos = sorted(os.listdir(dest))
                    file_sizes = {
                        f: os.path.getsize(os.path.join(dest, f))
                        for f in arquivos
                    }

                    # grava no DB
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("""
                        INSERT OR REPLACE INTO sync_records
                          (nr_atividade, cd_projeto, valores_site, arquivos, file_sizes, last_sync, status)
                        VALUES (?,?,?,?,?,?,?)
                    """, (
                        nr,
                        cd,
                        json.dumps(valores_site, ensure_ascii=False),
                        json.dumps(arquivos,     ensure_ascii=False),
                        json.dumps(file_sizes,   ensure_ascii=False),
                        time.strftime("%Y-%m-%d %H:%M:%S"),
                        "OK"
                    ))
                    conn.commit()
                    conn.close()

                    msg = f"✅ Nota {nr} sincronizada com sucesso"
                    logger.info(msg)
                    self.log_signal.emit(msg)

                except Exception as e:
                    msg = f"❌ Erro synchronizando nota {nr}: {e}"
                    logger.error(msg, exc_info=True)
                    self.log_signal.emit(msg)

            # ciclo completo
            msg = f"⏱ Ciclo concluído. Aguardando {SYNC_INTERVAL_SECONDS//60} minutos..."
            logger.info(msg)
            self.log_signal.emit(msg)

            # espera com checagem de interrupção
            for _ in range(SYNC_INTERVAL_SECONDS):
                if self.isInterruptionRequested():
                    break
                time.sleep(1)

        logger.info("Sync thread stopping")
        self.log_signal.emit("🛑 Sync interrompido")


class SyncManagerUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sync Manager")
        self.resize(600, 400)

        self.thread = None

        # Layout
        v = QVBoxLayout(self)

        # Status label
        self.lbl_status = QLabel("Pronto")
        v.addWidget(self.lbl_status)

        # Log view
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        v.addWidget(self.log_view, 1)

        # Botões
        h = QHBoxLayout()
        self.btn_start = QPushButton("▶ Iniciar Sync")
        self.btn_stop  = QPushButton("⏸ Parar Sync")
        self.btn_stop.setEnabled(False)
        h.addWidget(self.btn_start)
        h.addWidget(self.btn_stop)
        v.addLayout(h)

        # Conexões
        self.btn_start.clicked.connect(self.start_sync)
        self.btn_stop.clicked.connect(self.stop_sync)

    def append_log(self, msg: str):
        timestamp = time.strftime("%H:%M:%S")
        self.log_view.append(f"[{timestamp}] {msg}")
        self.lbl_status.setText(msg)

    def start_sync(self):
        if self.thread and self.thread.isRunning():
            return
        self.thread = SyncThread()
        self.thread.log_signal.connect(self.append_log)
        self.thread.start()
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.append_log("▶ Sync iniciado pelo usuário")

    def stop_sync(self):
        if not self.thread:
            return
        self.thread.requestInterruption()
        self.thread.wait()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.append_log("⏸ Sync parado pelo usuário")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SyncManagerUI()
    win.show()
    sys.exit(app.exec_())
