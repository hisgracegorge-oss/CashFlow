import logging
import os

import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
FRANKFURTER_URL = "https://api.frankfurter.app/latest"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "\U0001F44B Welcome to CashFlow!\n\n"
        "I give you live forex exchange rates and convert currencies.\n\n"
        "Commands:\n"
        "/rate <FROM> <TO> - e.g. /rate USD EUR\n"
        "/convert <AMOUNT> <FROM> <TO> - e.g. /convert 100 USD EUR\n"
        "/help - show this message again"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


def get_rate(base: str, target: str):
    """Fetch the exchange rate from Frankfurter (free, no API key needed)."""
    resp = requests.get(
        FRANKFURTER_URL, params={"from": base, "to": target}, timeout=10
    )
    resp.raise_for_status()
    data = resp.json()
    rate = data.get("rates", {}).get(target)
    return rate, data.get("date")


async def rate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 2:
        await update.message.reply_text(
            "Usage: /rate <FROM> <TO>\nExample: /rate USD EUR"
        )
        return

    base, target = args[0].upper(), args[1].upper()
    try:
        rate, date = get_rate(base, target)
        if rate is None:
            await update.message.reply_text(
                f"Couldn't find a rate for {base} \u2192 {target}. Check the currency codes."
            )
            return
        await update.message.reply_text(
            f"\U0001F4B1 1 {base} = {rate:.4f} {target}\n(as of {date})"
        )
    except requests.RequestException as e:
        logger.error(f"Rate fetch failed: {e}")
        await update.message.reply_text(
            "Sorry, couldn't fetch the exchange rate right now. Try again shortly."
        )


async def convert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 3:
        await update.message.reply_text(
            "Usage: /convert <AMOUNT> <FROM> <TO>\nExample: /convert 100 USD EUR"
        )
        return

    amount_str, base, target = args[0], args[1].upper(), args[2].upper()
    try:
        amount = float(amount_str)
    except ValueError:
        await update.message.reply_text(
            "Amount must be a number, e.g. /convert 100 USD EUR"
        )
        return

    try:
        rate, date = get_rate(base, target)
        if rate is None:
            await update.message.reply_text(
                f"Couldn't find a rate for {base} \u2192 {target}. Check the currency codes."
            )
            return
        converted = amount * rate
        await update.message.reply_text(
            f"\U0001F4B1 {amount:,.2f} {base} = {converted:,.2f} {target}\n"
            f"(rate: 1 {base} = {rate:.4f} {target}, as of {date})"
        )
    except requests.RequestException as e:
        logger.error(f"Convert fetch failed: {e}")
        await update.message.reply_text(
            "Sorry, couldn't fetch the exchange rate right now. Try again shortly."
        )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set.")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("rate", rate_command))
    app.add_handler(CommandHandler("convert", convert_command))

    logger.info("CashFlow bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
