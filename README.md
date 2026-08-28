# 🎙️ Podcast Brief Diario

Convierte automáticamente el brief diario de Rufino (agenda, correos, pendientes) en un archivo de audio MP3 y lo envía a un chat de Telegram.

## ¿Cómo funciona?

1. Una tarea programada de **Claude Cowork** abre cada mañana un issue con el label `brief-diario` y el guion en español como cuerpo.
2. El **GitHub Action** detecta el issue, convierte el texto a audio usando [`edge-tts`](https://github.com/rany2/edge-tts) (voces neuronales de Microsoft Edge, sin API key) y envía el MP3 al chat de Telegram.
3. Si el envío fue exitoso, el issue se cierra automáticamente. Si falló, se comenta el error y el issue queda abierto para reintento manual.

```
Issue abierto (label: brief-diario)
        │
        ▼
 edge-tts → MP3 (voz: es-MX-JorgeNeural)
        │
        ▼
 Telegram Bot API → sendAudio
        │
   ┌────┴────┐
   ▼         ▼
 Éxito    Error
Cerrar   Comentar
 issue    y dejar
         abierto
```

## Secrets requeridos

Ve a **Settings → Secrets and variables → Actions** en este repo y añade:

| Secret | Descripción |
|--------|-------------|
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram. Obténlo hablando con [@BotFather](https://t.me/BotFather) y creando un bot (`/newbot`). Formato: `123456789:AABBccDDeeFF...` |
| `TELEGRAM_CHAT_ID` | ID del chat o canal al que se enviará el audio. Puedes obtenerlo enviando un mensaje al bot y consultando `https://api.telegram.org/bot<TOKEN>/getUpdates`. Para canales privados usar el formato `-100xxxxxxxxxx`. |

## Label requerido

El workflow filtra issues por el label `brief-diario`. Créalo en **Issues → Labels → New label** (o ya fue creado automáticamente si ejecutaste el setup).

## Prueba manual

Puedes probar el workflow sin crear un issue real:

1. Ve a **Actions → Brief Diario → Podcast Telegram**.
2. Haz clic en **Run workflow**.
3. Opcionalmente escribe un guion de prueba en el campo de texto.
4. Haz clic en **Run workflow** (verde).

## Voz del audio

La voz por defecto es **`es-MX-JorgeNeural`** (hombre, español de México). Para cambiar a voz femenina, edita `VOICE` en [`scripts/brief_to_audio.py`](scripts/brief_to_audio.py):

```python
VOICE = "es-MX-DaliaNeural"   # Mujer, español de México
```

Otras opciones de edge-tts para español:

| Voz | Género | Variante |
|-----|--------|----------|
| `es-MX-JorgeNeural` | Hombre | México |
| `es-MX-DaliaNeural` | Mujer | México |
| `es-ES-AlvaroNeural` | Hombre | España |
| `es-ES-ElviraNeural` | Mujer | España |
| `es-AR-TomasNeural` | Hombre | Argentina |

## Estructura del repo

```
.
├── .github/
│   └── workflows/
│       └── brief_diario.yml   # GitHub Action principal
├── scripts/
│   ├── brief_to_audio.py      # Script Python: TTS + Telegram
│   └── requirements.txt       # edge-tts
└── README.md
```
