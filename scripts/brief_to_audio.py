#!/usr/bin/env python3
"""
brief_to_audio.py
Convierte el cuerpo de un issue de GitHub a audio MP3 con edge-tts
y lo envía al chat de Telegram configurado.

Variables de entorno requeridas:
  ISSUE_BODY          - Texto del guion (body del issue o texto de prueba)
  ISSUE_NUMBER        - Número del issue (0 para pruebas manuales)
  TELEGRAM_BOT_TOKEN  - Token del bot de Telegram
  TELEGRAM_CHAT_ID    - ID del chat/canal de destino
"""

import asyncio
import os
import sys
import json
import tempfile
import urllib.request
import urllib.parse
import urllib.error

import edge_tts

# ── Configuración ──────────────────────────────────────────────────────────────
VOICE = "es-MX-JorgeNeural"          # Alternativa: es-MX-DaliaNeural
TELEGRAM_API = "https://api.telegram.org"


def get_env(name: str, required: bool = True) -> str:
    value = os.environ.get(name, "").strip()
    if required and not value:
        print(f"[ERROR] Variable de entorno '{name}' no definida o vacía.", file=sys.stderr)
        sys.exit(1)
    return value


async def text_to_mp3(text: str, output_path: str) -> None:
    """Genera el archivo MP3 con edge-tts."""
    print(f"[INFO] Generando audio con voz '{VOICE}' ({len(text)} caracteres)...")
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_path)
    size_kb = os.path.getsize(output_path) / 1024
    print(f"[INFO] Audio generado: {output_path} ({size_kb:.1f} KB)")


def send_audio_to_telegram(mp3_path: str, bot_token: str, chat_id: str, caption: str) -> bool:
    """
    Envía el MP3 a Telegram vía multipart/form-data.
    Devuelve True si fue exitoso, False en caso contrario.
    """
    url = f"{TELEGRAM_API}/bot{bot_token}/sendAudio"

    # Construir multipart manualmente (sin dependencias externas)
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    crlf = b"\r\n"

    with open(mp3_path, "rb") as f:
        audio_data = f.read()

    filename = os.path.basename(mp3_path)
    caption_bytes = caption.encode("utf-8")
    chat_id_bytes = chat_id.encode("utf-8")

    parts = []

    # chat_id
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n".encode()
        + chat_id_bytes + crlf
    )

    # caption
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n".encode()
        + caption_bytes + crlf
    )

    # audio file
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"audio\"; filename=\"{filename}\"\r\nContent-Type: audio/mpeg\r\n\r\n".encode()
        + audio_data + crlf
    )

    # closing boundary
    parts.append(f"--{boundary}--\r\n".encode())

    body = b"".join(parts)
    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(body)),
    }

    print(f"[INFO] Enviando audio a Telegram (chat_id={chat_id})...")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            resp_body = resp.read().decode("utf-8")
            data = json.loads(resp_body)
            if data.get("ok"):
                msg_id = data.get("result", {}).get("message_id", "?")
                print(f"[OK] Audio enviado. message_id={msg_id}")
                return True
            else:
                print(f"[ERROR] Telegram respondió ok=false: {resp_body}", file=sys.stderr)
                return False
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode("utf-8", errors="replace")
        print(f"[ERROR] HTTP {e.code} al enviar a Telegram: {resp_body}", file=sys.stderr)
        return False
    except Exception as exc:
        print(f"[ERROR] Excepción al enviar a Telegram: {exc}", file=sys.stderr)
        return False


def main() -> None:
    issue_body = get_env("ISSUE_BODY")
    issue_number = get_env("ISSUE_NUMBER", required=False) or "0"
    bot_token = get_env("TELEGRAM_BOT_TOKEN")
    chat_id = get_env("TELEGRAM_CHAT_ID")

    if not issue_body:
        print("[ERROR] ISSUE_BODY está vacío. No hay guion que procesar.", file=sys.stderr)
        sys.exit(1)

    # Crear archivo temporal MP3
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        mp3_path = tmp.name

    try:
        # 1. Generar audio
        asyncio.run(text_to_mp3(issue_body, mp3_path))

        # 2. Enviar a Telegram
        caption = f"🎙️ Brief diario #{issue_number}"
        success = send_audio_to_telegram(mp3_path, bot_token, chat_id, caption)

        if not success:
            sys.exit(2)   # exit code 2 → el workflow comentará el error y dejará el issue abierto

    finally:
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
            print(f"[INFO] Archivo temporal eliminado: {mp3_path}")


if __name__ == "__main__":
    main()
