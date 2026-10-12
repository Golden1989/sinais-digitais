# Do sinal ao espectro: um analisador e filtro de sinais

Sistematização da disciplina de **Métodos Matemáticos**: Séries de Fourier → Transformada de Fourier → Transformada de Laplace, aplicadas a um único sinal real.

O sinal é a gravação de um **Lá4 de violão** (440 Hz teóricos). O notebook:

1. aproxima uma onda quadrada por séries de Fourier e mede o fenômeno de Gibbs;
2. analisa a nota com a FFT (fundamental, harmônicos, piso de ruído, Nyquist e aliasing);
3. contamina a gravação com zumbido de 60 Hz e ruído branco, e a filtra com um notch em 60 Hz mais um passa-baixas, aplicados no domínio da frequência;
4. descreve o mesmo filtro como sistema linear, com função de transferência $H(s)$, polos, zeros e diagrama de Bode, e liga o mapa de polos e zeros ao espectro.

Todo o relatório (texto, fórmulas, figuras e interpretações) está dentro do notebook `notebooks/sistematizacao.ipynb`, que já está executado e com as saídas visíveis.

## Autora

- Isabella Campos Bueno

## Como instalar

Desenvolvido e testado com Python 3.14 no Windows (as versões em `requirements.txt` são as desse ambiente).

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (no Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
```

## Como rodar

**No VS Code:** abra a pasta do projeto, abra `notebooks/sistematizacao.ipynb`, selecione o kernel do ambiente `.venv` e clique em *Run All*.

**Pela linha de comando** (executa de cima a baixo e grava as saídas no próprio arquivo):

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/sistematizacao.ipynb
```

A execução é rápida (da ordem de um minuto). Ela recria todas as figuras em `outputs/figures/` e os três áudios em `outputs/audio/`. O ruído usa semente fixa (`np.random.default_rng(42)`), então os resultados são sempre os mesmos.

O áudio `data/la4_violao.wav` já está no repositório; não é preciso baixar nada para rodar o notebook.

## Estrutura de pastas

```
README.md
requirements.txt                 versões fixadas das bibliotecas
.gitignore
data/
  la4_violao.wav                 nota usada no notebook (mono, 48 kHz, 16 bits, 2 s)
  fonte/                         gravação original de 25 MB (fora do Git; ver abaixo)
notebooks/
  sistematizacao.ipynb           notebook único com as 4 etapas e o relatório
outputs/
  audio/                         original.wav, ruidoso.wav, filtrado.wav
  figures/                       todas as figuras em PNG (200 dpi), fig01 a fig19
scripts/
  preparar_audio.py              recorta a nota a partir da gravação original
```

## De onde veio o áudio

- **Fonte:** University of Iowa Electronic Music Studios, *Musical Instrument Samples* (MIS), gravações de Lawrence Fritts. <https://theremin.music.uiowa.edu/MIS.html>
- **Arquivo original:** `Guitar.mf.sulG.C4B4.mono.aif` (violão, corda Sol, dinâmica *mezzo-forte*, escala cromática de Dó4 a Si4, mono, 24 bits, 96 kHz), na página <https://theremin.music.uiowa.edu/MISguitar.html>.
- **Licença:** a página do acervo informa que as gravações estão disponíveis gratuitamente desde 1997 e "may be downloaded and used for any projects, without restrictions".

O script `scripts/preparar_audio.py` reproduz a preparação: baixa o AIFF original para `data/fonte/`, localiza a nota mais próxima de 440 Hz (o Lá4, tocado na 14ª casa da corda Sol), recorta 2 s a partir de 50 ms antes do ataque, reamostra de 96 kHz para 48 kHz e salva `data/la4_violao.wav`. Só é preciso rodá-lo se quiser refazer esse arquivo:

```bash
python scripts/preparar_audio.py
```

O zumbido de 60 Hz e o ruído branco **não** fazem parte da gravação: são gerados dentro do notebook (Etapa 3), de forma controlada e documentada.

## Principais resultados

| Grandeza | Valor |
|---|---|
| Fundamental medida | 437,6 Hz (teórica: 440 Hz; erro de −2,4 Hz, cerca de −9 cents) |
| Harmônicos detectados | 1, 2, 3, 4 e 6 |
| SNR do sinal contaminado | 2,9 dB |
| SNR após o filtro | 12,1 dB (filtro causal) / 15,5 dB (versão de fase zero) |
| Zeros do notch | ±j377,0 rad/s (60 Hz) |
| Polos do notch (Q = 30) | −6,28 ± j376,9 rad/s |
| Polos do passa-baixas (6 kHz) | (−26,7 ± j26,7) × 10³ rad/s |
