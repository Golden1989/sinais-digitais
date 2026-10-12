"""Prepara o áudio usado no notebook (roda uma única vez).

Fonte: University of Iowa Electronic Music Studios, Musical Instrument Samples (MIS),
arquivo "Guitar.mf.sulG.C4B4.mono.aif" (violão, corda Sol, dinâmica mezzo-forte,
escala cromática de Dó4 a Si4, mono, 24 bits, 96 kHz).

O que o script faz:
  1. baixa o AIFF original para data/fonte/ (se ainda não estiver lá);
  2. lê o AIFF com um leitor mínimo (o módulo `aifc` saiu da biblioteca padrão no
     Python 3.13 e o scipy não lê AIFF), evitando dependências extras;
  3. separa as notas pela envoltória de energia e escolhe a mais próxima de 440 Hz (Lá4,
     tocado na 14ª casa da corda Sol);
  4. reamostra de 96 kHz para 48 kHz (com filtro anti-aliasing) e salva
     data/la4_violao.wav em PCM de 16 bits.

Uso (a partir da raiz do repositório):
    python scripts/preparar_audio.py
"""
from pathlib import Path
import struct
import urllib.request

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, resample_poly, sosfiltfilt

RAIZ = Path(__file__).resolve().parent.parent
URL = ("https://theremin.music.uiowa.edu/sound%20files/MIS/Piano_Other/guitar/"
       "Guitar.mf.sulG.C4B4.mono.aif")
AIFF = RAIZ / "data" / "fonte" / "Guitar.mf.sulG.C4B4.mono.aif"
SAIDA = RAIZ / "data" / "la4_violao.wav"

F_ALVO = 440.0       # Hz, Lá4
DURACAO = 2.0        # s de áudio a guardar (a nota decai até o ruído de fundo em ~1,5 s)
PRE_ATAQUE = 0.05    # s de silêncio mantidos antes do ataque da nota
FS_SAIDA = 48_000    # Hz


def baixar_se_preciso():
    """Baixa o AIFF original caso ele não exista localmente."""
    if AIFF.exists():
        return
    AIFF.parent.mkdir(parents=True, exist_ok=True)
    print(f"Baixando {URL} ...")
    urllib.request.urlretrieve(URL, AIFF)


def ler_aiff(caminho):
    """Lê um AIFF PCM sem compressão (mono, 16 ou 24 bits). Retorna (fs, x em [-1, 1])."""
    dados = caminho.read_bytes()
    assert dados[:4] == b"FORM" and dados[8:12] == b"AIFF", "não é um AIFF sem compressão"
    pos, fs, bits, n_quadros, bruto = 12, None, None, None, None
    while pos < len(dados) - 8:
        ident = dados[pos:pos + 4]
        tam = struct.unpack(">I", dados[pos + 4:pos + 8])[0]
        corpo = dados[pos + 8:pos + 8 + tam]
        if ident == b"COMM":
            canais, n_quadros, bits = struct.unpack(">hIh", corpo[:8])
            assert canais == 1, "esperado arquivo mono"
            # taxa de amostragem em ponto flutuante estendido de 80 bits (IEEE 754)
            expoente, mantissa = struct.unpack(">HQ", corpo[8:18])
            fs = mantissa * 2.0 ** ((expoente & 0x7FFF) - 16383 - 63)
        elif ident == b"SSND":
            deslocamento = struct.unpack(">I", corpo[:4])[0]
            bruto = corpo[8 + deslocamento:]
        pos += 8 + tam + (tam & 1)          # blocos são alinhados em bytes pares
    n_bytes = bits // 8
    b = np.frombuffer(bruto[:n_quadros * n_bytes], dtype=np.uint8)
    b = b.reshape(-1, n_bytes).astype(np.int64)
    x = np.zeros(len(b), dtype=np.int64)
    for k in range(n_bytes):                # big-endian: byte mais significativo primeiro
        x = (x << 8) | b[:, k]
    x = np.where(x >= 1 << (bits - 1), x - (1 << bits), x)
    return int(round(fs)), x / float(1 << (bits - 1))


def localizar_notas(x, fs, bloco=0.05, limiar_db=35.0, dur_min=0.5):
    """Separa as notas pela envoltória RMS. Retorna lista de (início, fim) em amostras."""
    h = int(bloco * fs)
    env = np.sqrt(np.mean(x[:len(x) // h * h].reshape(-1, h) ** 2, axis=1))
    db = 20 * np.log10(env + 1e-12)
    ativo = np.r_[False, db > db.max() - limiar_db, False]
    bordas = np.diff(ativo.astype(int))
    inicios, fins = np.where(bordas == 1)[0], np.where(bordas == -1)[0]
    return [(i * h, f * h) for i, f in zip(inicios, fins) if (f - i) * bloco >= dur_min]


def frequencia_dominante(x, fs, fmin=200.0, fmax=1000.0):
    """Frequência do maior pico do espectro entre fmin e fmax (estimativa grosseira)."""
    X = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1 / fs)
    faixa = (f > fmin) & (f < fmax)
    return f[faixa][np.argmax(X[faixa])]


def main():
    baixar_se_preciso()
    fs, x = ler_aiff(AIFF)
    print(f"AIFF original: fs = {fs} Hz, duração = {len(x) / fs:.2f} s")

    # Para localizar as notas, tira-se antes o ruído grave da sala (abaixo de 150 Hz),
    # que atrapalha a envoltória. O trecho salvo, porém, sai do sinal ORIGINAL, sem filtro.
    sos = butter(4, 150.0, btype="highpass", fs=fs, output="sos")
    x_det = sosfiltfilt(sos, x)
    notas = [n for n in localizar_notas(x_det, fs) if n[0] + int(1.2 * fs) < len(x)]
    freqs = [frequencia_dominante(x_det[i + int(0.2 * fs):i + int(1.2 * fs)], fs) for i, _ in notas]
    for (i, f), fr in zip(notas, freqs):
        print(f"  nota em {i / fs:6.2f}–{f / fs:6.2f} s: pico em {fr:6.1f} Hz")
    k = int(np.argmin(np.abs(np.array(freqs) - F_ALVO)))
    inicio = notas[k][0] - int(PRE_ATAQUE * fs)
    trecho = x[inicio:inicio + int(DURACAO * fs)]
    print(f"Nota escolhida (mais próxima de {F_ALVO:.0f} Hz): {freqs[k]:.1f} Hz, "
          f"a partir de {inicio / fs:.2f} s")

    # 96 kHz -> 48 kHz: resample_poly aplica um FIR passa-baixas antes de decimar
    y = resample_poly(trecho, FS_SAIDA, fs)
    y = 0.9 * y / np.max(np.abs(y))
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(SAIDA, FS_SAIDA, np.round(y * 32767).astype(np.int16))
    print(f"Salvo {SAIDA.relative_to(RAIZ)}: fs = {FS_SAIDA} Hz, {len(y)} amostras, "
          f"{len(y) / FS_SAIDA:.2f} s")


if __name__ == "__main__":
    main()
