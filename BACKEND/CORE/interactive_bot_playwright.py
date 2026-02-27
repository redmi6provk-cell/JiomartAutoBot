"""
Interactive Telegram Bot for JioMart Automation (Playwright Version)
✅ Multiple products support
✅ Default quantity = 1
✅ Multi-URL ek saath bhejo (comma ya newline se)
"""

import time
import requests
import threading
import traceback
import asyncio
import json
from config import Config
from main_async import run_automation_task

class InteractiveJioMartBot:
    def __init__(self):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.offset = 0
        self.user_sessions = {}
        self.active_tasks = {}

        # States
        self.IDLE           = 'idle'
        self.WAIT_URL       = 'wait_url'
        self.WAIT_QTY       = 'wait_qty'
        self.WAIT_MORE      = 'wait_more'
        self.WAIT_PROFILES  = 'wait_profiles'
        self.WAIT_MODE      = 'wait_mode'
        self.WAIT_COUPON    = 'wait_coupon'
        self.WAIT_AMOUNT   = 'wait_amount'
        self.WAIT_ADDRESS  = 'wait_address'
        self.WAIT_MULTI_QTY = 'wait_multi_qty'  # multiple URLs ke baad bulk qty

    # ── Telegram helpers ──────────────────────────────────────────────
    def get_updates(self, timeout=30):
        try:
            r = requests.get(f"{self.base_url}/getUpdates",
                             params={"timeout": timeout, "offset": self.offset},
                             timeout=timeout + 5)
            return r.json()
        except:
            return {"ok": False, "result": []}

    def send(self, chat_id, text, markup=None):
        try:
            data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
            if markup:
                data["reply_markup"] = json.dumps(markup)
            requests.post(f"{self.base_url}/sendMessage", data=data, timeout=10)
        except Exception as e:
            print(f"Send error: {e}")

    def kb(self, *buttons):
        rows = []
        flat = list(buttons)
        for i in range(0, len(flat), 2):
            rows.append(flat[i:i+2])
        return {"keyboard": rows, "resize_keyboard": True, "one_time_keyboard": True}

    def remove_kb(self):
        return {"remove_keyboard": True}

    # ── Session helpers ───────────────────────────────────────────────
    def session(self, chat_id):
        if chat_id not in self.user_sessions:
            self.user_sessions[chat_id] = {'state': self.IDLE, 'data': {}}
        return self.user_sessions[chat_id]

    def reset(self, chat_id):
        self.user_sessions[chat_id] = {'state': self.IDLE, 'data': {}}

    # ── Flow steps ────────────────────────────────────────────────────

    def ask_url(self, chat_id):
        s = self.session(chat_id)
        s['state'] = self.WAIT_URL
        count = len(s['data'].get('products', [])) + 1
        self.send(chat_id,
            f"📦 *Product {count} ka URL bhejo:*\n\n"
            "💡 *Ek URL:* Normal bhejo\n"
            "💡 *Multiple URLs:* Comma ya newline se alag karo\n"
            "   `url1, url2, url3` (har URL ki qty baad mein poochi jaayegi)",
            self.remove_kb())

    def ask_qty(self, chat_id, product_name):
        s = self.session(chat_id)
        s['state'] = self.WAIT_QTY
        self.send(chat_id,
            f"✅ *{product_name}*\n\n"
            "🔢 *Quantity?* (1-99)\n"
            "💡 Default = 1 (sirf Enter karo)")

    def ask_more(self, chat_id):
        s = self.session(chat_id)
        s['state'] = self.WAIT_MORE
        products = s['data']['products']
        plist = "\n".join(f"  {i+1}. {p['name']} (Qty: {p['qty']})"
                          for i, p in enumerate(products))
        self.send(chat_id,
            f"🛒 *Cart ({len(products)} items):*\n{plist}\n\n"
            "➕ Aur product add karna hai?",
            self.kb("✅ Done", "➕ Add More"))

    def ask_profiles(self, chat_id):
        s = self.session(chat_id)
        s['state'] = self.WAIT_PROFILES
        self.send(chat_id,
            "👥 *Profiles bhejo* (space se alag karo)\n"
            "Example: `1 2 3`",
            self.remove_kb())

    def ask_mode(self, chat_id):
        s = self.session(chat_id)
        s['state'] = self.WAIT_MODE
        profiles = s['data']['profiles']
        self.send(chat_id,
            f"✅ Profiles: {', '.join(profiles)}\n\n"
            "⚡ *Execution Mode?*",
            self.kb("Parallel", "Sequential"))

    def ask_coupon(self, chat_id):
        s = self.session(chat_id)
        s['state'] = self.WAIT_COUPON
        self.send(chat_id,
            "🎟️ *Coupon code bhejo* ya skip karo:",
            self.kb("Skip Coupon"))

    def ask_amount(self, chat_id):
        s = self.session(chat_id)
        s['state'] = self.WAIT_AMOUNT
        coupon = s['data']['coupon']
        self.send(chat_id,
            f"✅ Coupon: {coupon or 'None'}\n\n"
            "💰 *Max amount limit?*\n"
            "Example: `500`",
            self.kb("No Limit"))

    def ask_address(self, chat_id):
        s = self.session(chat_id)
        s['state'] = self.WAIT_ADDRESS
        limit = s['data']['max_amount']
        limit_str = f'₹{int(limit)}' if limit < 100000 else 'None'
        self.send(chat_id,
            f"✅ Limit: {limit_str}\n\n"
            "🏠 *Delivery Address Details?*\n\n"
            "Send in this format (one line):\n"
            "`PIN|HOUSE|FLOOR|TOWER|BUILDING|ROAD|AREA`\n\n"
            "**Example:**\n"
            "`421501|1|1|1|Aswaam Homeopathy|A-2, B Cabin Road|Bhawani Mandir Chowk`\n\n"
            "Or send `default` to use default address.",
            self.kb("Skip Address"))

    def _parse_urls(self, text):
        """Extract URLs from comma/newline-separated input. Returns list of {url, name}."""
        items = []
        lines = [l.strip() for l in text.replace(',', '\n').splitlines() if l.strip()]
        for line in lines:
            url = line.strip()
            if url.startswith('http'):
                name = url.rstrip('/').split('/')[-1].replace('-', ' ').title()[:25]
                items.append({'url': url, 'name': name})
        return items

    def _ask_next_in_queue(self, chat_id):
        """Queue se next URL uthao aur qty poochho."""
        s = self.session(chat_id)
        queue = s['data'].get('_url_queue', [])
        if queue:
            nxt = queue[0]  # peek - pop hoga qty ke baad
            s['data']['_cur_url']  = nxt['url']
            s['data']['_cur_name'] = nxt['name']
            self.ask_qty(chat_id, nxt['name'])
        else:
            self.ask_more(chat_id)

    def launch(self, chat_id):
        s = self.session(chat_id)
        d = s['data']
        products = d['products']
        plist = "\n".join(f"  {i+1}. {p['name']} (Qty: {p['qty']})"
                          for i, p in enumerate(products))
        limit    = d['max_amount']
        address  = d.get('custom_address') or None
        self.send(chat_id,
            f"🚀 *Automation Start!*\n\n"
            f"🛒 *Products ({len(products)}):*\n{plist}\n\n"
            f"👥 *Profiles:* {', '.join(d['profiles'])}\n"
            f"⚡ *Mode:* {d['mode'].capitalize()}\n"
            f"🎟️ *Coupon:* {d['coupon'] or 'None'}\n"
            f"💰 *Limit:* {'₹' + str(int(limit)) if limit < 100000 else 'None'}\n"
            f"📍 *Address:* {address or 'Default'}",
            self.remove_kb())
        threading.Thread(target=self._run_thread, args=(chat_id, dict(d)), daemon=True).start()
        self.reset(chat_id)

    def _run_thread(self, chat_id, data):
        try:
            self.active_tasks[chat_id] = {'start_time': time.time(), 'data': data}
            asyncio.run(run_automation_task(
                profiles=data['profiles'],
                products=data['products'],
                coupon=data['coupon'],
                reorder_count=1,
                mode=data['mode'],
                headless=False,
                monitor_otp=True,
                otp_wait=15,
                max_amount=data['max_amount'],
                auto_clean=True,
                custom_address=data.get('custom_address') or None
            ))
            self.send(chat_id, "✅ *Automation Khatam!*")
        except Exception as e:
            traceback.print_exc()
            self.send(chat_id, f"❌ *Error:*\n`{e}`")
        finally:
            self.active_tasks.pop(chat_id, None)

    # ── Message router ────────────────────────────────────────────────
    def handle(self, chat_id, text):
        text = (text or '').strip()
        s = self.session(chat_id)
        state = s['state']

        # ── Commands (har state mein kaam karte hain) ──
        if text == '/start':
            self.send(chat_id,
                "👋 *JioMart Bot*\n\n"
                "/order - Naya order shuru karo\n"
                "/status - Chal rahe tasks\n"
                "/cancel - Band karo\n"
                "/help - Help")
            return
        if text == '/help':
            self.send(chat_id,
                "📖 *How to use:*\n\n"
                "1️⃣ /order bhejo\n"
                "2️⃣ Product URL bhejo\n"
                "   • *Single URL:* ek URL bhejo\n"
                "   • *Multiple URLs:* comma/newline se alag karo\n"
                "     `url1, url2, url3`\n"
                "     (har URL ki qty alag alag poochi jaayegi)\n"
                "3️⃣ Quantity bhejo *(default = 1, sirf Enter karo)*\n"
                "4️⃣ *Add More* ya *Done* choose karo\n"
                "5️⃣ Profiles (e.g. `1 2 3`)\n"
                "6️⃣ Mode (Parallel/Sequential)\n"
                "7️⃣ Coupon (optional)\n"
                "8️⃣ Max Amount (optional)\n"
                "9️⃣ Address (optional, skip = default)")
            return
        if text == '/cancel':
            self.reset(chat_id)
            self.send(chat_id, "❌ Cancel ho gaya.", self.remove_kb())
            return
        if text == '/order':
            s['data'] = {'products': []}
            self.ask_url(chat_id)
            return
        if text == '/status':
            if not self.active_tasks:
                self.send(chat_id, "ℹ️ Koi task nahi chal raha.")
            else:
                lines = []
                for cid, t in self.active_tasks.items():
                    elapsed = int(time.time() - t['start_time'])
                    ps = t['data'].get('profiles', [])
                    lines.append(f"• {', '.join(ps)} | {elapsed}s")
                self.send(chat_id, "🔄 *Active Tasks:*\n" + "\n".join(lines))
            return

        # ── State Machine ──
        if state == self.WAIT_URL:
            parsed = self._parse_urls(text)
            if len(parsed) > 1:
                # Multiple URLs → queue mein daalo, ek ek qty poochho
                names = ", ".join(p['name'] for p in parsed)
                self.send(chat_id,
                    f"✅ *{len(parsed)} URLs mili:*\n"
                    + "\n".join(f"  {i+1}. {p['name']}" for i, p in enumerate(parsed))
                    + "\n\n🔢 Ab har ek ki qty poochhunga...")
                s['data']['_url_queue'] = parsed
                self._ask_next_in_queue(chat_id)
            elif len(parsed) == 1:
                # Single URL
                s['data']['_cur_url']  = parsed[0]['url']
                s['data']['_cur_name'] = parsed[0]['name']
                self.ask_qty(chat_id, parsed[0]['name'])
            else:
                self.send(chat_id, "❌ Valid JioMart URL bhejo!")

        elif state == self.WAIT_QTY:
            # Default qty = 1 agar empty
            if text in ('', '1', 'default'):
                qty = 1
            else:
                try:
                    qty = int(text)
                    if not 1 <= qty <= 99: raise ValueError()
                except:
                    self.send(chat_id, "❌ 1 se 99 ke beech number bhejo. (Default = 1)")
                    return
            s['data'].setdefault('products', []).append({
                'url':  s['data'].pop('_cur_url'),
                'name': s['data'].pop('_cur_name'),
                'qty':  qty
            })
            # Queue check: aur URLs baaki hain?
            queue = s['data'].get('_url_queue', [])
            if queue:
                queue.pop(0)  # abhi wala done
                self._ask_next_in_queue(chat_id)  # agla
            else:
                self.ask_more(chat_id)

        elif state == self.WAIT_MORE:
            t = text.lower()
            if t in ['✅ done', 'done', 'finish', 'no']:
                self.ask_profiles(chat_id)
            elif t in ['➕ add more', 'add more', 'yes', 'haan']:
                self.ask_url(chat_id)
            else:
                self.send(chat_id, "✅ Done ya ➕ Add More choose karo.",
                          self.kb("✅ Done", "➕ Add More"))

        elif state == self.WAIT_PROFILES:
            try:
                nums = [int(x) for x in text.split()]
                if not nums or len(nums) > 10: raise ValueError()
                s['data']['profiles'] = [f"Profile {n}" for n in nums]
                self.ask_mode(chat_id)
            except:
                self.send(chat_id, "❌ Invalid. Example: `1 2 3`")

        elif state == self.WAIT_MODE:
            mode = text.lower()
            if mode not in ['parallel', 'sequential']:
                self.send(chat_id, "❌ Parallel ya Sequential choose karo.",
                          self.kb("Parallel", "Sequential"))
                return
            s['data']['mode'] = mode
            self.ask_coupon(chat_id)

        elif state == self.WAIT_COUPON:
            coupon = '' if text.lower() in ['skip', 'skip coupon'] else text
            s['data']['coupon'] = coupon
            self.ask_amount(chat_id)

        elif state == self.WAIT_AMOUNT:
            try:
                amt = 100000.0 if text.lower() in ['no limit', 'skip'] else float(text)
                s['data']['max_amount'] = amt
                self.ask_address(chat_id)
            except:
                self.send(chat_id, "❌ Number bhejo ya 'No Limit'", self.kb("No Limit"))

        elif state == self.WAIT_ADDRESS:
            raw = text.strip().upper()
            if raw in ['SKIP', 'SKIP ADDRESS', 'DEFAULT', '']:
                s['data']['custom_address'] = None
                self.launch(chat_id)
            else:
                # Parse pipe format: PIN|HOUSE|FLOOR|TOWER|BUILDING|ROAD|AREA
                parts = text.split('|')
                if len(parts) == 7:
                    s['data']['custom_address'] = {
                        'pin':      parts[0].strip(),
                        'house':    parts[1].strip(),
                        'floor':    parts[2].strip(),
                        'tower':    parts[3].strip(),
                        'building': parts[4].strip(),
                        'road':     parts[5].strip(),
                        'area':     parts[6].strip()
                    }
                    self.launch(chat_id)
                else:
                    self.send(chat_id, 
                        "❌ *Invalid Format!*\n\n"
                        "Send exactly 7 fields separated by `|` (pipe).\n\n"
                        "Format: `PIN|HOUSE|FLOOR|TOWER|BUILDING|ROAD|AREA`",
                        self.kb("Skip Address"))

        else:
            self.send(chat_id, "💡 /order bhejo shuru karne ke liye.")

    # ── Main loop ─────────────────────────────────────────────────────
    def start(self):
        print("🤖 Bot started! Multiple products ✅")
        while True:
            try:
                updates = self.get_updates()
                if not updates.get('ok'):
                    time.sleep(2)
                    continue
                for u in updates['result']:
                    self.offset = u['update_id'] + 1
                    if 'message' in u:
                        msg = u['message']
                        self.handle(msg['chat']['id'], msg.get('text', ''))
                time.sleep(1)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Loop error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    InteractiveJioMartBot().start()
