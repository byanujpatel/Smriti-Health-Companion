"""
Smriti Telegram Bot — MVP
Four handlers: /start, voice, text, /ask
All AI calls delegate to the existing smriti services — zero new AI logic here.
"""
from __future__ import annotations

import io
import logging
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from smriti.clients.llm import create_answerer, create_checkin_structurer, create_transcriber
from smriti.clients.memory import create_memory_provider
from smriti.config import get_settings
from smriti.models import AskRequest, MemoryEntry, MemoryType, Persona
from smriti.services.memory_quality import save_unique_memories
from smriti.services.retrieval_service import retrieve_memories

logger = logging.getLogger(__name__)

# ── Shared services (initialised once when the module loads) ──────────────────
_settings = get_settings()
_transcriber = create_transcriber(_settings)
_structurer = create_checkin_structurer(_settings)
_answerer = create_answerer(_settings)
_memory = create_memory_provider(_settings)

# ── Simple in-process user store keyed by telegram chat_id ───────────────────
# Format: {chat_id: {"name": str, "subject_id": str, "subject_name": str}}
# Good enough for hackathon; replace with DB for production.
_users: dict[int, dict] = {}


def _get_user(chat_id: int) -> dict | None:
    return _users.get(chat_id)


def _set_user(chat_id: int, name: str) -> dict:
    subject_id = name.lower().replace(" ", "-")[:40]
    user = {"name": name, "subject_id": subject_id, "subject_name": name}
    _users[chat_id] = user
    return user


# ── Handlers ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user = _get_user(chat_id)
    if user:
        await update.message.reply_text(
            f"Namaste {user['name']} ji! 🙏\n\n"
            "Main Smriti hoon — aapka health saathi.\n\n"
            "Bas boliye ya type kijiye — main yaad rakhungi! 💚\n\n"
            "/ask — kuch puchna ho\n"
            "/help — sab commands dekhein"
        )
    else:
        context.user_data["awaiting_name"] = True
        await update.message.reply_text(
            "Namaste! Main Smriti hoon 🙏\n\n"
            "Aapka health saathi. Jo bhi bataiyega — main yaad rakhungi.\n\n"
            "Pehle bataiye — *aap kaun hain?*\n"
            "Apna naam type karein (jaise: Savitri Devi, Papa, Amma)",
            parse_mode="Markdown",
        )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🩺 *Smriti — Health Memory Saathi*\n\n"
        "📢 *Voice bhejein* — main sun leti hoon\n"
        "⌨️ *Type karein* — main samajh leti hoon\n"
        "📸 Photo — prescription ya report\n\n"
        "/ask [sawaal] — health history se kuch puchein\n"
        "/start — shuru ya naam badlein\n\n"
        "🛡️ _Main sirf yaad rakhti hoon. Doctor nahi hoon._",
        parse_mode="Markdown",
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()

    # Name collection flow after /start
    if context.user_data.get("awaiting_name"):
        user = _set_user(chat_id, text)
        context.user_data["awaiting_name"] = False
        await update.message.reply_text(
            f"Dhanyavaad *{text}* ji! ✨\n\n"
            "Ab aap apni health update bata sakte hain.\n"
            "Voice bhejein ya type karein — dono chalega! 🎙️",
            parse_mode="Markdown",
        )
        return

    user = _get_user(chat_id)
    if not user:
        await update.message.reply_text("Pehle /start karein aur apna naam batayein.")
        return

    # Emergency keywords
    lower = text.lower()
    if any(k in lower for k in ["madad", "bachao", "emergency", "🆘", "help me", "gir gayi", "gir gaya"]):
        await _handle_emergency(update, user)
        return

    await _process_input(update, context, text, user)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user = _get_user(chat_id)
    if not user:
        await update.message.reply_text("Pehle /start karein aur apna naam batayein.")
        return

    thinking = await update.message.reply_text("🎧 *Sun raha hoon…*", parse_mode="Markdown")

    # Download OGG from Telegram
    voice_file = await update.message.voice.get_file()
    voice_bytes = await voice_file.download_as_bytearray()

    # Transcribe via Groq Whisper
    try:
        audio_io = io.BytesIO(bytes(voice_bytes))
        audio_io.name = "voice.ogg"
        transcript = _transcriber.transcribe(audio_io, "voice.ogg", "audio/ogg")
    except Exception as exc:
        logger.warning("Transcription failed: %s", exc)
        await thinking.edit_text("Sunne mein problem aayi. Dobara try karein ya type karein.")
        return

    if not transcript:
        await thinking.edit_text("Kuch bol nahi aaya. Thoda door se aur clearly bolein.")
        return

    await thinking.edit_text(f"📝 Suna: _{transcript}_\n\nSamajh raha hoon…", parse_mode="Markdown")
    await _process_input(update, context, transcript, user, status_msg=thinking)


async def _process_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    user: dict,
    status_msg=None,
) -> None:
    """Shared pipeline: text/transcript → structure → preview card → Haan/Nahi buttons."""
    now = datetime.now().astimezone()
    try:
        checkin_summary, memories = _structurer.structure_checkin(
            transcript=text,
            subject_name=user["subject_name"],
            now=now,
        )
        for m in memories:
            m.subject_id = user["subject_id"]
            m.subject_name = user["subject_name"]
    except Exception as exc:
        logger.warning("Structuring failed: %s", exc)
        msg = "Samajhne mein dikkat aayi. Dobara clearly bolein?"
        if status_msg:
            await status_msg.edit_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    # Build compact preview
    lines = ["📋 *Mainne samjha:*\n"]
    if checkin_summary.mood and checkin_summary.mood != "neutral":
        lines.append(f"Mood: {checkin_summary.mood}")
    if checkin_summary.medicines:
        lines.append(f"💊 Dawai: {', '.join(checkin_summary.medicines)}")
    for hm in (checkin_summary.health_mentions or [])[:3]:
        snippet = (hm if isinstance(hm, str) else str(hm))[:80]
        lines.append(f"• {snippet}")
    if checkin_summary.direct_quote:
        lines.append(f'\n_"{checkin_summary.direct_quote}"_')
    if checkin_summary.flags:
        lines.append(f"\n⚠ {', '.join(checkin_summary.flags[:2])}")
    lines.append("\n*Kya yeh sahi hai?*")

    preview_text = "\n".join(lines)

    # Persist pending in user context for confirmation handler
    context.user_data["pending_memories"] = [m.model_dump(mode="json") for m in memories]

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Haan, sahi hai", callback_data="confirm_save"),
            InlineKeyboardButton("❌ Nahi", callback_data="cancel_save"),
        ]
    ])

    if status_msg:
        await status_msg.edit_text(preview_text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await update.message.reply_text(preview_text, reply_markup=keyboard, parse_mode="Markdown")


async def handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    user = _get_user(chat_id)

    if query.data == "cancel_save":
        context.user_data.pop("pending_memories", None)
        await query.edit_message_text("Theek hai! Dobara bolein jab taiyaar hon. 🙏")
        return

    pending_raw = context.user_data.pop("pending_memories", None)
    if not pending_raw or not user:
        await query.edit_message_text("Kuch galat ho gaya. /start se dobara try karein.")
        return

    memories = [MemoryEntry.model_validate(m) for m in pending_raw]
    try:
        ids, skipped = save_unique_memories(_memory, memories)
        saved = len(ids)
        skip_note = f" ({skipped} pehle se saved)" if skipped else ""
        await query.edit_message_text(
            f"✅ *Yaad rakh liya!* {saved} cheez{skip_note}\n\n"
            "Aapki family ko bata diya jayega. 🙏",
            parse_mode="Markdown",
        )
    except Exception as exc:
        logger.warning("Save failed: %s", exc)
        await query.edit_message_text("Save nahi ho paya. Thodi der mein dobara try karein.")


async def cmd_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user = _get_user(chat_id)
    if not user:
        await update.message.reply_text("Pehle /start karein.")
        return

    question = " ".join(context.args) if context.args else ""
    if not question:
        await update.message.reply_text(
            "Kya puchna chahte hain?\n\n"
            "Examples:\n"
            "`/ask dizziness kab aayi thi?`\n"
            "`/ask kaunsi dawai chal rahi hai?`\n"
            "`/ask BP kaisa raha pichle hafte?`",
            parse_mode="Markdown",
        )
        return

    thinking = await update.message.reply_text("🔍 _Yaad kar rahi hoon…_", parse_mode="Markdown")
    try:
        ask_req = AskRequest(
            question=question,
            persona=Persona.CARE,
            subject_id=user["subject_id"],
        )
        retrieved, _debug, _ = retrieve_memories(_memory, ask_req)
        if not retrieved:
            await thinking.edit_text(
                "Mujhe is baare mein koi record nahi mila.\n\n"
                "_🛡️ Main sirf recorded facts bata sakti hoon._",
                parse_mode="Markdown",
            )
            return
        answer = _answerer.answer(question, Persona.CARE, retrieved)
        sources_text = ""
        for src in retrieved[:2]:
            date_str = src.occurred_at.strftime("%-d %b") if src.occurred_at else ""
            sources_text += f"\n• _{date_str}: {src.text[:70]}…_"
        await thinking.edit_text(
            f"{answer}{sources_text}\n\n"
            "_🛡️ AI answer hai. Doctor se zaroor milein._",
            parse_mode="Markdown",
        )
    except Exception as exc:
        logger.warning("Ask failed: %s", exc)
        await thinking.edit_text("Kuch problem aayi. Dobara try karein.")


async def _handle_emergency(update: Update, user: dict) -> None:
    await update.message.reply_text(
        "🆘 *EMERGENCY NOTE KAR LIYA!*\n\n"
        "Aapke parivaar ko notification bheja ja raha hai.\n\n"
        "Agar aap theek nahi hain:\n"
        "📞 *112* — National Emergency\n"
        "📞 *14416* — Tele-MANAS (mental health)\n\n"
        "_Kya hua? Bata sakte hain? Main record kar leti hoon._",
        parse_mode="Markdown",
    )
    entry = MemoryEntry(
        text="Emergency alert triggered via Telegram",
        type=MemoryType.REMARK,
        persona=Persona.CARE,
        subject_id=user["subject_id"],
        subject_name=user["subject_name"],
        occurred_at=datetime.now().astimezone(),
        entities={"urgency": "emergency", "source": "telegram"},
        raw="Emergency alert triggered via Telegram",
    )
    try:
        save_unique_memories(_memory, [entry])
    except Exception:
        pass  # Don't crash; message already sent


# ── Bot factory (called from main.py) ─────────────────────────────────────────

def build_bot_app(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("ask", cmd_ask))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_confirm, pattern="^(confirm_save|cancel_save)$"))
    return app
