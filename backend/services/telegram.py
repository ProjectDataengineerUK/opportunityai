import logging
import os
import httpx

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


class TelegramNotifier:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    async def notify_top_opportunities(self, opportunities: list) -> None:
        if not self.token or not self.chat_id:
            return

        aplicar = [o for o in opportunities if o.decision == "APLICAR"]
        if not aplicar:
            return

        aplicar.sort(key=lambda o: o.score, reverse=True)
        top = aplicar[:5]

        lines = [f"🚀 *{len(aplicar)} vagas APLICAR* encontradas!\n"]
        for opp in top:
            urgency_icon = {"quente": "🔥", "frio": "❄️", "normal": "⚡"}.get(opp.urgency, "")
            budget = ""
            if opp.budget_min:
                budget = f" · {opp.budget_currency or 'USD'} {opp.budget_min:,.0f}"
            client_tag = " ✅" if opp.client_payment_verified else ""
            bids = f" · {opp.proposals_count} propostas" if opp.proposals_count else ""

            lines.append(
                f"{urgency_icon} *{opp.title}*\n"
                f"Score: {opp.score:.0f} · {opp.area}{budget}{client_tag}{bids}\n"
                f"[Abrir vaga]({opp.url})\n"
            )

        text = "\n".join(lines)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    TELEGRAM_API.format(token=self.token),
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": True,
                    },
                )
        except Exception as exc:
            logger.warning("Telegram notification failed: %s", exc)
