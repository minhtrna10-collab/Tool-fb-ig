"""
VNDEVCODE MULTI TOOL WEB - BACKEND FULL
Chức năng: Chuyển Page, Reg IG, Reg FB iOS, 10 FB API, Auto Reg Page PR5,
Check Cookie Live/Die, Nuôi Acc, Auto Proxy Manager, Proxy Gen, Token Parser
"""
import os
import json
import re
import time
import uuid
import random
import string
import threading
import base64
import urllib.parse
from datetime import datetime
import requests
from flask import Flask, request, jsonify, Response, stream_with_context

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

SESSION_LOGS = {}
SESSION_STATUS = {}
FARM_RESULTS = {}

# ═══════════════════════════════════════════════════════════
# PROXY MANAGER
# ═══════════════════════════════════════════════════════════
GLOBAL_PROXY_LIST = []
GLOBAL_PROXY_INDEX = 0
GLOBAL_PROXY_LOCK = threading.Lock()

def log_to_session(sid, msg):
    if sid not in SESSION_LOGS:
        SESSION_LOGS[sid] = []
    SESSION_LOGS[sid].append({
        'time': datetime.now().strftime('%H:%M:%S'),
        'msg': str(msg)
    })
    if len(SESSION_LOGS[sid]) > 1000:
        SESSION_LOGS[sid] = SESSION_LOGS[sid][-1000:]

def get_next_proxy():
    global GLOBAL_PROXY_INDEX
    with GLOBAL_PROXY_LOCK:
        if not GLOBAL_PROXY_LIST:
            return None
        proxy = GLOBAL_PROXY_LIST[GLOBAL_PROXY_INDEX % len(GLOBAL_PROXY_LIST)]
        GLOBAL_PROXY_INDEX += 1
        return proxy

def format_proxy_for_requests(proxy_str):
    if not proxy_str:
        return None
    p = proxy_str.strip()
    if not p:
        return None
    scheme = 'http'
    if p.startswith('socks5://'):
        scheme = 'socks5'
        p = p[len('socks5://'):]
    elif p.startswith('http://'):
        p = p[len('http://'):]
    elif p.startswith('https://'):
        p = p[len('https://'):]
    if '@' in p:
        url = f'{scheme}://{p}'
        return {'http': url, 'https': url}
    parts = p.split(':')
    if len(parts) == 2:
        url = f'{scheme}://{parts[0]}:{parts[1]}'
        return {'http': url, 'https': url}
    elif len(parts) == 4:
        if parts[1].isdigit() and not parts[3].isdigit():
            ip, port, user, pwd = parts
        else:
            user, pwd, ip, port = parts
        url = f'{scheme}://{user}:{pwd}@{ip}:{port}'
        return {'http': url, 'https': url}
    return {'http': f'{scheme}://{p}', 'https': f'{scheme}://{p}'}

def test_proxy(proxy_str, timeout=8):
    proxies = format_proxy_for_requests(proxy_str)
    if not proxies:
        return False
    try:
        r = requests.get('https://api.ipify.org?format=json',
                         proxies=proxies, timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False

# ═══════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════
FB4A_UA = '[FBAN/FB4A;FBAV/542.0.0.46.151;FBBV/840338789;FBDM/{density=0.75,width=300,height=540};FBLC/vi_VN;FBRV/0;FBCR/MobiFone;FBMF/MTool-Max;FBBD/MTool-Max;FBPN/com.facebook.katana;FBDV/MTool-Max;FBSV/9;FBOP/1;FBCA/x86_64:arm64-v8a;]'
FB_UA_552 = '[FBAN/FB4A;FBAV/552.1.0.45.68;FBBV/906187048;FBDM/{density=3.0,width=1080,height=1920};FBLC/en_US;FBRV/0;FBCR/MobiFone;FBMF/Samsung;FBBD/Samsung;FBPN/com.facebook.katana;FBDV/Samsung C3560;FBSV/9;FBOP/1;FBCA/x86_64:arm64-v8a;]'

REACTION_IDS = {
    'LIKE': '1635855486666999', 'LOVE': '1678524932434102',
    'HAHA': '115940658764963', 'WOW': '478547315650144',
    'SAD': '908563459236466', 'ANGRY': '444813342392137'
}

BLOKS_VERSION_PR5 = "338f8ead5977a2c41eba3e92584dcf1d132e8b7928f1f5796662ec064023047d"
APP_ID_PAGE_CREATE = "com.bloks.www.additional.profile.plus.creation.action.category.submit"
APP_ID_PROFILE_PLUS = "com.bloks.www.bloks.caa.profile_plus.creation.async"
GRAPHQL_DOC_PAGE_CREATE = "119940804239956818821550724"
GRAPHQL_DOC_PROFILE_PLUS = "11994080423986492941384902285"

PAGE_CATEGORIES = {
    "Cá nhân": "180164648685982",
    "Công ty": "180164648685982",
    "Cửa hàng": "180164648685982",
    "Nhà hàng": "180164648685982",
    "Thương hiệu": "180164648685982",
    "Blog": "180164648685982",
    "Giải trí": "180164648685982",
}

class VNNameGenerator:
    VN_HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Võ",
             "Vũ", "Bùi", "Đặng", "Đỗ", "Hồ", "Dương", "Đoàn",
             "Trịnh", "Tạ", "Đào", "Lý"]
    VN_LOT = ["Văn", "Thị", "Hữu", "Đình", "Ngọc", "Xuân", "Gia",
              "Minh", "Quang", "Đức", "Công", "Thành", "Tuấn",
              "Hoàng", "Kim", "Bảo"]
    VN_TEN = ["Anh", "Hùng", "Nam", "Tuấn", "Hoàng", "Quốc", "Giang",
              "Khương", "Dương", "Phúc", "Thiện", "Kiệt", "Châu",
              "Huệ", "Khánh", "Yến", "Linh", "Thảo", "My", "Huy",
              "Trang", "Huyền", "Ngân"]

    @staticmethod
    def gen():
        return (f"{random.choice(VNNameGenerator.VN_HO)} "
                f"{random.choice(VNNameGenerator.VN_LOT)} "
                f"{random.choice(VNNameGenerator.VN_TEN)}")


# ═══════════════════════════════════════════════════════════
# MODULE: CHUYỂN PAGE
# ═══════════════════════════════════════════════════════════
class ChuyenPageTool:
    def __init__(self, use_proxy=False):
        self.log_callback = None
        self.use_proxy = use_proxy
        self.proxy = get_next_proxy() if use_proxy else None

    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    def _req(self, method, url, **kwargs):
        if self.use_proxy and self.proxy:
            kwargs['proxies'] = format_proxy_for_requests(self.proxy)
        return requests.request(method, url, **kwargs)

    def get_user_info(self, access_token):
        try:
            r = self._req('GET', "https://graph.facebook.com/me",
                          params={"access_token": access_token,
                                  "fields": "id,name"}, timeout=10)
            d = r.json()
            return (d["id"], d.get("name", "")) if "id" in d else (None, None)
        except Exception:
            return None, None

    def _fb_fetch_profile_info(self, token, profile_id):
        v = {'profile_switcher_connection_first': 300,
             'additional_profile_picture_size': 80,
             'profileID': str(profile_id),
             'main_profile_picture_size': 80, 'scale': '2',
             'nt_context': {'using_white_navbar': True,
                            'styles_id': '588d028b36bed0e1889e09b60e0f9aea',
                            'pixel_ratio': 2, 'is_push_on': True,
                            'debug_tooling_metadata_token': None,
                            'is_flipper_enabled': False,
                            'theme_params': [{'value': [],
                                              'design_system_name': 'FDS'}],
                            'bloks_version': BLOKS_VERSION_PR5},
             'overflow_recent_searches_filter_ids': [],
             'use_native_entrypoint_for_stars_on_reels': True}
        p = {'method': 'post', 'pretty': 'false', 'format': 'json',
             'server_timestamps': 'true', 'locale': 'vi_VN',
             'client_doc_id': '116912609015732060545213902280',
             'variables': json.dumps(v)}
        h = {'User-Agent': FB4A_UA, 'Accept-Encoding': 'gzip',
             'authorization': f'OAuth {token}'}
        try:
            return self._req('POST', 'https://b-graph.facebook.com/graphql',
                             data=p, headers=h, timeout=15).json()
        except Exception:
            return None

    def _get_ps_map(self, token, uid):
        gql = self._fb_fetch_profile_info(token, uid)
        if not gql:
            return []
        res = []
        try:
            edges = gql.get('data', {}).get('user', {}).get(
                'profile_switcher_eligible_profiles', {}).get('edges', [])
            for e in edges:
                n = e.get('node', {})
                pr = n.get('profile', {})
                tk = n.get('session_info', {}).get('access_token', '')
                pid = str(pr.get('id', ''))
                if pid and pid != str(uid) and tk:
                    res.append({'profile_id': pid,
                                'name': pr.get('name', ''),
                                'access_token': tk})
        except Exception:
            pass
        return res

    def _match(self, page, ps_map):
        pid = str(page.get('id', ''))
        pname = page.get('name', '').strip().lower()
        for p in ps_map:
            if p['name'].strip().lower() == pname or p['profile_id'] == pid:
                return p['profile_id'], p.get('access_token', '')
        return None, None

    def get_pages(self, token, uid=None):
        try:
            r = self._req('GET', "https://graph.facebook.com/me/accounts",
                          params={"access_token": token,
                                  "fields": "id,name,access_token,category"},
                          timeout=15)
            d = r.json()
            if "data" not in d:
                return []
            ps = self._get_ps_map(token, uid) if uid else []
            pages = []
            for pg in d["data"]:
                if pg.get("id") and pg.get("access_token"):
                    pu, ptk = self._match(pg, ps)
                    pages.append({'uid': pu or pg["id"],
                                  'token': ptk or pg["access_token"],
                                  'name': pg.get("name", ""),
                                  'id': pg["id"],
                                  'category': pg.get("category", "")})
            return pages
        except Exception:
            return []

    def _hdrs(self, token):
        return {"User-Agent": FB4A_UA, "authorization": f"OAuth {token}",
                "x-fb-sim-hni": "45201", "x-fb-net-hni": "45201",
                "x-graphql-client-library": "graphservice",
                "x-tigon-is-retry": "False",
                "x-graphql-request-purpose": "fetch",
                "x-fb-device-group": "2789", "Accept-Encoding": "identity",
                "x-zero-eh": "error", "x-fb-connection-type": "WIFI",
                "x-fb-http-engine": "Tigon/Liger",
                "x-fb-client-ip": "True", "x-fb-server-cluster": "True",
                "Content-Type": "application/x-www-form-urlencoded"}

    def _send_inv(self, stk, spwd, puid, tuid):
        self.log(f"📤 Gửi lời mời page {puid} → {tuid}")
        url = (f"/nt/profile/admin_management/permissions_reauth?admin_id={tuid}"
               "&admin_rows_container_id=%5B%228bxxoh%3A2%22%2Cnull%5D&admin_type=full_access"
               "&entry_point_screen_id=%5B%227o2xil%3A5%22%2Cnull%5D"
               f"&profile_id={puid}"
               "&state_ids%5Bauthenticated%5D=8csr9g%3A0"
               "&state_ids%5Bauthentication_attempted%5D=8csr9g%3A1"
               "&state_ids%5Bshow_entry_point_saving_spinner%5D=8bxxoh%3A0"
               "&state_ids%5Bshow_saving_spinner%5D=8csr9g%3A3"
               "&state_ids%5Bads%5D=8clnk7%3A2&state_ids%5Bcontent%5D=8clnk7%3A3"
               "&state_ids%5Binsights%5D=8clnk7%3A4&state_ids%5Bmessages%5D=8clnk7%3A5"
               "&state_ids%5Bmoderate%5D=8clnk7%3A6")
        cd = {"sensitive_string_value": f'[["password","{spwd}"]]'}
        ntc = {"using_white_navbar": True,
               "styles_id": "55d2af294359fa6bbdb8e045ff01fc5e",
               "pixel_ratio": 1.5, "is_push_on": True,
               "debug_tooling_metadata_token": None,
               "is_flipper_enabled": False, "theme_params": [],
               "bloks_version": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c"}
        po = {"nt_context": ntc, "payload": url, "client_data": cd}
        v = {"params": json.dumps(po),
             "bloks_versioning_id": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c",
             "app_id": "com.bloks.www.bloks.caa.admin_management.permissions_reauth",
             "scale": 1, "nt_context": ntc}
        d = {"method": "post", "pretty": "false", "format": "json",
             "server_timestamps": "true", "locale": "vi_VN", "purpose": "fetch",
             "fb_api_req_friendly_name": "FbBloksActionRootQuery-com.bloks.www.bloks.caa.admin_management.permissions_reauth",
             "fb_api_caller_class": "graphservice",
             "client_doc_id": "30749539927629244093798192451",
             "variables": json.dumps(v),
             "fb_api_analytics_tags": '["GraphServices"]',
             "client_trace_id": str(uuid.uuid4())}
        try:
            return self._req('POST', "https://b-graph.facebook.com/graphql",
                             headers=self._hdrs(stk), data=d, timeout=30).json()
        except Exception as e:
            return {"error": str(e)}

    def _accept_inv(self, ttk, inv_id):
        self.log(f"✅ Chấp nhận lời mời (ID: {inv_id})")
        url = f"/nt/profile/admin_management/accept_invitation?invitation_id={inv_id}"
        ntc = {"using_white_navbar": True,
               "styles_id": "55d2af294359fa6bbdb8e045ff01fc5e",
               "pixel_ratio": 1.5, "is_push_on": True,
               "debug_tooling_metadata_token": None,
               "is_flipper_enabled": False, "theme_params": [],
               "bloks_version": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c"}
        po = {"nt_context": ntc, "payload": url}
        v = {"params": json.dumps(po),
             "bloks_versioning_id": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c",
             "app_id": "com.bloks.www.bloks.caa.admin_management.accept_invitation",
             "scale": 1, "nt_context": ntc}
        d = {"method": "post", "pretty": "false", "format": "json",
             "server_timestamps": "true", "locale": "vi_VN", "purpose": "fetch",
             "fb_api_req_friendly_name": "FbBloksActionRootQuery-com.bloks.www.bloks.caa.admin_management.accept_invitation",
             "fb_api_caller_class": "graphservice",
             "client_doc_id": "11994080423986492941384902285",
             "variables": json.dumps(v),
             "fb_api_analytics_tags": '["GraphServices"]',
             "client_trace_id": str(uuid.uuid4())}
        try:
            return self._req('POST', "https://b-graph.facebook.com/graphql",
                             headers=self._hdrs(ttk), data=d, timeout=30).json()
        except Exception as e:
            return {"error": str(e)}

    def _extract_inv_id(self, r):
        t = json.dumps(r)
        for p in [r'"invitation_id":"([^"]+)"',
                  r'"id":"([^"]+)"',
                  r'"confirmation_code":"([^"]+)"']:
            m = re.search(p, t)
            if m:
                return m.group(1)
        return None

    def transfer(self, stk, spwd, puid, ttk):
        tuid, _ = self.get_user_info(ttk)
        if not tuid:
            return False, "Không lấy được UID đích"
        r1 = self._send_inv(stk, spwd, puid, tuid)
        if "error" in r1:
            return False, f"Lỗi gửi: {r1['error']}"
        if r1.get("errors"):
            return False, f"Lỗi server: {r1['errors']}"
        inv = self._extract_inv_id(r1)
        if not inv:
            return False, "Không tìm thấy invitation_id"
        r2 = self._accept_inv(ttk, inv)
        if "error" in r2:
            return False, f"Lỗi accept: {r2['error']}"
        if r2.get("errors"):
            return False, f"Lỗi accept server: {r2['errors']}"
        return True, "OK"


# ═══════════════════════════════════════════════════════════
# TEMP EMAIL
# ═══════════════════════════════════════════════════════════
class TempEmailGenerator:
    def __init__(self, use_proxy=False):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        })
        self.use_proxy = use_proxy
        self.proxy = get_next_proxy() if use_proxy else None
        self.email_tokens = {}
        self.generated_usernames = set()

    def _req(self, method, url, **kwargs):
        if self.use_proxy and self.proxy:
            kwargs['proxies'] = format_proxy_for_requests(self.proxy)
        return requests.request(method, url, **kwargs)

    def _gen_username(self):
        ho = ['nguyen', 'tran', 'le', 'pham', 'hoang', 'huynh', 'phan', 'vu',
              'vo', 'dang', 'bui', 'do', 'ho', 'ngo', 'duong', 'ly']
        td = ['thi', 'van', 'duc', 'minh', 'quoc', 'thanh', 'ngoc', 'bao',
              'gia', 'khanh']
        t = ['an', 'binh', 'chi', 'duong', 'giang', 'han', 'khang', 'lam',
             'long', 'my', 'nhi', 'phong', 'quan', 'son', 'trang', 'uyen',
             'vy', 'yen']
        fmt = random.choice([1, 2, 3])
        if fmt == 1:
            u = f"{random.choice(ho)}{random.choice(td)}{random.choice(t)}"
        elif fmt == 2:
            u = f"{random.choice(ho)}{random.choice(t)}{random.choice(t)}"
        else:
            u = f"{random.choice(t)}{random.choice(td)}{random.choice(ho)}"
        u += str(random.randint(10, 999))
        if u in self.generated_usernames:
            u += str(random.randint(1000, 9999))
        self.generated_usernames.add(u)
        return u

    def _get_domains(self):
        try:
            r = self._req('GET', 'https://api.mail.tm/domains', timeout=8)
            if r.status_code == 200:
                d = r.json()
                if 'hydra:member' in d:
                    doms = [x['domain'] for x in d['hydra:member']
                            if x.get('isActive')]
                    if doms:
                        return doms
        except Exception:
            pass
        return ['agristur.com', 'febbox.com', 'main.truf.biz']

    def _get_token(self, email, pwd):
        if email in self.email_tokens:
            return self.email_tokens[email]
        try:
            r = self._req('POST', 'https://api.mail.tm/token',
                          json={'address': email, 'password': pwd}, timeout=10)
            if r.status_code == 200:
                tk = r.json().get('token')
                self.email_tokens[email] = tk
                return tk
        except Exception:
            pass
        return None

    def create_email(self):
        for _ in range(3):
            try:
                doms = self._get_domains()
                if not doms:
                    return None
                u = self._gen_username()
                dom = random.choice(doms)
                pwd = ''.join(random.choice(string.ascii_letters + string.digits)
                              for _ in range(12))
                r = self._req('POST', 'https://api.mail.tm/accounts',
                              json={'address': f'{u}@{dom}',
                                    'password': pwd}, timeout=12)
                if r.status_code == 201:
                    addr = f'{u}@{dom}'
                    tk = self._get_token(addr, pwd)
                    return {'email': addr, 'password': pwd,
                            'service': 'mailtm', 'token': tk}
            except Exception:
                pass
            time.sleep(2)
        return None

    def get_messages(self, email_info):
        try:
            tk = email_info.get('token') or self._get_token(
                email_info['email'], email_info['password'])
            if not tk:
                return []
            r = self._req('GET', 'https://api.mail.tm/messages',
                          headers={'Authorization': f'Bearer {tk}'},
                          timeout=10)
            if r.status_code == 200:
                d = r.json()
                msgs = d.get('hydra:member', []) if 'hydra:member' in d else []
                msgs.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
                for m in msgs[:3]:
                    try:
                        cr = self._req('GET',
                                       f"https://api.mail.tm/messages/{m['id']}",
                                       headers={'Authorization': f'Bearer {tk}'},
                                       timeout=8)
                        if cr.status_code == 200:
                            j = cr.json()
                            m['full_content'] = j.get('text', '') or j.get('html', '')
                    except Exception:
                        pass
                return msgs
        except Exception:
            pass
        return []


# ═══════════════════════════════════════════════════════════
# INSTAGRAM REG
# ═══════════════════════════════════════════════════════════
class InstagramReg:
    def __init__(self, use_proxy=False):
        self.log_callback = None
        self.is_stopped = lambda: False
        self.use_proxy = use_proxy
        self.proxy = get_next_proxy() if use_proxy else None
        self.email_gen = TempEmailGenerator(use_proxy=use_proxy)
        self.displayed_msgs = set()

    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    def _ua(self):
        devs = ["iPhone15,2", "iPhone14,7", "iPhone13,2", "iPhone12,1",
                "iPhone11,2"]
        ios = ["17_2", "16_4", "15_5", "17_0"]
        return (f'Mozilla/5.0 ({random.choice(devs)}; CPU iPhone OS '
                f'{random.choice(ios)} like Mac OS X) AppleWebKit/605.1.15 '
                f'(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/605.1')

    def _session(self):
        s = requests.Session()
        s.headers.update({
            'accept': '*/*',
            'accept-language': 'vi-VN,vi;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.instagram.com',
            'referer': 'https://www.instagram.com/accounts/emailsignup/',
            'user-agent': self._ua()
        })
        if self.use_proxy and self.proxy:
            s.proxies.update(format_proxy_for_requests(self.proxy))
        return s

    def _init_cookies(self, s):
        try:
            s.get('https://www.instagram.com/', timeout=30)
            time.sleep(random.uniform(2, 4))
            r = s.get('https://www.instagram.com/accounts/emailsignup/',
                      timeout=30)
            if r.status_code == 200:
                csrf = s.cookies.get('csrftoken') or ''.join(
                    random.choice(string.ascii_letters + string.digits)
                    for _ in range(32))
                s.headers['x-csrftoken'] = csrf
                return csrf
        except Exception:
            pass
        return None

    def _gen_name(self):
        ho = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Vũ', 'Đặng',
              'Bùi', 'Đỗ', 'Ngô']
        td = ['Thị', 'Văn', 'Đức', 'Minh', 'Quốc', 'Thanh', 'Ngọc',
              'Bảo', 'Gia']
        t = ['An', 'Bình', 'Chi', 'Dương', 'Giang', 'Hân', 'Khang',
             'Lam', 'Long', 'My', 'Nhi', 'Phong', 'Quân', 'Sơn', 'Trang']
        return f"{random.choice(ho)} {random.choice(td)} {random.choice(t)}"

    def _gen_ig_username(self, name):
        u = re.sub(r'[^a-zA-Z0-9]', '', name.lower())
        return u + str(random.randint(100, 9999))

    def create_account(self, pwd):
        s = self._session()
        csrf = self._init_cookies(s)
        if not csrf:
            self.log("❌ Không init được session")
            return False

        email_info = self.email_gen.create_email()
        if not email_info:
            self.log("❌ Không tạo được email")
            return False
        email = email_info['email']
        self.log(f"📧 Email: {email}")

        first_name = self._gen_name()
        username = self._gen_ig_username(first_name)
        client_id = ''.join(random.choice(string.ascii_lowercase + string.digits)
                            for _ in range(20))
        jazoest = ''.join(random.choice(string.digits) for _ in range(5))

        enc_pwd = f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{pwd}"
        data1 = {'enc_password': enc_pwd, 'email': email,
                 'username': username, 'first_name': first_name,
                 'client_id': client_id, 'seamless_login_enabled': '1',
                 'opt_into_one_tap': 'false', 'jazoest': jazoest}
        try:
            r1 = s.post('https://www.instagram.com/api/v1/web/accounts/web_create_ajax/attempt/',
                        data=data1, timeout=45)
            self.log(f"• Signup step 1: HTTP {r1.status_code}")
            if r1.status_code != 200:
                return False
        except Exception as e:
            self.log(f"❌ Lỗi step1: {e}")
            return False

        try:
            s.post('https://www.instagram.com/api/v1/web/consent/check_age_eligibility/',
                   data={'day': str(random.randint(1, 28)),
                         'month': str(random.randint(1, 12)),
                         'year': str(random.randint(1990, 2000)),
                         'jazoest': jazoest}, timeout=30)
        except Exception:
            pass

        try:
            s.post('https://www.instagram.com/api/v1/accounts/send_verify_email/',
                   data={'device_id': client_id, 'email': email,
                         'jazoest': jazoest}, timeout=30)
            self.log("• Đã gửi code verify")
        except Exception:
            pass

        code = None
        for i in range(60):
            if self.is_stopped():
                return False
            msgs = self.email_gen.get_messages(email_info)
            for m in msgs:
                mid = m.get('id', '')
                key = f"{email}_{mid}"
                if key in self.displayed_msgs:
                    continue
                self.displayed_msgs.add(key)
                content = (m.get('full_content', '') + ' ' +
                           m.get('subject', ''))
                codes = re.findall(r'\b\d{6}\b', content)
                if codes:
                    code = codes[0]
                    self.log(f"✅ Code: {code}")
                    break
            if code:
                break
            time.sleep(2)

        if not code:
            self.log("❌ Không lấy được code")
            return False

        data2 = {'enc_password': enc_pwd,
                 'day': str(random.randint(1, 28)),
                 'email': email, 'failed_birthday_year_count': '{}',
                 'first_name': first_name,
                 'month': str(random.randint(1, 12)),
                 'username': username,
                 'year': str(random.randint(1990, 2000)),
                 'client_id': client_id, 'seamless_login_enabled': '1',
                 'tos_version': 'row', 'force_sign_up_code': code,
                 'jazoest': jazoest}
        try:
            r2 = s.post('https://www.instagram.com/api/v1/web/accounts/web_create_ajax/',
                        data=data2, timeout=30)
            res = r2.json()
            if res.get('account_created') or res.get('user_id'):
                self.log(f"✅ TẠO THÀNH CÔNG: {username}")
                cookies = s.cookies.get_dict()
                important = {k: cookies[k] for k in
                             ['csrftoken', 'sessionid', 'ds_user_id',
                              'ig_did', 'mid', 'datr'] if k in cookies}
                ck_str = '; '.join(f'{k}={v}' for k, v in important.items())
                with open('account_instagram.txt', 'a', encoding='utf-8') as f:
                    f.write(f"||{first_name} | {username} | {pwd} | {email}||\n")
                    f.write(f"||{ck_str}||\n")
                return True
            else:
                self.log(f"❌ Lỗi: {res}")
                return False
        except Exception as e:
            self.log(f"❌ Lỗi hoàn tất: {e}")
            return False


# ═══════════════════════════════════════════════════════════
# FACEBOOK iOS REG
# ═══════════════════════════════════════════════════════════
class FacebookIOSReg:
    def __init__(self, use_proxy=False):
        self.log_callback = None
        self.is_stopped = lambda: False
        self.use_proxy = use_proxy

    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    def register(self, password='anhem1234'):
        self.log("🚀 Bắt đầu đăng ký Facebook iOS")
        email_gen = TempEmailGenerator(use_proxy=self.use_proxy)
        email_info = email_gen.create_email()
        if not email_info:
            self.log("❌ Không tạo được email")
            return False, None
        email = email_info['email']
        self.log(f"📧 Email: {email}")

        ho = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Vũ']
        ten = ['An', 'Bình', 'Chi', 'Dương', 'Giang', 'Hân']
        last_name = random.choice(ho)
        first_name = random.choice(ten)
        full_name = f"{last_name} {first_name}"
        self.log(f"👤 Tên: {full_name}")

        code = None
        self.log("⏳ Đợi OTP...")
        for i in range(60):
            if self.is_stopped():
                return False, None
            msgs = email_gen.get_messages(email_info)
            for m in msgs:
                content = (m.get('full_content', '') + ' ' +
                           m.get('subject', ''))
                codes = re.findall(r'\b\d{5,6}\b', content)
                if codes:
                    code = codes[0]
                    self.log(f"✅ OTP: {code}")
                    break
            if code:
                break
            time.sleep(2)

        if not code:
            self.log("❌ Không lấy được OTP")
            return False, None

        with open('account_facebook.txt', 'a', encoding='utf-8') as f:
            f.write(f"{email}|{password}|{full_name}|{code}\n")

        self.log("⚠️ FB iOS Reg cần IP sạch + device thật")
        return True, {'email': email, 'password': password,
                      'name': full_name, 'code': code}


# ═══════════════════════════════════════════════════════════
# COOKIE LOGIN CHECKER
# ═══════════════════════════════════════════════════════════
class CookieLoginChecker:
    def __init__(self, platform='facebook', use_proxy=False):
        self.platform = platform.lower()
        self.session = requests.Session()
        self.use_proxy = use_proxy
        self.proxy = get_next_proxy() if use_proxy else None

    def parse_cookie_string(self, cookie_str):
        cookies = {}
        for item in cookie_str.split(';'):
            item = item.strip()
            if '=' in item:
                k, v = item.split('=', 1)
                cookies[k.strip()] = v.strip()
        return cookies

    def _req(self, method, url, **kwargs):
        if self.use_proxy and self.proxy:
            kwargs['proxies'] = format_proxy_for_requests(self.proxy)
        return requests.request(method, url, **kwargs)

    def login_facebook(self, cookie_str):
        cookies = self.parse_cookie_string(cookie_str)
        if 'c_user' not in cookies:
            return {'ok': False, 'error': 'Cookie thiếu c_user'}
        uid = cookies.get('c_user', '')
        for k, v in cookies.items():
            self.session.cookies.set(k, v, domain='.facebook.com')
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
        }
        try:
            r = self._req('GET', 'https://mbasic.facebook.com/profile.php',
                          headers=headers, cookies=self.session.cookies,
                          timeout=20, allow_redirects=True)
            html = r.text
            url_lower = r.url.lower()
            if 'checkpoint' in url_lower:
                return {'ok': False, 'error': 'Bị checkpoint',
                        'uid': uid, 'status': 'DIE'}
            if 'login' in url_lower and 'profile' not in url_lower:
                return {'ok': False, 'error': 'Cookie hết hạn',
                        'uid': uid, 'status': 'DIE'}
            name = uid
            m = re.search(r'<title>([^<]+)</title>', html)
            if m:
                name = m.group(1).replace(' | Facebook', '').strip()
            avatar = ''
            av_match = re.search(
                r'<img[^>]+src="(https://[^"]+scontent[^"]+)"', html)
            if av_match:
                avatar = av_match.group(1).replace('&amp;', '&')
            return {'ok': True, 'uid': uid, 'name': name,
                    'avatar': avatar, 'status': 'LIVE',
                    'platform': 'facebook'}
        except Exception as e:
            return {'ok': False, 'error': str(e),
                    'uid': uid, 'status': 'ERROR'}

    def login_instagram(self, cookie_str):
        cookies = self.parse_cookie_string(cookie_str)
        if 'sessionid' not in cookies:
            return {'ok': False, 'error': 'Cookie thiếu sessionid'}
        uid = cookies.get('ds_user_id', '')
        for k, v in cookies.items():
            self.session.cookies.set(k, v, domain='.instagram.com')
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) '
                          'AppleWebKit/605.1.15 (KHTML, like Gecko) '
                          'Version/17.0 Mobile/15E148 Safari/604.1',
            'Accept': '*/*',
            'Accept-Language': 'vi-VN,vi;q=0.9',
            'X-IG-App-ID': '936619743392459',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.instagram.com/',
        }
        try:
            r = self._req('GET',
                          'https://www.instagram.com/api/v1/users/web_profile_info/',
                          headers=headers, cookies=self.session.cookies,
                          timeout=20)
            if r.status_code == 200:
                try:
                    data = r.json()
                    user = data.get('data', {}).get('user', {})
                    if user.get('id'):
                        return {
                            'ok': True, 'uid': user.get('id'),
                            'username': user.get('username', ''),
                            'name': user.get('full_name', ''),
                            'avatar': user.get('profile_pic_url_hd', ''),
                            'status': 'LIVE', 'platform': 'instagram'}
                except Exception:
                    pass
            r2 = self._req('GET', 'https://www.instagram.com/accounts/edit/',
                           headers=headers, cookies=self.session.cookies,
                           timeout=15, allow_redirects=True)
            if 'accounts/login' in r2.url.lower():
                return {'ok': False, 'error': 'Cookie hết hạn',
                        'uid': uid, 'status': 'DIE'}
            return {'ok': True, 'uid': uid, 'status': 'LIVE',
                    'platform': 'instagram', 'name': uid}
        except Exception as e:
            return {'ok': False, 'error': str(e),
                    'uid': uid, 'status': 'ERROR'}


# ═══════════════════════════════════════════════════════════
# NUÔI TÀI KHOẢN
# ═══════════════════════════════════════════════════════════
class AccountFarmer:
    FB_TARGETS = ['4', '5', '6', '8', '9', '10', '11', '12']
    IG_TARGETS = ['instagram', 'cristiano', 'leomessi', 'selenagomez',
                  'kyliejenner', 'therock', 'natgeo', 'nasa']
    BIOS = [
        "Sống để học hỏi và sẻ chia.",
        "Photography is my passion 📸",
        "Loving life in Vietnam 🇻🇳",
        "Đơn giản là tôi.",
        "Keep it real 💯",
        "Traveler | Foodie | Dreamer",
        "Work hard, play hard.",
        "Always be yourself.",
    ]

    def __init__(self, platform='facebook', use_proxy=False):
        self.platform = platform.lower()
        self.session = requests.Session()
        self.log_callback = None
        self.is_stopped = lambda: False
        self.use_proxy = use_proxy
        self.proxy = get_next_proxy() if use_proxy else None
        if self.use_proxy and self.proxy:
            self.session.proxies.update(format_proxy_for_requests(self.proxy))

    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    def load_cookies(self, cookie_str):
        cookies = {}
        for item in cookie_str.split(';'):
            item = item.strip()
            if '=' in item:
                k, v = item.split('=', 1)
                cookies[k.strip()] = v.strip()
        for k, v in cookies.items():
            domain = '.facebook.com' if self.platform == 'facebook' else '.instagram.com'
            self.session.cookies.set(k, v, domain=domain)
        return cookies

    def _headers_fb(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Referer': 'https://www.facebook.com/',
        }

    def _headers_ig(self):
        return {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) '
                          'AppleWebKit/605.1.15 (KHTML, like Gecko) '
                          'Version/17.0 Mobile/15E148 Safari/604.1',
            'Accept': '*/*',
            'Accept-Language': 'vi-VN,vi;q=0.9',
            'X-IG-App-ID': '936619743392459',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.instagram.com/',
        }

    def _sleep(self, min_s, max_s):
        t = random.uniform(min_s, max_s)
        end = time.time() + t
        while time.time() < end:
            if self.is_stopped():
                raise Exception('stopped')
            time.sleep(0.5)

    def fb_view_feed(self):
        self.log("📰 Xem feed...")
        try:
            self.session.get('https://mbasic.facebook.com/home.php',
                             headers=self._headers_fb(), timeout=20)
            self._sleep(3, 6)
            return True
        except Exception as e:
            self.log(f"❌ {e}")
            return False

    def fb_like_random(self):
        self.log("❤️ Like bài viết...")
        try:
            r = self.session.get('https://mbasic.facebook.com/home.php',
                                 headers=self._headers_fb(), timeout=20)
            likes = re.findall(r'href="(/a/like\.php[^"]+)"', r.text)
            if not likes:
                return False
            for u in random.sample(likes, min(3, len(likes))):
                full = f'https://mbasic.facebook.com{u.replace("&amp;", "&")}'
                self.session.get(full, headers=self._headers_fb(), timeout=15)
                self._sleep(4, 10)
            return True
        except Exception as e:
            self.log(f"❌ {e}")
            return False

    def fb_view_profile(self, uid):
        self.log(f"👤 Xem profile {uid}...")
        try:
            self.session.get(f'https://mbasic.facebook.com/profile.php?id={uid}',
                             headers=self._headers_fb(), timeout=20)
            self._sleep(3, 8)
            return True
        except Exception as e:
            self.log(f"❌ {e}")
            return False

    def fb_update_bio(self):
        self.log("📝 Đổi bio...")
        try:
            self.session.get('https://mbasic.facebook.com/profile/edit/info',
                             headers=self._headers_fb(), timeout=20)
            self._sleep(2, 4)
            return True
        except Exception as e:
            self.log(f"❌ {e}")
            return False

    def ig_view_feed(self):
        self.log("📰 Lướt IG feed...")
        try:
            self.session.get('https://www.instagram.com/',
                             headers=self._headers_ig(), timeout=20)
            self._sleep(4, 8)
            return True
        except Exception as e:
            self.log(f"❌ {e}")
            return False

    def ig_view_story(self, username):
        self.log(f"📱 Xem story @{username}...")
        try:
            r = self.session.get(
                'https://www.instagram.com/api/v1/users/web_profile_info/',
                params={'username': username},
                headers=self._headers_ig(), timeout=15)
            uid = r.json().get('data', {}).get('user', {}).get('id')
            if not uid:
                return False
            self.session.get(
                f'https://www.instagram.com/api/v1/feed/reels_media/?reel_ids={uid}',
                headers=self._headers_ig(), timeout=15)
            self._sleep(3, 6)
            return True
        except Exception as e:
            self.log(f"❌ {e}")
            return False

    def ig_like_user_posts(self, username, num=3):
        self.log(f"❤️ Like {num} bài @{username}...")
        try:
            r = self.session.get(
                'https://www.instagram.com/api/v1/users/web_profile_info/',
                params={'username': username},
                headers=self._headers_ig(), timeout=15)
            edges = (r.json().get('data', {}).get('user', {})
                     .get('edge_owner_to_timeline_media', {}).get('edges', []))
            if not edges:
                return False
            csrf = self.session.cookies.get('csrftoken', '')
            for e in edges[:num]:
                pid = e['node']['id']
                headers = self._headers_ig()
                headers['X-CSRFToken'] = csrf
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
                self.session.post(
                    f'https://www.instagram.com/api/v1/web/likes/{pid}/like/',
                    headers=headers, timeout=15)
                self._sleep(4, 9)
            return True
        except Exception as e:
            self.log(f"❌ {e}")
            return False

    def ig_follow_user(self, username):
        self.log(f"👥 Follow @{username}...")
        try:
            r = self.session.get(
                'https://www.instagram.com/api/v1/users/web_profile_info/',
                params={'username': username},
                headers=self._headers_ig(), timeout=15)
            uid = r.json().get('data', {}).get('user', {}).get('id')
            if not uid:
                return False
            csrf = self.session.cookies.get('csrftoken', '')
            headers = self._headers_ig()
            headers['X-CSRFToken'] = csrf
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            r2 = self.session.post(
                f'https://www.instagram.com/api/v1/friendships/create/{uid}/',
                headers=headers, data={'container_module': 'profile'},
                timeout=15)
            return r2.status_code == 200
        except Exception as e:
            self.log(f"❌ {e}")
            return False

    def ig_update_bio(self):
        bio = random.choice(self.BIOS)
        self.log(f"📝 Đổi bio...")
        try:
            csrf = self.session.cookies.get('csrftoken', '')
            headers = self._headers_ig()
            headers['X-CSRFToken'] = csrf
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            r = self.session.post(
                'https://www.instagram.com/api/v1/web/accounts/edit_profile/',
                headers=headers,
                data={'biography': bio, 'external_url': '',
                      'chaining_enabled': 'on'}, timeout=15)
            return r.status_code == 200
        except Exception as e:
            self.log(f"❌ {e}")
            return False

    def warmup(self, cookie_str, duration_min=5, actions_per_min=3):
        try:
            self.load_cookies(cookie_str)
            proxy_info = f" | Proxy: {self.proxy}" if self.proxy else " | No Proxy"
            self.log(f"🌱 Nuôi acc {duration_min}p, {actions_per_min}act/p{proxy_info}")
            end_time = time.time() + duration_min * 60
            action_count = 0
            while time.time() < end_time:
                if self.is_stopped():
                    self.log("⏹ Dừng")
                    return
                if self.platform == 'facebook':
                    actions = [
                        self.fb_view_feed, self.fb_like_random,
                        lambda: self.fb_view_profile(random.choice(self.FB_TARGETS)),
                        self.fb_update_bio,
                    ]
                else:
                    target = random.choice(self.IG_TARGETS)
                    actions = [
                        self.ig_view_feed,
                        lambda: self.ig_view_story(target),
                        lambda: self.ig_like_user_posts(target, random.randint(1, 3)),
                        lambda: self.ig_follow_user(target),
                        self.ig_update_bio,
                    ]
                action = random.choice(actions)
                try:
                    action()
                    action_count += 1
                    self.log(f"✅ Action #{action_count}")
                except Exception as e:
                    if 'stopped' in str(e).lower():
                        return
                    self.log(f"⚠️ {e}")
                delay = 60.0 / actions_per_min
                self._sleep(delay * 0.7, delay * 1.3)
            self.log(f"🎉 Xong! {action_count} hành động")
        except Exception as e:
            self.log(f"❌ {e}")


# ═══════════════════════════════════════════════════════════
# AUTO REG PAGE PR5
# ═══════════════════════════════════════════════════════════
class FBPageAutoRegPR5:
    def __init__(self, use_proxy=False):
        self.log_callback = None
        self.is_stopped = lambda: False
        self.use_proxy = use_proxy
        self.proxy = get_next_proxy() if use_proxy else None
        self.session = requests.Session()
        if self.use_proxy and self.proxy:
            self.session.proxies.update(format_proxy_for_requests(self.proxy))

    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    def _hdrs(self, token):
        return {
            'User-Agent': FB4A_UA,
            'authorization': f'OAuth {token}',
            'x-fb-sim-hni': '45201',
            'x-fb-net-hni': '45201',
            'x-graphql-client-library': 'graphservice',
            'x-tigon-is-retry': 'False',
            'x-graphql-request-purpose': 'fetch',
            'x-fb-device-group': '2789',
            'Accept-Encoding': 'gzip, deflate',
            'x-fb-connection-type': 'WIFI',
            'x-fb-http-engine': 'Tigon/Liger',
            'x-fb-client-ip': 'True',
            'x-fb-server-cluster': 'True',
            'Content-Type': 'application/x-www-form-urlencoded',
        }

    def _build_create_variables(self, page_name, category_id):
        inner = (
            '{"client_input_params":{'
            '"page_id":"0","profile_plus_id":"0","cp_upsell_declined":0,'
            '"off_platform_creator_reachout_id":"",'
            f'"category_ids":["{category_id}"],'
            '"nav_chain":"..."'
            '},"server_params":{'
            '"referrer":"pages_tab_launch_point",'
            '"INTERNAL__latency_qpl_marker_id":36707139,'
            '"creation_source":"android",'
            f'"name":"{page_name}",'
            '"variant":5,"screen":"category",'
            '"INTERNAL__latency_qpl_instance_id":5.5098533200051e13}}'
        )
        outer = {"params": inner,
                 "bloks_versioning_id": BLOKS_VERSION_PR5,
                 "app_id": APP_ID_PAGE_CREATE}
        ntc = {"using_white_navbar": True,
               "styles_id": "588d028b36bed0e1889e09b60e0f9aea",
               "pixel_ratio": 2, "is_push_on": True,
               "debug_tooling_metadata_token": None,
               "is_flipper_enabled": False,
               "theme_params": [{"value": [], "design_system_name": "FDS"}],
               "bloks_version": BLOKS_VERSION_PR5}
        return json.dumps({"params": outer, "scale": "2", "nt_context": ntc})

    def step1_create_page(self, token, page_name, category_id):
        self.log(f"📄 B1: Tạo Page '{page_name}'")
        variables = self._build_create_variables(page_name, category_id)
        data = {'method': 'post', 'pretty': 'false', 'format': 'json',
                'server_timestamps': 'true', 'locale': 'vi_VN',
                'client_doc_id': GRAPHQL_DOC_PAGE_CREATE,
                'variables': variables}
        try:
            r = self.session.post('https://graph.facebook.com/graphql',
                                  headers=self._hdrs(token),
                                  data=urllib.parse.urlencode(data),
                                  timeout=60)
            result = r.json()
            raw = json.dumps(result)
            m = re.search(r'"page_id"\s*:\s*"?(\d{6,})"?', raw)
            if m:
                return {'ok': True, 'page_id': m.group(1), 'raw': result}
            m2 = re.search(r'"profile_plus_id"\s*:\s*"?(\d{6,})"?', raw)
            if m2:
                return {'ok': True, 'page_id': m2.group(1), 'raw': result}
            if 'create_success' in raw or 'bloks_bundle_action' in raw:
                return {'ok': True, 'page_id': None, 'raw': result}
            if 'errors' in result:
                err = result.get('errors', [{}])[0].get('message', 'Lỗi')
                return {'ok': False, 'error': err, 'raw': result}
            return {'ok': False, 'error': 'Không tạo được Page', 'raw': result}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def step2_get_page_list(self, token):
        self.log("📋 B2: Lấy danh sách Page...")
        try:
            r = self.session.get('https://graph.facebook.com/me/accounts',
                                 headers=self._hdrs(token),
                                 params={'access_token': token,
                                         'fields': 'id,name,access_token,category'},
                                 timeout=20)
            data = r.json()
            if 'data' in data:
                return {'ok': True, 'pages': data['data']}
            return {'ok': False, 'error': 'Không lấy được page'}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def step3_activate_profile_plus(self, token, page_id):
        self.log(f"✨ B3: Kích hoạt Profile Plus cho Page {page_id}")
        payload_url = (f"/nt/profile_plus/activate?page_id={page_id}"
                       "&enable_profile_plus=true"
                       "&source=page_creation_flow")
        ntc = {"using_white_navbar": True,
               "styles_id": "55d2af294359fa6bbdb8e045ff01fc5e",
               "pixel_ratio": 1.5, "is_push_on": True,
               "debug_tooling_metadata_token": None,
               "is_flipper_enabled": False, "theme_params": [],
               "bloks_version": BLOKS_VERSION_PR5}
        po = {"nt_context": ntc, "payload": payload_url}
        v = {"params": json.dumps(po),
             "bloks_versioning_id": BLOKS_VERSION_PR5,
             "app_id": APP_ID_PROFILE_PLUS,
             "scale": 1, "nt_context": ntc}
        d = {'method': 'post', 'pretty': 'false', 'format': 'json',
             'server_timestamps': 'true', 'locale': 'vi_VN', 'purpose': 'fetch',
             'fb_api_req_friendly_name': 'FbBloksActionRootQuery-com.bloks.www.bloks.caa.profile_plus.creation.async',
             'fb_api_caller_class': 'graphservice',
             'client_doc_id': GRAPHQL_DOC_PROFILE_PLUS,
             'variables': json.dumps(v),
             'fb_api_analytics_tags': '["GraphServices"]',
             'client_trace_id': str(uuid.uuid4())}
        try:
            r = self.session.post('https://graph.facebook.com/graphql',
                                  headers=self._hdrs(token),
                                  data=d, timeout=30)
            result = r.json()
            if 'data' in result or 'errors' not in result:
                return {'ok': True, 'raw': result}
            return {'ok': False, 'error': 'Không activate được Profile Plus',
                    'raw': result}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def step4_set_category(self, token, page_id, category_id):
        self.log(f"🏷️ B4: Set category cho Page {page_id}")
        try:
            r = self.session.post(
                f'https://graph.facebook.com/{page_id}',
                headers=self._hdrs(token),
                data={'access_token': token, 'category': category_id},
                timeout=20)
            data = r.json()
            if data.get('success') or 'id' in data:
                return {'ok': True, 'raw': data}
            return {'ok': False, 'error': str(data), 'raw': data}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def step5_warmup_page(self, token, page_id):
        self.log(f"🔥 B5: Warm-up Page {page_id}")
        try:
            post_text = random.choice([
                "Chào mừng các bạn đến với Page! 🎉",
                "Hôm nay là một ngày tuyệt vời! ☀️",
                "Cảm ơn mọi người đã ủng hộ ❤️",
                "Follow Page để nhận nhiều thông tin hữu ích nhé!",
            ])
            r = self.session.post(
                f'https://graph.facebook.com/{page_id}/feed',
                headers=self._hdrs(token),
                data={'access_token': token, 'message': post_text},
                timeout=30)
            data = r.json()
            if 'id' in data:
                self.log(f"   ✅ Đã đăng bài warm-up: {data['id']}")
            time.sleep(2)
            return {'ok': True}
        except Exception as e:
            self.log(f"   ⚠️ Warm-up lỗi (bỏ qua): {e}")
            return {'ok': True}

    def create_pr5_page(self, token, page_name=None, category="Cá nhân"):
        if not page_name:
            page_name = VNNameGenerator.gen()
        category_id = PAGE_CATEGORIES.get(category,
                                          PAGE_CATEGORIES["Cá nhân"])

        r1 = self.step1_create_page(token, page_name, category_id)
        if not r1.get('ok'):
            return {'ok': False,
                    'error': f"B1 fail: {r1.get('error')}",
                    'page_name': page_name}
        page_id = r1.get('page_id')

        if not page_id:
            time.sleep(3)
            r2 = self.step2_get_page_list(token)
            if r2.get('ok'):
                for p in r2['pages']:
                    if p.get('name', '').strip().lower() == page_name.strip().lower():
                        page_id = p.get('id')
                        break

        if not page_id:
            return {'ok': False, 'error': 'Không lấy được page_id',
                    'page_name': page_name}

        self.log(f"   🎯 Page ID: {page_id}")

        time.sleep(random.uniform(2, 4))
        r3 = self.step3_activate_profile_plus(token, page_id)
        if not r3.get('ok'):
            self.log(f"   ⚠️ B3 lỗi: {r3.get('error')} (tiếp tục)")

        time.sleep(random.uniform(1, 3))
        r4 = self.step4_set_category(token, page_id, category_id)
        if not r4.get('ok'):
            self.log(f"   ⚠️ B4 lỗi: {r4.get('error')} (tiếp tục)")

        time.sleep(random.uniform(2, 4))
        self.step5_warmup_page(token, page_id)

        return {'ok': True, 'page_id': page_id,
                'page_name': page_name, 'category': category,
                'profile_plus': r3.get('ok', False)}


# ═══════════════════════════════════════════════════════════
# FB API FUNCTIONS
# ═══════════════════════════════════════════════════════════
def _fb_req(method, url, use_proxy=False, **kwargs):
    if use_proxy:
        proxy = get_next_proxy()
        if proxy:
            kwargs['proxies'] = format_proxy_for_requests(proxy)
    return requests.request(method, url, **kwargs)

def fb_reaction(token, post_id, reaction_type='LIKE', use_proxy=False):
    try:
        r = _fb_req('GET', 'https://graph.facebook.com/me',
                    use_proxy=use_proxy,
                    params={'access_token': token}, timeout=15)
        actor_id = r.json().get('id')
        if not actor_id:
            return {'ok': False, 'error': 'Token không hợp lệ'}
        fb_id = base64.b64encode(f'feedback:{post_id}'.encode()).decode()
        react_id = REACTION_IDS.get(reaction_type.upper(),
                                     REACTION_IDS['LIKE'])
        variables = json.dumps({
            'input': {'feedback_id': fb_id,
                      'feedback_reaction_id': react_id,
                      'actor_id': actor_id}})
        headers = {'User-Agent': FB_UA_552, 'Accept-Encoding': 'gzip',
                   'authorization': f'OAuth {token}'}
        payload = {'pretty': 'false', 'variables': variables,
                   'method': 'post',
                   'client_doc_id': '2857784093518205785115255697',
                   'format': 'json', 'server_timestamps': 'true',
                   'locale': 'vi_VN'}
        r2 = _fb_req('POST', 'https://graph.facebook.com/graphql',
                     use_proxy=use_proxy, data=payload, headers=headers,
                     timeout=15)
        result = r2.json()
        return {'ok': 'data' in result, 'raw': result}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def fb_get_uid_from_link(link, use_proxy=False):
    url = "https://id.traodoisub.com/api.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://id.traodoisub.com",
        "Referer": "https://id.traodoisub.com/",
    }
    try:
        resp = _fb_req('POST', url, use_proxy=use_proxy,
                       data=urllib.parse.urlencode({"link": link}),
                       headers=headers, timeout=15)
        data = resp.json()
        if data.get("success") == 200 and "id" in data:
            return {'ok': True, 'uid': data['id'], 'raw': data}
        return {'ok': False, 'error': str(data)}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def fb_like_page(token, target_uid, use_proxy=False):
    try:
        r = _fb_req('GET', 'https://graph.facebook.com/me',
                    use_proxy=use_proxy,
                    params={'access_token': token}, timeout=15)
        if not r.json().get('id'):
            return {'ok': False, 'error': 'Token không hợp lệ'}
        attempts = [
            ('POST', f'https://graph.facebook.com/{target_uid}/likes',
             {'access_token': token}),
            ('POST', 'https://graph.facebook.com/me/likes',
             {'id': target_uid, 'access_token': token}),
        ]
        for method, url, payload in attempts:
            try:
                r2 = _fb_req(method, url, use_proxy=use_proxy,
                             data=payload,
                             headers={'User-Agent': FB_UA_552,
                                      'Accept-Encoding': 'gzip'},
                             timeout=20)
                data = r2.json()
                if data.get('success') is True or data.get('id') == str(target_uid):
                    return {'ok': True, 'raw': data}
            except Exception:
                continue
        return {'ok': False, 'error': 'Like page thất bại'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def fb_upload_avatar(token, image_url, use_proxy=False):
    try:
        r = _fb_req('GET', image_url, use_proxy=use_proxy, timeout=30)
        if r.status_code != 200:
            return {'ok': False, 'error': 'Không tải được ảnh'}
        files = {"source": ("avatar.jpg", r.content, "image/jpeg")}
        data = {"access_token": token}
        r2 = _fb_req('POST', "https://graph.facebook.com/me/picture",
                     use_proxy=use_proxy,
                     files=files, data=data, timeout=30)
        if r2.status_code == 200:
            return {'ok': True, 'raw': r2.text}
        return {'ok': False, 'error': f'HTTP {r2.status_code}'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def fb_upload_cover(token, image_url, use_proxy=False):
    try:
        r = _fb_req('GET', image_url, use_proxy=use_proxy, timeout=30)
        if r.status_code != 200:
            return {'ok': False, 'error': 'Không tải được ảnh'}
        files = {"source": ("cover.jpg", r.content, "image/jpeg")}
        data = {"access_token": token, "no_story": "true"}
        r2 = _fb_req('POST', "https://graph.facebook.com/me/photos",
                     use_proxy=use_proxy, files=files, data=data, timeout=30)
        photo_data = r2.json()
        if "id" in photo_data:
            photo_id = photo_data["id"]
            r3 = _fb_req('POST', "https://graph.facebook.com/me",
                         use_proxy=use_proxy,
                         data={"access_token": token, "cover": photo_id},
                         timeout=30)
            if r3.status_code == 200:
                return {'ok': True, 'raw': r3.text}
        return {'ok': False, 'error': 'Upload cover thất bại'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def fb_get_info(token, use_proxy=False):
    try:
        r = _fb_req('GET', "https://graph.facebook.com/me",
                    use_proxy=use_proxy,
                    params={"access_token": token,
                            "fields": "id,name,email,birthday"},
                    timeout=10)
        data = r.json()
        if "id" in data:
            try:
                r2 = _fb_req('GET',
                             f"https://graph.facebook.com/{data['id']}/picture",
                             use_proxy=use_proxy,
                             params={"type": "large", "redirect": "false",
                                     "access_token": token}, timeout=10)
                if "data" in r2.json() and "url" in r2.json()["data"]:
                    data["avatar_url"] = r2.json()["data"]["url"]
            except Exception:
                pass
            return {'ok': True, 'info': data}
        return {'ok': False,
                'error': data.get("error", {}).get("message", "Lỗi")}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def fb_follow(token, target_uid, use_proxy=False):
    try:
        r = _fb_req('GET', 'https://graph.facebook.com/me',
                    use_proxy=use_proxy,
                    params={'access_token': token}, timeout=15)
        actor_id = r.json().get('id')
        if not actor_id:
            return {'ok': False, 'error': 'Token không hợp lệ'}
        ufs_session_id = f'UFS-{uuid.uuid4()}-fg-{random.randint(1, 10)}'
        nav_parts = []
        login_base_s = time.time() - random.uniform(30, 60)
        login_times = [login_base_s + random.uniform(0, 0.3)
                       for _ in range(4)]
        for lt in reversed(login_times):
            nav_parts.append(f'login_{int(lt*1000)}')
        nav_chain = ';'.join(nav_parts)
        base_hdrs = {
            'User-Agent': FB_UA_552, 'Accept-Encoding': 'gzip, deflate',
            'x-fb-rmd': 'state=URL_ELIGIBLE',
            'x-graphql-client-library': 'graphservice',
            'x-fb-connection-type': 'WIFI',
            'authorization': f'OAuth {token}',
            'x-fb-http-engine': 'Tigon/Liger',
            'x-fb-client-ip': 'True', 'x-fb-server-cluster': 'True'}
        api2_vars = json.dumps({
            'input': {'tracking': [], 'subscribee_id': str(target_uid),
                      'subscribe_location': 'PROFILE', 'story_id': None,
                      'is_tracking_encrypted': False,
                      'attribution_id_v2': nav_chain,
                      'downstream_share_navigation_events_count': {
                          'downstream_share_navigation_events_count_vec': [
                              {'name': 'APP_BACKGROUNDED', 'count': 0},
                              {'name': 'APP_FOREGROUNDED', 'count': 0}]},
                      'actor_id': actor_id},
            'fetch_profile_context_row': True, 'nt_context': {}})
        api2_payload = {
            'method': 'post', 'pretty': 'false', 'format': 'json',
            'server_timestamps': 'true', 'locale': 'en_US',
            'fb_api_req_friendly_name': 'ActorSubscribeCoreMutation',
            'fb_api_caller_class': 'graphservice',
            'client_doc_id': '333384874811539315526365045620',
            'variables': api2_vars,
            'fb_api_analytics_tags': json.dumps(
                [f'session_id={ufs_session_id}', 'GraphServices']),
            'client_trace_id': str(uuid.uuid4())}
        h2 = base_hdrs.copy()
        h2['x-fb-friendly-name'] = 'ActorSubscribeCoreMutation'
        h2['x-fb-navigation-chain'] = nav_chain
        r2 = _fb_req('POST', 'https://graph.facebook.com/graphql',
                     use_proxy=use_proxy,
                     data=api2_payload, headers=h2, timeout=30)
        data = r2.json()
        if 'data' in data and 'actor_subscribe' in data.get('data', {}):
            return {'ok': True, 'raw': data}
        return {'ok': False, 'error': 'Follow thất bại', 'raw': data}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def fb_comment(token, post_id, comment_text, use_proxy=False):
    try:
        r = _fb_req('GET', 'https://graph.facebook.com/me',
                    use_proxy=use_proxy,
                    params={'access_token': token}, timeout=15)
        actor_id = r.json().get('id')
        if not actor_id:
            return {'ok': False, 'error': 'Token không hợp lệ'}
        parts = post_id.split('_', 1)
        if len(parts) == 2:
            owner_id, post_fbid = parts
        else:
            post_fbid = post_id
            owner_id = post_id
        feedback_id = base64.b64encode(
            f'feedback:{post_fbid}'.encode()).decode()
        idempotence_token = str(uuid.uuid4())
        ufs_session_id = f'UFS-{uuid.uuid4()}-fg-{random.randint(1, 10)}'
        base_hdrs = {
            'User-Agent': FB_UA_552, 'Accept-Encoding': 'gzip, deflate',
            'x-fb-rmd': 'state=URL_ELIGIBLE', 'priority': 'u=3, i',
            'x-graphql-client-library': 'graphservice',
            'x-fb-connection-type': 'WIFI',
            'authorization': f'OAuth {token}',
            'x-fb-http-engine': 'Tigon/Liger',
            'x-fb-client-ip': 'True', 'x-fb-server-cluster': 'True'}
        bloks_ver = '51ee0924c1a66b5dd670a44370f6278f66485250d78f72d036fb4ff6480c1d16'
        api2_vars = json.dumps({
            'include_ban_block_fields_for_pplus': True,
            'input': {'tracking': [],
                      'skip_link_usage_quota_validation': False,
                      'session_id': ufs_session_id,
                      'privacy_type': 'DEFAULT_PRIVACY',
                      'nectar_module': 'newsfeed_ufi',
                      'actor_id': actor_id,
                      'feedback_source': 'feedback_comments',
                      'message': {'text': comment_text, 'ranges': []},
                      'feedback_referrer': 'native_newsfeed',
                      'feedback_id': feedback_id,
                      'idempotence_token': idempotence_token,
                      'entry_point': 'TAP_FOOTER_COMMENT',
                      'action_timestamp': int(time.time())},
            'nt_context': {'using_white_navbar': True,
                           'styles_id': 'cc0995fd4392efdb0fd2bbe7fc9091fe',
                           'pixel_ratio': 3, 'is_push_on': True,
                           'is_flipper_enabled': False,
                           'theme_params': [{'value': [],
                                             'design_system_name': 'FDS'}],
                           'bloks_version': bloks_ver},
            'feedback_source': 'NEWS_FEED',
            'image_medium_width': 540, 'image_high_width': 1080,
            'image_low_width': 360, 'profile_image_size': 120})
        api2_payload = {
            'method': 'post', 'pretty': 'false', 'format': 'json',
            'server_timestamps': 'true', 'locale': 'en_US',
            'fb_api_req_friendly_name': 'CommentCreateMutation',
            'fb_api_caller_class': 'graphservice',
            'client_doc_id': '847448981415323174993593552',
            'variables': api2_vars,
            'fb_api_analytics_tags': json.dumps(['GraphServices']),
            'client_trace_id': str(uuid.uuid4())}
        h2 = base_hdrs.copy()
        h2['x-fb-friendly-name'] = 'CommentCreateMutation'
        r2 = _fb_req('POST', 'https://graph.facebook.com/graphql',
                     use_proxy=use_proxy,
                     data=api2_payload, headers=h2, timeout=30)
        data = r2.json()
        if 'data' in data and 'comment_create' in data.get('data', {}):
            return {'ok': True, 'raw': data}
        return {'ok': False, 'error': 'Comment thất bại', 'raw': data}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def fb_share(token, post_id, use_proxy=False):
    try:
        r = _fb_req('GET', 'https://graph.facebook.com/me',
                    use_proxy=use_proxy,
                    params={'access_token': token}, timeout=15)
        actor_id = r.json().get('id')
        if not actor_id:
            return {'ok': False, 'error': 'Token không hợp lệ'}
        parts = post_id.split('_', 1)
        if len(parts) != 2:
            return {'ok': False, 'error': 'PostID dạng owner_id_post_fbid'}
        owner_id, post_fbid = parts
        composer_session_id = str(uuid.uuid4())
        raw_linkable = f'S:_I{owner_id}:{post_fbid}:{post_fbid}'
        linkable_id = base64.b64encode(raw_linkable.encode()).decode()
        ufs_session_id = f'UFS-{uuid.uuid4()}-fg-{random.randint(1, 10)}'
        bloks_ver = '51ee0924c1a66b5dd670a44370f6278f66485250d78f72d036fb4ff6480c1d16'
        base_hdrs = {
            'User-Agent': FB_UA_552, 'Accept-Encoding': 'gzip, deflate',
            'x-fb-rmd': 'state=URL_ELIGIBLE', 'priority': 'u=3, i',
            'x-graphql-client-library': 'graphservice',
            'x-fb-connection-type': 'WIFI',
            'authorization': f'OAuth {token}',
            'x-fb-http-engine': 'Tigon/Liger',
            'x-fb-client-ip': 'True', 'x-fb-server-cluster': 'True'}
        api2_input = {
            'tracking': [],
            'logging': {'composer_session_id': composer_session_id},
            'reshare_original_post': 'SHARE_LINK_ONLY',
            'composer_type': 'share',
            'composer_source_surface': 'newsfeed',
            'message': {'text': ''},
            'composer_entry_point': 'uss_feed_to_feed_reshare',
            'action_timestamp': int(time.time()), 'source': 'MOBILE',
            'audiences': [{'undirected': {'privacy': {
                'tag_expansion_state': 'UNSPECIFIED',
                'deny': [], 'base_state': 'EVERYONE', 'allow': []}}}],
            'attachments': [{'link': {'internal_linkable_id': linkable_id}}],
            'audiences_is_complete': True,
            'nectar_module': 'newsfeed_ufi', 'actor_id': actor_id}
        api2_vars = json.dumps({
            'nt_context': {'using_white_navbar': True,
                           'styles_id': 'cc0995fd4392efdb0fd2bbe7fc9091fe',
                           'pixel_ratio': 3, 'is_push_on': True,
                           'is_flipper_enabled': False,
                           'theme_params': [{'value': [],
                                             'design_system_name': 'FDS'}],
                           'bloks_version': bloks_ver},
            'input': api2_input,
            'size_style': 'contain-fit', 'profile_image_size': 120})
        api2_payload = {
            'method': 'post', 'pretty': 'false', 'format': 'json',
            'server_timestamps': 'true', 'locale': 'en_US',
            'fb_api_req_friendly_name': 'ComposerStoryCreateMutation',
            'fb_api_caller_class': 'graphservice',
            'client_doc_id': '9109379068877895824326160447',
            'variables': api2_vars,
            'fb_api_analytics_tags': json.dumps(
                [f'session_id={ufs_session_id}', 'GraphServices']),
            'client_trace_id': str(uuid.uuid4())}
        h2 = base_hdrs.copy()
        h2['x-fb-friendly-name'] = 'ComposerStoryCreateMutation'
        r2 = _fb_req('POST', 'https://graph.facebook.com/graphql',
                     use_proxy=use_proxy,
                     data=api2_payload, headers=h2, timeout=30)
        for line in r2.text.splitlines():
            try:
                item = json.loads(line.strip())
                if 'data' in item and 'story_create' in item['data']:
                    story = item['data']['story_create'].get('story')
                    if story and story.get('id'):
                        return {'ok': True, 'story_id': story['id'],
                                'raw': item}
            except Exception:
                pass
        return {'ok': False, 'error': 'Share thất bại'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def fb_get_pages(token, use_proxy=False):
    try:
        r = _fb_req('GET', "https://graph.facebook.com/me",
                    use_proxy=use_proxy,
                    params={"access_token": token, "fields": "id,name"},
                    timeout=15)
        user_data = r.json()
        uid = user_data.get('id')
        if not uid:
            return {'ok': False, 'error': 'Token không hợp lệ'}
        tool = ChuyenPageTool(use_proxy=use_proxy)
        pages = tool.get_pages(token, uid)
        return {'ok': True, 'user': user_data, 'pages': pages}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


# ═══════════════════════════════════════════════════════════
# PROXY GENERATOR + TOKEN PARSER
# ═══════════════════════════════════════════════════════════
def fetch_proxies(limit=500):
    apis = [
        {'url': 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=3000&country=all&ssl=all&anonymity=all', 'type': 'HTTP'},
        {'url': 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=https&timeout=3000&country=all&ssl=all&anonymity=all', 'type': 'HTTPS'},
        {'url': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt', 'type': 'HTTP'},
        {'url': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/https.txt', 'type': 'HTTPS'},
        {'url': 'https://www.proxy-list.download/api/v1/get?type=https', 'type': 'HTTPS'},
        {'url': 'https://www.proxy-list.download/api/v1/get?type=http', 'type': 'HTTP'},
    ]
    all_p = []
    for a in apis:
        try:
            r = requests.get(a['url'], timeout=12)
            for line in r.text.split('\n'):
                line = line.strip()
                if line and ':' in line and not line.startswith('#'):
                    parts = line.split(':')
                    if len(parts) >= 2:
                        all_p.append({'ip': parts[0], 'port': parts[1],
                                      'type': a['type'],
                                      'url': f"{a['type'].lower()}://{line}",
                                      'status': 'LIVE'})
        except Exception:
            pass
    seen = {}
    https_list, http_list = [], []
    for p in all_p:
        key = f"{p['ip']}:{p['port']}"
        if key in seen:
            continue
        seen[key] = 1
        (https_list if p['type'] == 'HTTPS' else http_list).append(p)
    result = https_list[:limit]
    if len(result) < limit:
        result += http_list[:limit - len(result)]
    return result

def parse_token_cookie(raw):
    result = {'cookies': '', 'tokens': [], 'user_agents': []}
    cookies = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*=[^;\s]+)', raw)
    if cookies:
        seen = {}
        for c in cookies:
            k, v = c.split('=', 1)
            seen[k] = v
        result['cookies'] = '; '.join(f'{k}={v}' for k, v in seen.items())
    tokens = list(set(re.findall(r'(EAA[A-Za-z0-9]{30,})', raw)))
    tokens += list(set(re.findall(
        r'(eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+)', raw)))
    result['tokens'] = tokens
    result['user_agents'] = list(set(re.findall(
        r'(Mozilla/5\.0[^\n\r]{10,300})', raw)))
    return result


# ═══════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════
@app.route('/')
def index():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'index.html')
    if not os.path.exists(html_path):
        return "❌ Không tìm thấy file index.html", 500
    with open(html_path, 'r', encoding='utf-8') as f:
        return Response(f.read(), mimetype='text/html')

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'time': datetime.now().isoformat(),
                    'proxy_count': len(GLOBAL_PROXY_LIST)})

@app.route('/api/proxy/set', methods=['POST'])
def api_proxy_set():
    global GLOBAL_PROXY_LIST, GLOBAL_PROXY_INDEX
    d = request.json or {}
    proxies = d.get('proxies', [])
    if isinstance(proxies, str):
        proxies = [p.strip() for p in proxies.split('\n') if p.strip()]
    seen = set()
    unique = []
    for p in proxies:
        p = p.strip()
        if p and p not in seen:
            seen.add(p)
            unique.append(p)
    with GLOBAL_PROXY_LOCK:
        GLOBAL_PROXY_LIST = unique
        GLOBAL_PROXY_INDEX = 0
    return jsonify({'success': True, 'count': len(unique)})

@app.route('/api/proxy/status')
def api_proxy_status():
    return jsonify({'count': len(GLOBAL_PROXY_LIST),
                    'current_index': GLOBAL_PROXY_INDEX,
                    'preview': GLOBAL_PROXY_LIST[:5]})

@app.route('/api/proxy/clear', methods=['POST'])
def api_proxy_clear():
    global GLOBAL_PROXY_LIST, GLOBAL_PROXY_INDEX
    with GLOBAL_PROXY_LOCK:
        GLOBAL_PROXY_LIST = []
        GLOBAL_PROXY_INDEX = 0
    return jsonify({'success': True})

@app.route('/api/proxy/test', methods=['POST'])
def api_proxy_test():
    proxy = (request.json or {}).get('proxy', '').strip()
    if not proxy:
        return jsonify({'success': False, 'error': 'Thiếu proxy'})
    ok = test_proxy(proxy)
    return jsonify({'success': True, 'alive': ok})

@app.route('/api/proxy/fetch', methods=['POST'])
def api_px_fetch():
    try:
        limit = int((request.json or {}).get('limit', 500))
        proxies = fetch_proxies(limit)
        return jsonify({'success': True, 'proxies': proxies,
                        'total': len(proxies)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/chuyenpage/scan', methods=['POST'])
def api_cp_scan():
    d = request.json or {}
    token = d.get('token', '').strip()
    use_proxy = d.get('use_proxy', False)
    if not token:
        return jsonify({'success': False, 'error': 'Token trống'})
    try:
        t = ChuyenPageTool(use_proxy=use_proxy)
        uid, name = t.get_user_info(token)
        if not uid:
            return jsonify({'success': False, 'error': 'Token không hợp lệ'})
        pages = t.get_pages(token, uid)
        return jsonify({'success': True, 'uid': uid, 'name': name,
                        'pages': pages})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/chuyenpage/transfer', methods=['POST'])
def api_cp_transfer():
    d = request.json or {}
    stk = d.get('source_token', '').strip()
    spwd = d.get('source_password', '').strip()
    ttk = d.get('target_token', '').strip()
    puids = d.get('page_uids', [])
    use_proxy = d.get('use_proxy', False)
    if not all([stk, spwd, ttk, puids]):
        return jsonify({'success': False, 'error': 'Thiếu thông tin'})
    sid = str(uuid.uuid4())
    SESSION_STATUS[sid] = 'running'
    SESSION_LOGS[sid] = []

    def run():
        try:
            t = ChuyenPageTool(use_proxy=use_proxy)
            t.log_callback = lambda m: log_to_session(sid, m)
            if use_proxy and t.proxy:
                log_to_session(sid, f"🌐 Proxy: {t.proxy}")
            tuid, tname = t.get_user_info(ttk)
            if not tuid:
                log_to_session(sid, "❌ Token đích sai")
                SESSION_STATUS[sid] = 'error'
                return
            log_to_session(sid, f"🚀 Chuyển {len(puids)} page → {tname}")
            ok_cnt = 0
            fail_cnt = 0
            for pu in puids:
                if SESSION_STATUS.get(sid) == 'stopped':
                    break
                log_to_session(sid, f"⏳ Xử lý: {pu}")
                ok, msg = t.transfer(stk, spwd, pu, ttk)
                if ok:
                    ok_cnt += 1
                    log_to_session(sid, f"✅ OK: {pu}")
                else:
                    fail_cnt += 1
                    log_to_session(sid, f"❌ Fail: {pu} - {msg}")
                time.sleep(1)
            log_to_session(sid, f"📊 OK={ok_cnt} FAIL={fail_cnt}")
            SESSION_STATUS[sid] = 'done'
        except Exception as e:
            log_to_session(sid, f"❌ {e}")
            SESSION_STATUS[sid] = 'error'

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True, 'session_id': sid})

@app.route('/api/instagram/start', methods=['POST'])
def api_ig_start():
    d = request.json or {}
    num = int(d.get('num_accounts', 1))
    pwd = d.get('password', '').strip()
    use_proxy = d.get('use_proxy', False)
    if len(pwd) < 6:
        return jsonify({'success': False, 'error': 'Password ≥ 6 ký tự'})
    sid = str(uuid.uuid4())
    SESSION_STATUS[sid] = 'running'
    SESSION_LOGS[sid] = []

    def run():
        try:
            t = InstagramReg(use_proxy=use_proxy)
            t.log_callback = lambda m: log_to_session(sid, m)
            t.is_stopped = lambda: SESSION_STATUS.get(sid) == 'stopped'
            log_to_session(sid, f"🚀 Tạo {num} IG acc")
            ok = 0
            for i in range(num):
                if SESSION_STATUS.get(sid) == 'stopped':
                    break
                log_to_session(sid, f"\n=== ACC {i+1}/{num} ===")
                if t.create_account(pwd):
                    ok += 1
                if i < num - 1:
                    time.sleep(3)
            log_to_session(sid, f"\n📊 Thành công: {ok}/{num}")
            SESSION_STATUS[sid] = 'done'
        except Exception as e:
            log_to_session(sid, f"❌ {e}")
            SESSION_STATUS[sid] = 'error'

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True, 'session_id': sid})

@app.route('/api/regfb/start', methods=['POST'])
def api_fb_start():
    d = request.json or {}
    num = int(d.get('num_accounts', 1))
    pwd = d.get('password', 'anhem1234').strip()
    use_proxy = d.get('use_proxy', False)
    sid = str(uuid.uuid4())
    SESSION_STATUS[sid] = 'running'
    SESSION_LOGS[sid] = []

    def run():
        try:
            t = FacebookIOSReg(use_proxy=use_proxy)
            t.log_callback = lambda m: log_to_session(sid, m)
            t.is_stopped = lambda: SESSION_STATUS.get(sid) == 'stopped'
            log_to_session(sid, f"🚀 Tạo {num} FB acc")
            ok = 0
            for i in range(num):
                if SESSION_STATUS.get(sid) == 'stopped':
                    break
                log_to_session(sid, f"\n=== ACC {i+1}/{num} ===")
                success, info = t.register(pwd)
                if success:
                    ok += 1
                if i < num - 1:
                    time.sleep(5)
            log_to_session(sid, f"\n📊 Thành công: {ok}/{num}")
            SESSION_STATUS[sid] = 'done'
        except Exception as e:
            log_to_session(sid, f"❌ {e}")
            SESSION_STATUS[sid] = 'error'

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True, 'session_id': sid})

@app.route('/api/fb/regpagepr5', methods=['POST'])
def api_fb_regpage_pr5():
    d = request.json or {}
    token = d.get('token', '').strip()
    count = int(d.get('count', 1))
    category = d.get('category', 'Cá nhân')
    use_proxy = d.get('use_proxy', False)
    names_input = d.get('names', [])
    if not token:
        return jsonify({'success': False, 'error': 'Token trống'})
    sid = str(uuid.uuid4())
    SESSION_STATUS[sid] = 'running'
    SESSION_LOGS[sid] = []

    def run():
        try:
            t = FBPageAutoRegPR5(use_proxy=use_proxy)
            t.log_callback = lambda m: log_to_session(sid, m)
            t.is_stopped = lambda: SESSION_STATUS.get(sid) == 'stopped'
            log_to_session(sid, f"🚀 Tạo {count} Page PR5 ({category})"
                                f"{' [Proxy]' if use_proxy else ''}")
            ok = 0
            for i in range(count):
                if SESSION_STATUS.get(sid) == 'stopped':
                    break
                log_to_session(sid, f"\n{'='*30}")
                log_to_session(sid, f"📄 PAGE {i+1}/{count}")
                log_to_session(sid, f"{'='*30}")
                pname = names_input[i] if i < len(names_input) and names_input[i] else None
                result = t.create_pr5_page(token, pname, category)
                if result.get('ok'):
                    ok += 1
                    log_to_session(sid,
                                   f"✅ THÀNH CÔNG: {result.get('page_name')} "
                                   f"(ID: {result.get('page_id')}) "
                                   f"PR+: {result.get('profile_plus')}")
                    with open('acc_page_pr5.txt', 'a', encoding='utf-8') as f:
                        f.write(f"{result.get('page_id')}|"
                                f"{result.get('page_name')}|"
                                f"{category}\n")
                else:
                    log_to_session(sid,
                                   f"❌ THẤT BẠI: {result.get('page_name')} - "
                                   f"{result.get('error')}")
                if i < count - 1:
                    time.sleep(5)
            log_to_session(sid, f"\n📊 Thành công: {ok}/{count}")
            SESSION_STATUS[sid] = 'done'
        except Exception as e:
            log_to_session(sid, f"❌ {e}")
            SESSION_STATUS[sid] = 'error'

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True, 'session_id': sid})

@app.route('/api/login/check', methods=['POST'])
def api_login_check():
    d = request.json or {}
    platform = d.get('platform', 'facebook').lower()
    cookies_list = d.get('cookies', [])
    use_proxy = d.get('use_proxy', False)
    if not cookies_list:
        return jsonify({'success': False, 'error': 'Không có cookie'})
    sid = str(uuid.uuid4())
    SESSION_STATUS[sid] = 'running'
    SESSION_LOGS[sid] = []

    def run():
        try:
            live = 0
            die = 0
            results = []
            log_to_session(sid, f"🔐 Check {len(cookies_list)} cookie "
                                f"{platform.upper()}"
                                f"{' [Proxy]' if use_proxy else ''}")
            for i, ck in enumerate(cookies_list):
                if SESSION_STATUS.get(sid) == 'stopped':
                    break
                ck = ck.strip()
                if not ck:
                    continue
                checker = CookieLoginChecker(platform, use_proxy=use_proxy)
                log_to_session(sid, f"\n=== Cookie #{i+1} ===")
                if checker.proxy:
                    log_to_session(sid, f"🌐 Proxy: {checker.proxy}")
                if platform == 'facebook':
                    result = checker.login_facebook(ck)
                else:
                    result = checker.login_instagram(ck)
                if result.get('ok'):
                    live += 1
                    nm = result.get('name') or result.get('username') or ''
                    log_to_session(sid,
                                   f"✅ LIVE: {nm} "
                                   f"(UID: {result.get('uid')})")
                    results.append({'cookie': ck, 'status': 'LIVE',
                                    'uid': result.get('uid'),
                                    'name': nm,
                                    'avatar': result.get('avatar', '')})
                else:
                    die += 1
                    log_to_session(sid, f"❌ DIE: {result.get('error')}")
                    results.append({'cookie': ck, 'status': 'DIE',
                                    'uid': result.get('uid', ''),
                                    'error': result.get('error')})
                time.sleep(1)
            log_to_session(sid, f"\n📊 LIVE={live} | DIE={die}")
            FARM_RESULTS[sid] = results
            SESSION_STATUS[sid] = 'done'
        except Exception as e:
            log_to_session(sid, f"❌ {e}")
            SESSION_STATUS[sid] = 'error'

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True, 'session_id': sid})

@app.route('/api/login/results/<sid>')
def api_login_results(sid):
    return jsonify({'results': FARM_RESULTS.get(sid, [])})

@app.route('/api/farm/start', methods=['POST'])
def api_farm_start():
    d = request.json or {}
    platform = d.get('platform', 'facebook').lower()
    cookie_str = d.get('cookie', '').strip()
    duration = int(d.get('duration', 5))
    actions_per_min = int(d.get('actions_per_min', 3))
    use_proxy = d.get('use_proxy', False)
    if not cookie_str:
        return jsonify({'success': False, 'error': 'Thiếu cookie'})
    sid = str(uuid.uuid4())
    SESSION_STATUS[sid] = 'running'
    SESSION_LOGS[sid] = []

    def run():
        try:
            farmer = AccountFarmer(platform, use_proxy=use_proxy)
            farmer.log_callback = lambda m: log_to_session(sid, m)
            farmer.is_stopped = lambda: SESSION_STATUS.get(sid) == 'stopped'
            farmer.warmup(cookie_str, duration, actions_per_min)
            SESSION_STATUS[sid] = 'done'
        except Exception as e:
            log_to_session(sid, f"❌ {e}")
            SESSION_STATUS[sid] = 'error'

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True, 'session_id': sid})

@app.route('/api/fb/reaction', methods=['POST'])
def api_fb_reaction():
    d = request.json or {}
    result = fb_reaction(d.get('token', '').strip(),
                         d.get('post_id', '').strip(),
                         d.get('reaction', 'LIKE').strip().upper(),
                         d.get('use_proxy', False))
    return jsonify({'success': result.get('ok', False), **result})

@app.route('/api/fb/getpage', methods=['POST'])
def api_fb_getpage():
    d = request.json or {}
    result = fb_get_pages(d.get('token', '').strip(),
                          d.get('use_proxy', False))
    return jsonify({'success': result.get('ok', False), **result})

@app.route('/api/fb/getid', methods=['POST'])
def api_fb_getid():
    d = request.json or {}
    result = fb_get_uid_from_link(d.get('link', '').strip(),
                                  d.get('use_proxy', False))
    return jsonify({'success': result.get('ok', False), **result})

@app.route('/api/fb/likepage', methods=['POST'])
def api_fb_likepage():
    d = request.json or {}
    result = fb_like_page(d.get('token', '').strip(),
                          d.get('target_uid', '').strip(),
                          d.get('use_proxy', False))
    return jsonify({'success': result.get('ok', False), **result})

@app.route('/api/fb/upavatar', methods=['POST'])
def api_fb_upavatar():
    d = request.json or {}
    result = fb_upload_avatar(d.get('token', '').strip(),
                              d.get('image_url', '').strip(),
                              d.get('use_proxy', False))
    return jsonify({'success': result.get('ok', False), **result})

@app.route('/api/fb/upcover', methods=['POST'])
def api_fb_upcover():
    d = request.json or {}
    result = fb_upload_cover(d.get('token', '').strip(),
                             d.get('image_url', '').strip(),
                             d.get('use_proxy', False))
    return jsonify({'success': result.get('ok', False), **result})

@app.route('/api/fb/follow', methods=['POST'])
def api_fb_follow():
    d = request.json or {}
    result = fb_follow(d.get('token', '').strip(),
                       d.get('target_uid', '').strip(),
                       d.get('use_proxy', False))
    return jsonify({'success': result.get('ok', False), **result})

@app.route('/api/fb/comment', methods=['POST'])
def api_fb_comment():
    d = request.json or {}
    result = fb_comment(d.get('token', '').strip(),
                        d.get('post_id', '').strip(),
                        d.get('text', '').strip(),
                        d.get('use_proxy', False))
    return jsonify({'success': result.get('ok', False), **result})

@app.route('/api/fb/share', methods=['POST'])
def api_fb_share():
    d = request.json or {}
    result = fb_share(d.get('token', '').strip(),
                      d.get('post_id', '').strip(),
                      d.get('use_proxy', False))
    return jsonify({'success': result.get('ok', False), **result})

@app.route('/api/fb/getinfo', methods=['POST'])
def api_fb_getinfo():
    d = request.json or {}
    result = fb_get_info(d.get('token', '').strip(),
                         d.get('use_proxy', False))
    return jsonify({'success': result.get('ok', False), **result})

@app.route('/api/gettoken/parse', methods=['POST'])
def api_tk_parse():
    raw = (request.json or {}).get('raw', '')
    return jsonify({'success': True, 'result': parse_token_cookie(raw)})

@app.route('/api/logs/<sid>')
def api_logs(sid):
    def gen():
        idx = 0
        while True:
            if sid in SESSION_LOGS:
                logs = SESSION_LOGS[sid]
                if idx < len(logs):
                    for l in logs[idx:]:
                        yield f"data: {json.dumps(l, ensure_ascii=False)}\n\n"
                    idx = len(logs)
            st = SESSION_STATUS.get(sid, 'unknown')
            yield f"data: {json.dumps({'status': st}, ensure_ascii=False)}\n\n"
            if st in ['done', 'error', 'stopped']:
                yield f"data: {json.dumps({'status': 'closed'}, ensure_ascii=False)}\n\n"
                break
            time.sleep(0.5)
    return Response(stream_with_context(gen()),
                    mimetype='text/event-stream')

@app.route('/api/stop/<sid>', methods=['POST'])
def api_stop(sid):
    SESSION_STATUS[sid] = 'stopped'
    return jsonify({'success': True})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 60)
    print("  🚀 VNDEVCODE MULTI TOOL WEB - FULL")
    print(f"  🌐 http://localhost:{port}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
"app_id": "com.bloks.www.bloks.caa.admin_management.permissions_reauth",
             "scale": 1, "nt_context": ntc}
        d = {"method": "post", "pretty": "false", "format": "json",
             "server_timestamps": "true", "locale": "vi_VN", "purpose": "fetch",
             "fb_api_req_friendly_name": "FbBloksActionRootQuery-com.bloks.www.bloks.caa.admin_management.permissions_reauth",
             "fb_api_caller_class": "graphservice",
             "client_doc_id": "30749539927629244093798192451",
             "variables": json.dumps(v),
             "fb_api_analytics_tags": '["GraphServices"]',
             "client_trace_id": str(uuid.uuid4())}
        try:
            return self._req('POST', "https://b-graph.facebook.com/graphql",
                             headers=self._hdrs(stk), data=d, timeout=30).json()
        except Exception as e:
            return {"error": str(e)}

    def _accept_inv(self, ttk, inv_id):
        self.log(f"✅ Chấp nhận lời mời (ID: {inv_id})")
        url = f"/nt/profile/admin_management/accept_invitation?invitation_id={inv_id}"
        ntc = {"using_white_navbar": True,
               "styles_id": "55d2af294359fa6bbdb8e045ff01fc5e",
               "pixel_ratio": 1.5, "is_push_on": True,
               "debug_tooling_metadata_token": None,
               "is_flipper_enabled": False, "theme_params": [],
               "bloks_version": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c"}
        po = {"nt_context": ntc, "payload": url}
        v = {"params": json.dumps(po),
             "bloks_versioning_id": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c",
             "app_id": "com.bloks.www.bloks.caa.admin_management.accept_invitation",
             "scale": 1, "nt_context": ntc}
        d = {"method": "post", "pretty": "false", "format": "json",
             "server_timestamps": "true", "locale": "vi_VN", "purpose": "fetch",
             "fb_api_req_friendly_name": "FbBloksActionRootQuery-com.bloks.www.bloks.caa.admin_management.accept_invitation",
             "fb_api_caller_class": "graphservice",
             "client_doc_id": "11994080423986492941384902285",
             "variables": json.dumps(v),
             "fb_api_analytics_tags": '["GraphServices"]',
             "client_trace_id": str(uuid.uuid4())}
        try:
            return self._req('POST', "https://b-graph.facebook.com/graphql",
                             headers=self._hdrs(ttk), data=d, timeout=30).json()
        except Exception as e:
            return {"error": str(e)}

    def _extract_inv_id(self, r):
        t = json.dumps(r)
        for p in [r'"invitation_id":"([^"]+)"',
                  r'"id":"([^"]+)"',
                  r'"confirmation_code":"([^"]+)"']:
            m = re.search(p, t)
            if m:
                return m.group(1)
        return None

    def transfer(self, stk, spwd, puid, ttk):
        tuid, _ = self.get_user_info(ttk)
        if not tuid:
            return False, "Không lấy được UID đích"
        r1 = self._send_inv(stk, spwd, puid, tuid)
        if "error" in r1:
            return False, f"Lỗi gửi: {r1['error']}"
        if r1.get("errors"):
            return False, f"Lỗi server: {r1['errors']}"
        inv = self._extract_inv_id(r1)
        if not inv:
            return False, "Không tìm thấy invitation_id"
        r2 = self._accept_inv(ttk, inv)
        if "error" in r2:
            return False, f"Lỗi accept: {r2['error']}"
        if r2.get("errors"):
            return False, f"Lỗi accept server: {r2['errors']}"
        return True, "OK"


# ═══════════════════════════════════════════════════════════
# MODULE: TEMP EMAIL
# ═══════════════════════════════════════════════════════════
class TempEmailGenerator:
    def __init__(self, use_proxy=False):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        })
        self.use_proxy = use_proxy
        self.proxy = get_next_proxy() if use_proxy else None
        self.email_tokens = {}
        self.generated_usernames = set()

    def _req(self, method, url, **kwargs):
        if self.use_proxy and self.proxy:
            kwargs['proxies'] = format_proxy_for_requests(self.proxy)
        return requests.request(method, url, **kwargs)

    def _gen_username(self):
        ho = ['nguyen', 'tran', 'le', 'pham', 'hoang', 'huynh', 'phan', 'vu',
              'vo', 'dang', 'bui', 'do', 'ho', 'ngo', 'duong', 'ly']
        td = ['thi', 'van', 'duc', 'minh', 'quoc', 'thanh', 'ngoc', 'bao',
              'gia', 'khanh']
        t = ['an', 'binh', 'chi', 'duong', 'giang', 'han', 'khang', 'lam',
             'long', 'my', 'nhi', 'phong', 'quan', 'son', 'trang', 'uyen',
             'vy', 'yen']
        fmt = random.choice([1, 2, 3])
        if fmt == 1:
            u = f"{random.choice(ho)}{random.choice(td)}{random.choice(t)}"
        elif fmt == 2:
            u = f"{random.choice(ho)}{random.choice(t)}{random.choice(t)}"
        else:
            u = f"{random.choice(t)}{random.choice(td)}{random.choice(ho)}"
        u += str(random.randint(10, 999))
        if u in self.generated_usernames:
            u += str(random.randint(1000, 9999))
        self.generated_usernames.add(u)
        return u

    def _get_domains(self):
        try:
            r = self._req('GET', 'https://api.mail.tm/domains', timeout=8)
            if r.status_code == 200:
                d = r.json()
                if 'hydra:member' in d:
                    doms = [x['domain'] for x in d['hydra:member']
                            if x.get('isActive')]
                    if doms:
                        return doms
        except Exception:
            pass
        return ['agristur.com', 'febbox.com', 'main.truf.biz']

    def _get_token(self, email, pwd):
        if email in self.email_tokens:
            return self.email_tokens[email]
        try:
            r = self._req('POST', 'https://api.mail.tm/token',
                          json={'address': email, 'password': pwd}, timeout=10)
            if r.status_code == 200:
                tk = r.json().get('token')
                self.email_tokens[email] = tk
                return tk
        except Exception:
            pass
        return None

    def create_email(self):
        for _ in range(3):
            try:
                doms = self._get_domains()
                if not doms:
                    return None
                u = self._gen_username()
                dom = random.choice(doms)
                pwd = ''.join(random.choice(string.ascii_letters + string.digits)
                              for _ in range(12))
                r = self._req('POST', 'https://api.mail.tm/accounts',
                              json={'address': f'{u}@{dom}',
                                    'password': pwd}, timeout=12)
                if r.status_code == 201:
                    addr = f'{u}@{dom}'
                    tk = self._get_token(addr, pwd)
                    return {'email': addr, 'password': pwd,
                            'service': 'mailtm', 'token': tk}
            except Exception:
                pass
            time.sleep(2)
        return None

    def get_messages(self, email_info):
        try:
            tk = email_info.get('token') or self._get_token(
                email_info['email'], email_info['password'])
            if not tk:
                return []
            r = self._req('GET', 'https://api.mail.tm/messages',
                          headers={'Authorization': f'Bearer {tk}'},
                          timeout=10)
            if r.status_code == 200:
                d = r.json()
                msgs = d.get('hydra:member', []) if 'hydra:member' in d else []
                msgs.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
                for m in msgs[:3]:
                    try:
                        cr = self._req('GET',
                                       f"https://api.mail.tm/messages/{m['id']}",
                                       headers={'Authorization': f'Bearer {tk}'},
                                       timeout=8)
                        if cr.status_code == 200:
                            j = cr.json()
                            m['full_content'] = j.get('text', '') or j.get('html', '')
                    except Exception:
                        pass
                return msgs
        except Exception:
            pass
        return []


# ═══════════════════════════════════════════════════════════
# MODULE: INSTAGRAM REG
# ═══════════════════════════════════════════════════════════
class InstagramReg:
    def __init__(self, use_proxy=False):
        self.log_callback = None
        self.is_stopped = lambda: False
        self.use_proxy = use_proxy
        self.proxy = get_next_proxy() if use_proxy else None
        self.email_gen = TempEmailGenerator(use_proxy=use_proxy)
        self.displayed_msgs = set()

    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    def _ua(self):
        devs = ["iPhone15,2", "iPhone14,7", "iPhone13,2", "iPhone12,1",
                "iPhone11,2"]
        ios = ["17_2", "16_4", "15_5", "17_0"]
        return (f'Mozilla/5.0 ({random.choice(devs)}; CPU iPhone OS '
                f'{random.choice(ios)} like Mac OS X) AppleWebKit/605.1.15 '
                f'(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/605.1')

    def _session(self):
        s = requests.Session()
        s.headers.update({
            'accept': '*/*',
            'accept-language': 'vi-VN,vi;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.instagram.com',
            'referer': 'https://www.instagram.com/accounts/emailsignup/',
            'user-agent': self._ua()
        })
        if self.use_proxy and self.proxy:
            s.proxies.update(format_proxy_for_requests(self.proxy))
        return s

    def _init_cookies(self, s):
        try:
            s.get('https://www.instagram.com/', timeout=30)
            time.sleep(random.uniform(2, 4))
            r = s.get('https://www.instagram.com/accounts/emailsignup/',
                      timeout=30)
            if r.status_code == 200:
                csrf = s.cookies.get('csrftoken') or ''.join(
                    random.choice(string.ascii_letters + string.digits)
                    for _ in range(32))
                s.headers['x-csrftoken'] = csrf
                return csrf
        except Exception:
            pass
        return None

    def _gen_name(self):
        ho = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Vũ', 'Đặng',
              'Bùi', 'Đỗ', 'Ngô']
        td = ['Thị', 'Văn', 'Đức', 'Minh', 'Quốc', 'Thanh', 'Ngọc',
              'Bảo', 'Gia']
        t = ['An', 'Bình', 'Chi', 'Dương', 'Giang', 'Hân', 'Khang',
             'Lam', 'Long', 'My', 'Nhi', 'Phong', 'Quân', 'Sơn', 'Trang']
        return f"{random.choice(ho)} {random.choice(td)} {random.choice(t)}"

    def _gen_ig_username(self, name):
        u = re.sub(r'[^a-zA-Z0-9]', '', name.lower())
        return u + str(random.randint(100, 9999))

    def create_account(self, pwd):
        s = self._session()
        csrf = self._init_cookies(s)
        if not csrf:
            self.log("❌ Không init được session")
            return False

        email_info = self.email_gen.create_email()
        if not email_info:
            self.log("❌ Không tạo được email")
            return False
        email = email_info['email']
        self.log(f"📧 Email: {email}")

        first_name = self._gen_name()
        username = self._gen_ig_username(first_name)
        client_id = ''.join(random.choice(string.ascii_lowercase + string.digits)
                            for _ in range(20))
        jazoest = ''.join(random.choice(string.digits) for _ in range(5))

        enc_pwd = f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{pwd}"
        data1 = {'enc_password': enc_pwd, 'email': email,
                 'username': username, 'first_name': first_name,
                 'client_id': client_id, 'seamless_login_enabled': '1',
                 'opt_into_one_tap': 'false', 'jazoest': jazoest}
        try:
            r1 = s.post('https://www.instagram.com/api/v1/web/accounts/web_create_ajax/attempt/',
                        data=data1, timeout=45)
            self.log(f"• Signup step 1: HTTP {r1.status_code}")
            if r1.status_code != 200:
                return False
        except Exception as e:
            self.log(f"❌ Lỗi step1: {e}")
            return False

        try:
            s.post('https://www.instagram.com/api/v1/web/consent/check_age_eligibility/',
                   data={'day': str(random.randint(1, 28)),
                         'month': str(random.randint(1, 12)),
                         'year': str(random.randint(1990, 2000)),
                         'jazoest': jazoest}, timeout=30)
        except Exception:
            pass

        try:
            s.post('https://www.instagram.com/api/v1/accounts/send_verify_email/',
                   data={'device_id': client_id, 'email': email,
                         'jazoest': jazoest}, timeout=30)
            self.log("• Đã gửi code verify")
        except Exception:
            pass

        code = None
        for i in range(60):
            if self.is_stopped():
                return False
            msgs = self.email_gen.get_messages(email_info)
            for m in msgs:
                mid = m.get('id', '')
                key = f"{email}_{mid}"
                if key in self.displayed_msgs:
                    continue
                self.displayed_msgs.add(key)
                content = (m.get('full_content', '') + ' ' +
                           m.get('subject', ''))
                codes = re.findall(r'\b\d{6}\b', content)
                if codes:
                    code = codes[0]
                    self.log(f"✅ Code: {code}")
                    break
            if code:
                break
            time.sleep(2)

        if not code:
            self.log("❌ Không lấy được code")
            return False

        data2 = {'enc_password': enc_pwd,
                 'day': str(random.randint(1, 28)),
                 'email': email, 'failed_birthday_year_count': '{}',
                 'first_name': first_name,
                 'month': str(random.randint(1, 12)),
                 'username': username,
                 'year': str(random.randint(1990, 2000)),
                 'client_id': client_id, 'seamless_login_enabled': '1',
                 'tos_version': 'row', 'force_sign_up_code': code,
                 'jazoest': jazoest}
        try:
            r2 = s.post('https://www.instagram.com/api/v1/web/accounts/web_create_ajax/',
                        data=data2, timeout=30)
            res = r2.json()
            if res.get('account_created') or res.get('user_id'):
                self.log(f"✅ TẠO THÀNH CÔNG: {username}")
                cookies = s.cookies.get_dict()
                important = {k: cookies[k] for k in
                             ['csrftoken', 'sessionid', 'ds_user_id',
                              'ig_did', 'mid', 'datr'] if k in cookies}
                ck_str = '; '.join(f'{k}={v}' for k, v in important.items())
                with open('account_instagram.txt', 'a', encoding='utf-8') as f:
                    f.write(f"||{first_name} | {username} | {pwd} | {email}||\n")
                    f.write(f"||{ck_str}||\n")
                return True
            else:
                self.log(f"❌ Lỗi: {res}")
                return False
        except Exception as e:
            self.log(f"❌ Lỗi hoàn tất: {e}")
            return False


# ═══════════════════════════════════════════════════════════
# MODULE: FACEBOOK iOS REG
# ═══════════════════════════════════════════════════════════
class FacebookIOSReg:
    def __init__(self, use_proxy=False):
        self.log_callback = None
        self.is_stopped = lambda: False
        self.use_proxy = use_proxy

    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    def register(self, password='anhem1234'):
        self.log("🚀 Bắt đầu đăng ký Facebook iOS")
        email_gen = TempEmailGenerator(use_proxy=self.use_proxy)
        email_info = email_gen.create_email()
        if not email_info:
            self.log("❌ Không tạo được email")
            return False, None
        email = email_info['email']
        self.log(f"📧 Email: {email}")

        ho = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Vũ']
        ten = ['An', 'Bình', 'Chi', 'Dương', 'Giang', 'Hân']
        last_name = random.choice(ho)
        first_name = random.choice(ten)
        full_name = f"{last_name} {first_name}"
        self.log(f"👤 Tên: {full_name}")

        code = None
        self.log("⏳ Đợi OTP...")
        for i in range(60):
            if self.is_stopped():
                return False, None
            msgs = email_gen.get_messages(email_info)
            for m in msgs:
                content = (m.get('full_content', '') + ' ' +
                           m.get('subject', ''))
                codes = re.findall(r'\b\d{5,6}\b', content)
                if codes:
                    code = codes[0]
                    self.log(f"✅ OTP: {code}")
                    break
            if code:
                break
            time.sleep(2)

        if not code:
            self.log("❌ Không lấy được OTP")
            return False, None

        with open('account_facebook.txt', 'a', encoding='utf-8') as f:
            f.write(f"{email}|{password}|{full_name}|{code}\n")

        self.log("⚠️ FB iOS Reg cần IP sạch + device thật")
        return True, {'email': email, 'password': password,
                      'name': full_name, 'code': code}


# ═══════════════════════════════════════════════════════════
# MODULE: COOKIE LOGIN CHECKER
# ═══════════════════════════════════════════════════════════
class CookieLoginChecker:
    def __init__(self, platform='facebook', use_proxy=False):
        self.platform = platform.lower()
        self.session = requests.Session()
        self.use_proxy = use_proxy
        self.proxy = get_next_proxy() if use_proxy else None

    def parse_cookie_string(self, cookie_str):
        cookies = {}
        for item in cookie_str.split(';'):
            item = item.strip()
            if '=' in item:
                k, v = item.split('=', 1)
                cookies[k.strip()] = v.strip()
        return cookies

    def _req(self, method, url, **kwargs):
        if self.use_proxy and self.proxy:
            kwargs['proxies'] = format_proxy_for_requests(self.proxy)
        return requests.request(method, url, **kwargs)

    def login_facebook(self, cookie_str):
        cookies = self.parse_cookie_string(cookie_str)
        if 'c_user' not in cookies:
            return {'ok': False, 'error': 'Cookie thiếu c_user'}
        uid = cookies.get('c_user', '')
        for k, v in cookies.items():
            self.session.cookies.set(k, v, domain='.facebook.com')
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
        }
        try:
            r = self._req('GET', 'https://mbasic.facebook.com/profile.php',
                          headers=headers, cookies=self.session.cookies,
                          timeout=20, allow_redirects=True)
            html = r.text
            url_lower = r.url.lower()
            if 'checkpoint' in url_lower:
                return {'ok': False, 'error': 'Bị checkpoint',
                        'uid': uid, 'status': 'DIE'}
            if 'login' in url_lower and 'profile' not in url_lower:
                return {'ok': False, 'error': 'Cookie hết hạn',
                        'uid': uid, 'status': 'DIE'}
            name = uid
            m = re.search(r'<title>([^<]+)</title>', html)
            if m:
                name = m.group(1).replace(' | Facebook', '').strip()
            avatar = ''
            av_match = re.search(
                r'<img[^>]+src="(https://[^"]+scontent[^"]+)"', html)
            if av_match:
                avatar = av_match.group(1).replace('&amp;', '&')
            return {'ok': True, 'uid': uid, 'name': name,
                    'avatar': avatar, 'status': 'LIVE',
                    'platform': 'facebook'}
        except Exception as e:
            return {'ok': False, 'error': str(e),
                    'uid': uid, 'status': 'ERROR'}

    def login_instagram(self, cookie_str):
        cookies = self.parse_cookie_string(cookie_str)
        if 'sessionid' not in cookies:
            return {'ok': False, 'error': 'Cookie thiếu sessionid'}
        uid = cookies.get('ds_user_id', '')
        for k, v in cookies.items():
            self.session.cookies.set(k, v, domain='.instagram.com')
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) '
                          'AppleWebKit/605.1.15 (KHTML, like Gecko) '
                          'Version/17.0 Mobile/15E148 Safari/604.1',
            'Accept': '*/*',
            'Accept-Language': 'vi-VN,vi;q=0.9',
            'X-IG-App-ID': '936619743392459',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.instagram.com/',
        }
        try:
            r = self._req('GET',
                          'https://www.instagram.com/api/v1/users/web_profile_info/',
                          headers=headers, cookies=self.session.cookies,
                          timeout=20)
            if r.status_code == 200:
                try:
                    data = r.json()
                    user = data.get('data', {}).get('user', {})
                    if user.get('id'):
                        return {
                            'ok': True, 'uid': user.get('id'),
                            'username': user.get('username', ''),
                            'name': user.get('full_name', ''),
                            'avatar': user.get('profile_pic_url_hd', ''),
                            'followers': user.get('edge_followed_by', {}).get('count', 0),
                            'status': 'LIVE', 'platform': 'instagram'}
                except Exception:
                    pass
            r2 = self._req('GET', 'https://www.instagram.com/accounts/edit/',
                           headers=headers, cookies=self.session.cookies,
                           timeout=15, allow_redirects=True)
            if 'accounts/login' in r2.url.lower():
                return {'ok': False, 'error': 'Cookie hết hạn',
                        'uid': uid, 'status': 'DIE'}
            return {'ok': True, 'uid': uid, 'status': 'LIVE',
                    'platform': 'instagram', 'name': uid}
        except Exception as e:
            return {'ok': False, 'error': str(e),
                    'uid': uid, 'status': 'ERROR'}


# ═══════════════════════════════════════════════════════════
# MODULE: NUÔI TÀI KHOẢN
# ═══════════════════════════════════════════════════════════
class AccountFarmer:
    FB_TARGETS = ['4', '5', '6', '8', '9', '10', '11', '12']
    IG_TARGETS = ['instagram', 'cristiano', 'leomessi', 'selenagomez',
                  'kyliejenner', 'therock', 'natgeo', 'nasa']
    BIOS = [
        "Sống để học hỏi và sẻ chia.",
        "Photography is my passion 📸",
        "Loving life in Vietnam 🇻🇳",
        "Đơn giản là tôi.",
        "Keep it real 💯",
        "Traveler | Foodie | Dreamer",
        "Work hard, play hard.",
        "Always be yourself.",
    ]

    def __init__(self, platform='facebook', use_proxy=False):
        self.platform = platform.lower()
        self.session = requests.Session()
        self.log_callback = None
        self.is_stopped = lambda: False
        self.use_proxy = use_proxy
        self.proxy = get_next_proxy() if use_proxy else None
        if self.use_proxy and self.proxy:
            self.session.proxies.update(format_proxy_for_requests(self.proxy))

    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    def load_cookies(self, cookie_str):
        cookies = {}
        for item in cookie_str.split(';'):
            item = item.strip()
            if '=' in item:
                k, v = item.split('=', 1)
                cookies[k.strip()] = v.strip()
        for k, v in cookies.items():
            domain = '.facebook.com' if self.platform == 'facebook' else '.instagram.com'
            self.session.cookies.set(k, v, domain=domain)
        return cookies

    def _headers_fb(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Referer': 'https://www.facebook.com/',
        }

    def _headers_ig(self):
        return {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) '
                          'AppleWebKit/605.1.15 (KHTML, like Gecko) '
                          'Version/17.0 Mobile/15E148 Safari/604.1',
            'Accept': '*/*',
            'Accept-Language': 'vi-VN,vi;q=0.9',
            'X-IG-App-ID': '936619743392459',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.instagram.com/',
        }

    def _sleep(self, min_s, max_s):
        t = random.uniform(min_s, max_s)
        end = time.time() + t
        while time.time() < end:
            if self.is_stopped():
                raise Exception('stopped')
            time.sleep(0.5)

    def fb_view_feed(self):
        self.log("📰 Xem feed...")
        try:
            self.session.get('https://mbasic.facebook.com/home.php',
                             headers=self._headers_fb(), timeout=20)
            self._sleep(3, 6)
            return True
        except Exception as e:
            self.log(f"❌ {e}")
            return False

    def fb_like_random(self):
        self.log("❤️ Like bài viết...")
        try:
            r = self.session.get('https://mbasic.facebook.com/home.php',
                                 headers=self._headers_fb(), timeout=20)
            likes = re.findall(r'href="(/a/like\.php[^"]+)"', r.text)
            if not likes:
                return False
            for u in random.sample(likes, min(3, len(likes))):
                full = f'https://mbasic.facebook.com{u.replace("&amp;", "&")}'
                self.session.get(full, headers=self._headers_fb(), timeout=15)
                self._sleep(4, 10)
            return True
        except Exception as e:
            self.log(f"❌ {e}")
            return False

    def fb_view_profile(self, uid):
        self.log(f"👤 Xem profile {uid}...")
        try:
            self.session.get(f'https://mbasic.facebook.com/profile.php?id={uid}',
                             headers=self._headers_fb(), timeout=20)
            self._sleep(3, 8)
            return True
        except Exception as e:
            self.log(f"❌ {e}")
            return False

    def fb_update_bio(self):
        self.log("📝 Đổi bio...")
        try:
            self.session.get('https://mbasic.facebook.com/profile/edit/info',
                             headers=self._headers_fb(), timeout=20)
            self._sleep(2, 4)
            return True
        except Exception as e:
            self.log(f"❌ {e}")
            return False

    def ig_view_feed(self):
        self.log("📰 Lướt IG feed...")
        try:
            self.session.get('https://www.instagram.com/',
                             headers=self._headers_ig(), timeout=20)
            self._sleep(4, 8)
            return True
        except Exception as e:
            self.log(f"❌ {e}")
            return False

    def ig_view_story(self, username):
        self.log(f"📱 Xem story @{username}...")
        try:
            r = self.session.get(
                'https://www.instagram.com/api/v1/users/web_profile_info/',
                params={'username': username},
                headers=self._headers_ig(), timeout=15)
            uid = r.json().get('data', {}).get('user', {}).get('id')
            if not uid:
                return False
            self.session.get(
                f'https://www.instagram.com/api/v1/feed/reels_media/?reel_ids={uid}',
                headers=self._headers_ig(), timeout=15)
            self._sleep(3, 6)
            return True
        except Exception as e:
            self.log(f"❌ {e}")
            return False

    def ig_like_user_posts(self, username, num=3):
        self.log(f"❤️ Like {num} bài @{username}...")
        try:
            r = self.session.get(
                'https://www.instagram.com/api/v1/users/web_profile_info/',
                params={'username': username},
                headers=self._headers_ig(), timeout=15)
            edges = (r.json().get('data', {}).get('user', {})
                     .get('edge_owner_to_timeline_media', {}).get('edges', []))
            if not edges:
                return False
            csrf = self.session.cookies.get('csrftoken', '')
            for e in edges[:num]:
                pid = e['node']['id']
                headers = self._headers_ig()
                headers['X-CSRFToken'] = csrf
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
                self.session.post(
                    f'https://www.instagram.com/api/v1/web/likes/{pid}/like/',
                    headers=headers, timeout=15)
                self._sleep(4, 9)
            return True
        except Exception as e:
            self.log(f"❌ {e}")
            return False

    def ig_follow_user(self, username):
        self.log(f"👥 Follow @{username}...")
        try:
            r = self.session.get(
                'https://www.instagram.com/api/v1/users/web_profile_info/',
                params={'username': username},
                headers=self._headers_ig(), timeout=15)
            uid = r.json().get('data', {}).get('user', {}).get('id')
            if not uid:
                return False
            csrf = self.session.cookies.get('csrftoken', '')
            headers = self._headers_ig()
            headers['X-CSRFToken'] = csrf
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            r2 = self.session.post(
                f'https://www.instagram.com/api/v1/friendships/create/{uid}/',
                headers=headers, data={'container_module': 'profile'},
                timeout=15)
            return r2.status_code == 200
        except Exception as e:
            self.log(f"❌ {e}")
            return False

    def ig_update_bio(self):
        bio = random.choice(self.BIOS)
        self.log(f"📝 Đổi bio...")
        try:
            csrf = self.session.cookies.get('csrftoken', '')
            headers = self._headers_ig()
            headers['X-CSRFToken'] = csrf
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            r = self.session.post(
                'https://www.instagram.com/api/v1/web/accounts/edit_profile/',
                headers=headers,
                data={'biography': bio, 'external_url': '',
                      'chaining_enabled': 'on'}, timeout=15)
            return r.status_code == 200
        except Exception as e:
            self.log(f"❌ {e}")
            return False

    def warmup(self, cookie_str, duration_min=5, actions_per_min=3):
        try:
            self.load_cookies(cookie_str)
            proxy_info = f" | Proxy: {self.proxy}" if self.proxy else " | No Proxy"
            self.log(f"🌱 Nuôi acc {duration_min}p, {actions_per_min}act/p{proxy_info}")
            end_time = time.time() + duration_min * 60
            action_count = 0
            while time.time() < end_time:
                if self.is_stopped():
                    self.log("⏹ Dừng")
                    return
                if self.platform == 'facebook':
                    actions = [
                        self.fb_view_feed, self.fb_like_random,
                        lambda: self.fb_view_profile(random.choice(self.FB_TARGETS)),
                        self.fb_update_bio,
                    ]
                else:
                    target = random.choice(self.IG_TARGETS)
                    actions = [
                        self.ig_view_feed,
                        lambda: self.ig_view_story(target),
                        lambda: self.ig_like_user_posts(target, random.randint(1, 3)),
                        lambda: self.ig_follow_user(target),
                        self.ig_update_bio,
                    ]
                action = random.choice(actions)
                try:
                    action()
                    action_count += 1
                    self.log(f"✅ Action #{action_count}")
                except Exception as e:
                    if 'stopped' in str(e).lower():
                        return
                    self.log(f"⚠️ {e}")
                delay = 60.0 / actions_per_min
                self._sleep(delay * 0.7, delay * 1.3)
            self.log(f"🎉 Xong! {action_count} hành động")
        except Exception as e:
            self.log(f"❌ {e}")


# ═══════════════════════════════════════════════════════════
# MODULE: AUTO REG PAGE PR5
# ═══════════════════════════════════════════════════════════
class FBPageAutoRegPR5:
    def __init__(self, use_proxy=False):
        self.log_callback = None
        self.is_stopped = lambda: False
        self.use_proxy = use_proxy
        self.proxy = get_next_proxy() if use_proxy else None
        self.session = requests.Session()
        if self.use_proxy and self.proxy:
            self.session.proxies.update(format_proxy_for_requests(self.proxy))

    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    def _hdrs(self, token):
        return {
            'User-Agent': FB4A_UA,
            'authorization': f'OAuth {token}',
            'x-fb-sim-hni': '45201',
            'x-fb-net-hni': '45201',
            'x-graphql-client-library': 'graphservice',
            'x-tigon-is-retry': 'False',
            'x-graphql-request-purpose': 'fetch',
            'x-fb-device-group': '2789',
            'Accept-Encoding': 'gzip, deflate',
            'x-fb-connection-type': 'WIFI',
            'x-fb-http-engine': 'Tigon/Liger',
            'x-fb-client-ip': 'True',
            'x-fb-server-cluster': 'True',
            'Content-Type': 'application/x-www-form-urlencoded',
        }

    def _build_create_variables(self, page_name, category_id):
        inner = (
            '{"client_input_params":{'
            '"page_id":"0","profile_plus_id":"0","cp_upsell_declined":0,'
            '"off_platform_creator_reachout_id":"",'
            f'"category_ids":["{category_id}"],'
            '"nav_chain":"..."'
            '},"server_params":{'
            '"referrer":"pages_tab_launch_point",'
            '"INTERNAL__latency_qpl_marker_id":36707139,'
            '"creation_source":"android",'
            f'"name":"{page_name}",'
            '"variant":5,"screen":"category",'
            '"INTERNAL__latency_qpl_instance_id":5.5098533200051e13}}'
        )
        outer = {"params": inner,
                 "bloks_versioning_id": BLOKS_VERSION_PR5,
                 "app_id": APP_ID_PAGE_CREATE}
        ntc = {"using_white_navbar": True,
               "styles_id": "588d028b36bed0e1889e09b60e0f9aea",
               "pixel_ratio": 2, "is_push_on": True,
               "debug_tooling_metadata_token": None,
               "is_flipper_enabled": False,
               "theme_params": [{"value": [], "design_system_name": "FDS"}],
               "bloks_version": BLOKS_VERSION_PR5}
        return json.dumps({"params": outer, "scale": "2", "nt_context": ntc})

    def step1_create_page(self, token, page_name, category_id):
        self.log(f"📄 B1: Tạo Page '{page_name}'")
        variables = self._build_create_variables(page_name, category_id)
        data = {'method': 'post', 'pretty': 'false', 'format': 'json',
                'server_timestamps': 'true', 'locale': 'vi_VN',
                'client_doc_id': GRAPHQL_DOC_PAGE_CREATE,
                'variables': variables}
        try:
            r = self.session.post('https://graph.facebook.com/graphql',
                                  headers=self._hdrs(token),
                                  data=urllib.parse.urlencode(data),
                                  timeout=60)
            result = r.json()
            raw = json.dumps(result)
            m = re.search(r'"page_id"\s*:\s*"?(\d{6,})"?', raw)
            if m:
                return {'ok': True, 'page_id': m.group(1), 'raw': result}
            m2 = re.search(r'"profile_plus_id"\s*:\s*"?(\d{6,})"?', raw)
            if m2:
                return {'ok': True, 'page_id': m2.group(1), 'raw': result}
            if 'create_success' in raw or 'bloks_bundle_action' in raw:
                return {'ok': True, 'page_id': None, 'raw': result}
            if 'errors' in result:
                err = result.get('errors', [{}])[0].get('message', 'Lỗi')
                return {'ok': False, 'error': err, 'raw': result}
            return {'ok': False, 'error': 'Không tạo được Page', 'raw': result}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def step2_get_page_list(self, token):
        self.log("📋 B2: Lấy danh sách Page...")
        try:
            r = self.session.get('https://graph.facebook.com/me/accounts',
                                 headers=self._hdrs(token),
                                 params={'access_token': token,
                                         'fields': 'id,name,access_token,category'},
                                 timeout=20)
            data = r.json()
            if 'data' in data:
                return {'ok': True, 'pages': data['data']}
            return {'ok': False, 'error': 'Không lấy được page'}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def step3_activate_profile_plus(self, token, page_id):
        self.log(f"✨ B3: Kích hoạt Profile Plus cho Page {page_id}")
        payload_url = (f"/nt/profile_plus/activate?page_id={page_id}"
                       "&enable_profile_plus=true"
                       "&source=page_creation_flow")
        ntc = {"using_white_navbar": True,
               "styles_id": "55d2af294359fa6bbdb8e045ff01fc5e",
               "pixel_ratio": 1.5, "is_push_on": True,
               "debug_tooling_metadata_token": None,
               "is_flipper_enabled": False, "theme_params": [],
               "bloks_version": BLOKS_VERSION_PR5}
        po = {"nt_context": ntc, "payload": payload_url}
        v = {"params": json.dumps(po),
             "bloks_versioning_id": BLOKS_VERSION_PR5,
             "app_id": APP_ID_PROFILE_PLUS,
             "scale": 1, "nt_context": ntc}
        d = {'method': 'post', 'pretty': 'false', 'format': 'json',
             'server_timestamps': 'true', 'locale': 'vi_VN', 'purpose': 'fetch',
             'fb_api_req_friendly_name': 'FbBloksActionRootQuery-com.bloks.www.bloks.caa.profile_plus.creation.async',
             'fb_api_caller_class': 'graphservice',
             'client_doc_id': GRAPHQL_DOC_PROFILE_PLUS,
             'variables': json.dumps(v),
             'fb_api_analytics_tags': '["GraphServices"]',
             'client_trace_id': str(uuid.uuid4())}
        try:
            r = self.session.post('https://graph.facebook.com/graphql',
                                  headers=self._hdrs(token),
                                  data=d, timeout=30)
            result = r.json()
            if 'data' in result or 'errors' not in result:
                return {'ok': True, 'raw': result}
            return {'ok': False, 'error': 'Không activate được Profile Plus',
                    'raw': result}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def step4_set_category(self, token, page_id, category_id):
        self.log(f"🏷️ B4: Set category cho Page {page_id}")
        try:
            r = self.session.post(
                f'https://graph.facebook.com/{page_id}',
                headers=self._hdrs(token),
                data={'access_token': token, 'category': category_id},
                timeout=20)
            data = r.json()
            if data.get('success') or 'id' in data:
                return {'ok': True, 'raw': data}
            return {'ok': False, 'error': str(data), 'raw': data}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def step5_warmup_page(self, token, page_id):
        self.log(f"🔥 B5: Warm-up Page {page_id}")
        try:
            post_text = random.choice([
                "Chào mừng các bạn đến với Page! 🎉",
                "Hôm nay là một ngày tuyệt vời! ☀️",
                "Cảm ơn mọi người đã ủng hộ ❤️",
                "Follow Page để nhận nhiều thông tin hữu ích nhé!",
            ])
            r = self.session.post(
                f'https://graph.facebook.com/{page_id}/feed',
                headers=self._hdrs(token),
                data={'access_token': token, 'message': post_text},
                timeout=30)
            data = r.json()
            if 'id' in data:
                self.log(f"   ✅ Đã đăng bài warm-up: {data['id']}")
            time.sleep(2)
            return {'ok': True}
        except Exception as e:
            self.log(f"   ⚠️ Warm-up lỗi (bỏ qua): {e}")
            return {'ok': True}

    def create_pr5_page(self, token, page_name=None, category="Cá nhân"):
        if not page_name:
            page_name = VNNameGenerator.gen()
        category_id = PAGE_CATEGORIES.get(category,
                                          PAGE_CATEGORIES["Cá nhân"])

        r1 = self.step1_create_page(token, page_name, category_id)
        if not r1.get('ok'):
            return {'ok': False,
                    'error': f"B1 fail: {r1.get('error')}",
                    'page_name': page_name}
        page_id = r1.get('page_id')

        if not page_id:
            time.sleep(3)
            r2 = self.step2_get_page_list(token)
            if r2.get('ok'):
                for p in r2['pages']:
                    if p.get('name', '').strip().lower() == page_name.strip().lower():
                        page_id = p.get('id')
                        break

        if not page_id:
            return {'ok': False, 'error': 'Không lấy được page_id',
                    'page_name': page_name}

        self.log(f"   🎯 Page ID: {page_id}")

        time.sleep(random.uniform(2, 4))
        r3 = self.step3_activate_profile_plus(token, page_id)
        if not r3.get('ok'):
            self.log(f"   ⚠️ B3 lỗi: {r3.get('error')} (tiếp tục)")

        time.sleep(random.uniform(1, 3))
        r4 = self.step4_set_category(token, page_id, category_id)
        if not r4.get('ok'):
            self.log(f"   ⚠️ B4 lỗi: {r4.get('error')} (tiếp tục)")

        time.sleep(random.uniform(2, 4))
        self.step5_warmup_page(token, page_id)

        return {'ok': True, 'page_id': page_id,
                'page_name': page_name, 'category': category,
                'profile_plus': r3.get('ok', False)}


# ═══════════════════════════════════════════════════════════
# FB API FUNCTIONS
# ═══════════════════════════════════════════════════════════
def _fb_req(method, url, use_proxy=False, **kwargs):
    if use_proxy:
        proxy = get_next_proxy()
        if proxy:
            kwargs['proxies'] = format_proxy_for_requests(proxy)
    return requests.request(method, url, **kwargs)


def fb_reaction(token, post_id, reaction_type='LIKE', use_proxy=False):
    try:
        r = _fb_req('GET', 'https://graph.facebook.com/me',
                    use_proxy=use_proxy,
                    params={'access_token': token}, timeout=15)
        actor_id = r.json().get('id')
        if not actor_id:
            return {'ok': False, 'error': 'Token không hợp lệ'}
        fb_id = base64.b64encode(f'feedback:{post_id}'.encode()).decode()
        react_id = REACTION_IDS.get(reaction_type.upper(),
                                     REACTION_IDS['LIKE'])
        variables = json.dumps({
            'input': {'feedback_id': fb_id,
                      'feedback_reaction_id': react_id,
                      'actor_id': actor_id}})
        headers = {'User-Agent': FB_UA_552, 'Accept-Encoding': 'gzip',
                   'authorization': f'OAuth {token}'}
        payload = {'pretty': 'false', 'variables': variables,
                   'method': 'post',
                   'client_doc_id': '2857784093518205785115255697',
                   'format': 'json', 'server_timestamps': 'true',
                   'locale': 'vi_VN'}
        r2 = _fb_req('POST', 'https://graph.facebook.com/graphql',
                     use_proxy=use_proxy, data=payload, headers=headers,
                     timeout=15)
        result = r2.json()
        return {'ok': 'data' in result, 'raw': result}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def fb_get_uid_from_link(link, use_proxy=False):
    url = "https://id.traodoisub.com/api.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://id.traodoisub.com",
        "Referer": "https://id.traodoisub.com/",
    }
    try:
        resp = _fb_req('POST', url, use_proxy=use_proxy,
                       data=urllib.parse.urlencode({"link": link}),
                       headers=headers, timeout=15)
        data = resp.json()
        if data.get("success") == 200 and "id" in data:
            return {'ok': True, 'uid': data['id'], 'raw': data}
        return {'ok': False, 'error': str(data)}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def fb_like_page(token, target_uid, use_proxy=False):
    try:
        r = _fb_req('GET', 'https://graph.facebook.com/me',
                    use_proxy=use_proxy,
                    params={'access_token': token}, timeout=15)
        if not r.json().get('id'):
            return {'ok': False, 'error': 'Token không hợp lệ'}
        attempts = [
            ('POST', f'https://graph.facebook.com/{target_uid}/likes',
             {'access_token': token}),
            ('POST', 'https://graph.facebook.com/me/likes',
             {'id': target_uid, 'access_token': token}),
        ]
        for method, url, payload in attempts:
            try:
                r2 = _fb_req(method, url, use_proxy=use_proxy,
                             data=payload,
                             headers={'User-Agent': FB_UA_552,
                                      'Accept-Encoding': 'gzip'},
                             timeout=20)
                data = r2.json()
                if data.get('success') is True or data.get('id') == str(target_uid):
                    return {'ok': True, 'raw': data}
            except Exception:
                continue
        return {'ok': False, 'error': 'Like page thất bại'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def fb_upload_avatar(token, image_url, use_proxy=False):
    try:
        r = _fb_req('GET', image_url, use_proxy=use_proxy, timeout=30)
        if r.status_code != 200:
            return {'ok': False, 'error': 'Không tải được ảnh'}
        files = {"source": ("avatar.jpg", r.content, "image/jpeg")}
        data = {"access_token": token}
        r2 = _fb_req('POST', "https://graph.facebook.com/me/picture",
                     use_proxy=use_proxy,
                     files=files, data=data, timeout=30)
        if r2.status_code == 200:
            return {'ok': True, 'raw': r2.text}
        return {'ok': False, 'error': f'HTTP {r2.status_code}'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def fb_upload_cover(token, image_url, use_proxy=False):
    try:
        r = _fb_req('GET', image_url, use_proxy=use_proxy, timeout=30)
        if r.status_code != 200:
            return {'ok': False, 'error': 'Không tải được ảnh'}
        files = {"source": ("cover.jpg", r.content, "image/jpeg")}
        data = {"access_token": token, "no_story": "true"}
        r2 = _fb_req('POST', "https://graph.facebook.com/me/photos",
                     use_proxy=use_proxy, files=files, data=data, timeout=30)
        photo_data = r2.json()
        if "id" in photo_data:
            photo_id = photo_data["id"]
            r3 = _fb_req('POST', "https://graph.facebook.com/me",
                         use_proxy=use_proxy,
                         data={"access_token": token, "cover": photo_id},
                         timeout=30)
            if r3.status_code == 200:
                return {'ok': True, 'raw': r3.text}
        return {'ok': False, 'error': 'Upload cover thất bại'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def fb_get_info(token, use_proxy=False):
    try:
        r = _fb_req('GET', "https://graph.facebook.com/me",
                    use_proxy=use_proxy,
                    params={"access_token": token,
                            "fields": "id,name,email,birthday"},
                    timeout=10)
        data = r.json()
        if "id" in data:
            try:
                r2 = _fb_req('GET',
                             f"https://graph.facebook.com/{data['id']}/picture",
                             use_proxy=use_proxy,
                             params={"type": "large", "redirect": "false",
                                     "access_token": token}, timeout=10)
                if "data" in r2.json() and "url" in r2.json()["data"]:
                    data["avatar_url"] = r2.json()["data"]["url"]
            except Exception:
                pass
            return {'ok': True, 'info': data}
        return {'ok': False,
                'error': data.get("error", {}).get("message", "Lỗi")}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def fb_follow(token, target_uid, use_proxy=False):
    try:
        r = _fb_req('GET', 'https://graph.facebook.com/me',
                    use_proxy=use_proxy,
                    params={'access_token': token}, timeout=15)
        actor_id = r.json().get('id')
        if not actor_id:
            return {'ok': False, 'error': 'Token không hợp lệ'}
        ufs_session_id = f'UFS-{uuid.uuid4()}-fg-{random.randint(1, 10)}'
        nav_parts = []
        login_base_s = time.time() - random.uniform(30, 60)
        login_times = [login_base_s + random.uniform(0, 0.3)
                       for _ in range(4)]
        for lt in reversed(login_times):
            nav_parts.append(f'login_{int(lt*1000)}')
        nav_chain = ';'.join(nav_parts)
        base_hdrs = {
            'User-Agent': FB_UA_552, 'Accept-Encoding': 'gzip, deflate',
            'x-fb-rmd': 'state=URL_ELIGIBLE',
            'x-graphql-client-library': 'graphservice',
            'x-fb-connection-type': 'WIFI',
            'authorization': f'OAuth {token}',
            'x-fb-http-engine': 'Tigon/Liger',
            'x-fb-client-ip': 'True', 'x-fb-server-cluster': 'True'}
        api2_vars = json.dumps({
            'input': {'tracking': [], 'subscribee_id': str(target_uid),
                      'subscribe_location': 'PROFILE', 'story_id': None,
                      'is_tracking_encrypted': False,
                      'attribution_id_v2': nav_chain,
                      'downstream_share_navigation_events_count': {
                          'downstream_share_navigation_events_count_vec': [
                              {'name': 'APP_BACKGROUNDED', 'count': 0},
                              {'name': 'APP_FOREGROUNDED', 'count': 0}]},
                      'actor_id': actor_id},
            'fetch_profile_context_row': True, 'nt_context': {}})
        api2_payload = {
            'method': 'post', 'pretty': 'false', 'format': 'json',
            'server_timestamps': 'true', 'locale': 'en_US',
            'fb_api_req_friendly_name': 'ActorSubscribeCoreMutation',
            'fb_api_caller_class': 'graphservice',
            'client_doc_id': '333384874811539315526365045620',
            'variables': api2_vars,
            'fb_api_analytics_tags': json.dumps(
                [f'session_id={ufs_session_id}', 'GraphServices']),
            'client_trace_id': str(uuid.uuid4())}
        h2 = base_hdrs.copy()
        h2['x-fb-friendly-name'] = 'ActorSubscribeCoreMutation'
        h2['x-fb-navigation-chain'] = nav_chain
        r2 = _fb_req('POST', 'https://graph.facebook.com/graphql',
                     use_proxy=use_proxy,
                     data=api2_payload, headers=h2, timeout=30)
        data = r2.json()
        if 'data' in data and 'actor_subscribe' in data.get('data', {}):
            return {'ok': True, 'raw': data}
        return {'ok': False, 'error': 'Follow thất bại', 'raw': data}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def fb_comment(token, post_id, comment_text, use_proxy=False):
    try:
        r = _fb_req('GET', 'https://graph.facebook.com/me',
                    use_proxy=use_proxy,
                    params={'access_token': token}, timeout=15)
        actor_id = r.json().get('id')
        if not actor_id:
            return {'ok': False, 'error': 'Token không hợp lệ'}
        parts = post_id.split('_', 1)
        if len(parts) == 2:
            owner_id, post_fbid = parts
        else:
            post_fbid = post_id
            owner_id = post_id
        feedback_id = base64.b64encode(
            f'feedback:{post_fbid}'.encode()).decode()
        idempotence_token = str(uuid.uuid4())
        ufs_session_id = f'UFS-{uuid.uuid4()}-fg-{random.randint(1, 10)}'
        base_hdrs = {
            'User-Agent': FB_UA_552, 'Accept-Encoding': 'gzip, deflate',
            'x-fb-rmd': 'state=URL_ELIGIBLE', 'priority': 'u=3, i',
            'x-graphql-client-library': 'graphservice',
            'x-fb-connection-type': 'WIFI',
            'authorization': f'OAuth {token}',
            'x-fb-http-engine': 'Tigon/Liger',
            'x-fb-client-ip': 'True', 'x-fb-server-cluster': 'True'}
        bloks_ver = '51ee0924c1a66b5dd670a44370f6278f66485250d78f72d036fb4ff6480c1d16'
        api2_vars = json.dumps({
            'include_ban_block_fields_for_pplus': True,
            'input': {'tracking': [],
                      'skip_link_usage_quota_validation': False,
                      'session_id': ufs_session_id,
                      'privacy_type': 'DEFAULT_PRIVACY',
                      'nectar_module': 'newsfeed_ufi',
                      'actor_id': actor_id,
                      'feedback_source': 'feedback_comments',
                      'message': {'text': comment_text, 'ranges': []},
                      'feedback_referrer': 'native_newsfeed',
                      'feedback_id': feedback_id,
                      'idempotence_token': idempotence_token,
                      'entry_point': 'TAP_FOOTER_COMMENT',
                      'action_timestamp': int(time.time())},
            'nt_context': {'using_white_navbar': True,
                           'styles_id': 'cc0995fd4392efdb0fd2bbe7fc9091fe',
                           'pixel_ratio': 3, 'is_push_on': True,
                           'is_flipper_enabled': False,
                           'theme_params': [{'value': [],
                                             'design_system_name': 'FDS'}],
                           'bloks_version': bloks_ver},
            'feedback_source': 'NEWS_FEED',
            'image_medium_width': 540, 'image_high_width': 1080,
            'image_low_width': 360, 'profile_image_size': 120})
        api2_payload = {
            'method': 'post', 'pretty': 'false', 'format': 'json',
            'server_timestamps': 'true', 'locale': 'en_US',
            'fb_api_req_friendly_name': 'CommentCreateMutation',
            'fb_api_caller_class': 'graphservice',
            'client_doc_id': '847448981415323174993593552',
            'variables': api2_vars,
            'fb_api_analytics_tags': json.dumps(['GraphServices']),
            'client_trace_id': str(uuid.uuid4())}
        h2 = base_hdrs.copy()
        h2['x-fb-friendly-name'] = 'CommentCreateMutation'
        r2 = _fb_req('POST', 'https://graph.facebook.com/graphql',
                     use_proxy=use_proxy,
                     data=api2_payload, headers=h2, timeout=30)
        data = r2.json()
        if 'data' in data and 'comment_create' in data.get('data', {}):
            return {'ok': True, 'raw': data}
        return {'ok': False, 'error': 'Comment thất bại', 'raw': data}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def fb_share(token, post_id, use_proxy=False):
    try:
        r = _fb_req('GET', 'https://graph.facebook.com/me',
                    use_proxy=use_proxy,
                    params={'access_token': token}, timeout=15)
        actor_id = r.json().get('id')
        if not actor_id:
            return {'ok': False, 'error': 'Token không hợp lệ'}
        parts = post_id.split('_', 1)
        if len(parts) != 2:
            return {'ok': False, 'error': 'PostID dạng owner_id_post_fbid'}
        owner_id, post_fbid = parts
        composer_session_id = str(uuid.uuid4())
        raw_linkable = f'S:_I{owner_id}:{post_fbid}:{post_fbid}'
        linkable_id = base64.b64encode(raw_linkable.encode()).decode()
        ufs_session_id = f'UFS-{uuid.uuid4()}-fg-{random.randint(1, 10)}'
        bloks_ver = '51ee0924c1a66b5dd670a44370f6278f66485250d78f72d036fb4ff6480c1d16'
        base_hdrs = {
            'User-Agent': FB_UA_552, 'Accept-Encoding': 'gzip, deflate',
            'x-fb-rmd': 'state=URL_ELIGIBLE', 'priority': 'u=3, i',
            'x-graphql-client-library': 'graphservice',
            'x-fb-connection-type': 'WIFI',
            'authorization': f'OAuth {token}',
            'x-fb-http-engine': 'Tigon/Liger',
            'x-fb-client-ip': 'True', 'x-fb-server-cluster': 'True'}
        api2_input = {
            'tracking': [],
            'logging': {'composer_session_id': composer_session_id},
            'reshare_original_post': 'SHARE_LINK_ONLY',
            'composer_type': 'share',
            'composer_source_surface': 'newsfeed',
            'message': {'text': ''},
            'composer_entry_point': 'uss_feed_to_feed_reshare',
            'action_timestamp': int(time.time()), 'source': 'MOBILE',
            'audiences': [{'undirected': {'privacy': {
                'tag_expansion_state': 'UNSPECIFIED',
                'deny': [], 'base_state': 'EVERYONE', 'allow': []}}}],
            'attachments': [{'link': {'internal_linkable_id': linkable_id}}],
            'audiences_is_complete': True,
            'nectar_module': 'newsfeed_ufi', 'actor_id': actor_id}
        api2_vars = json.dumps({
            'nt_context': {'using_white_navbar': True,
                           'styles_id': 'cc0995fd4392efdb0fd2bbe7fc9091fe',
                           'pixel_ratio': 3, 'is_push_on': True,
                           'is_flipper_enabled': False,
                           'theme_params': [{'value': [],
                                             'design_system_name': 'FDS'}],
                           'bloks_version': bloks_ver},
            'input': api2_input,
            'size_style': 'contain-fit', 'profile_image_size': 120})
        api2_payload = {
            'method': 'post', 'pretty': 'false', 'format': 'json',
            'server_timestamps': 'true', 'locale': 'en_US',
            'fb_api_req_friendly_name': 'ComposerStoryCreateMutation',
            'fb_api_caller_class': 'graphservice',
            'client_doc_id': '9109379068877895824326160447',
            'variables': api2_vars,
            'fb_api_analytics_tags': json.dumps(
                [f'session_id={ufs_session_id}', 'GraphServices']),
            'client_trace_id': str(uuid.uuid4())}
        h2 = base_hdrs.copy()
        h2['x-fb-friendly-name'] = 'ComposerStoryCreateMutation'
        r2 = _fb_req('POST', 'https://graph.facebook.com/graphql',
                     use_proxy=use_proxy,
                     data=api2_payload, headers=h2, timeout=30)
        for line in r2.text.splitlines():
            try:
                item = json.loads(line.strip())
                if 'data' in item and 'story_create' in item['data']:
                    story = item['data']['story_create'].get('story')
                    if story and story.get('id'):
                        return {'ok': True, 'story_id': story['id'],
                                'raw': item}
            except Exception:
                pass
        return {'ok': False, 'error': 'Share thất bại'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def fb_get_pages(token, use_proxy=False):
    try:
        r = _fb_req('GET', "https://graph.facebook.com/me",
                    use_proxy=use_proxy,
                    params={"access_token": token, "fields": "id,name"},
                    timeout=15)
        user_data = r.json()
        uid = user_data.get('id')
        if not uid:
            return {'ok': False, 'error': 'Token không hợp lệ'}
        tool = ChuyenPageTool(use_proxy=use_proxy)
        pages = tool.get_pages(token, uid)
        return {'ok': True, 'user': user_data, 'pages': pages}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def fetch_proxies(limit=500):
    apis = [
        {'url': 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=3000&country=all&ssl=all&anonymity=all', 'type': 'HTTP'},
        {'url': 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=https&timeout=3000&country=all&ssl=all&anonymity=all', 'type': 'HTTPS'},
        {'url': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt', 'type': 'HTTP'},
        {'url': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/https.txt', 'type': 'HTTPS'},
        {'url': 'https://www.proxy-list.download/api/v1/get?type=https', 'type': 'HTTPS'},
        {'url': 'https://www.proxy-list.download/api/v1/get?type=http', 'type': 'HTTP'},
    ]
    all_p = []
    for a in apis:
        try:
            r = requests.get(a['url'], timeout=12)
            for line in r.text.split('\n'):
                line = line.strip()
                if line and ':' in line and not line.startswith('#'):
                    parts = line.split(':')
                    if len(parts) >= 2:
                        all_p.append({'ip': parts[0], 'port': parts[1],
                                      'type': a['type'],
                                      'url': f"{a['type'].lower()}://{line}",
                                      'status': 'LIVE'})
        except Exception:
            pass
    seen = {}
    https_list, http_list = [], []
    for p in all_p:
        key = f"{p['ip']}:{p['port']}"
        if key in seen:
            continue
        seen[key] = 1
        (https_list if p['type'] == 'HTTPS' else http_list).append(p)
    result = https_list[:limit]
    if len(result) < limit:
        result += http_list[:limit - len(result)]
    return result


def parse_token_cookie(raw):
    result = {'cookies': '', 'tokens': [], 'user_agents': []}
    cookies = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*=[^;\s]+)', raw)
    if cookies:
        seen = {}
        for c in cookies:
            k, v = c.split('=', 1)
            seen[k] = v
        result['cookies'] = '; '.join(f'{k}={v}' for k, v in seen.items())
    tokens = list(set(re.findall(r'(EAA[A-Za-z0-9]{30,})', raw)))
    tokens += list(set(re.findall(
        r'(eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+)', raw)))
    result['tokens'] = tokens
    result['user_agents'] = list(set(re.findall(
        r'(Mozilla/5\.0[^\n\r]{10,300})', raw)))
    return result


@app.route('/')
def index():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'index.html')
    if not os.path.exists(html_path):
        return "❌ Không tìm thấy file index.html", 500
    with open(html_path, 'r', encoding='utf-8') as f:
        return Response(f.read(), mimetype='text/html')


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'time': datetime.now().isoformat(),
                    'proxy_count': len(GLOBAL_PROXY_LIST)})


@app.route('/api/proxy/set', methods=['POST'])
def api_proxy_set():
    global GLOBAL_PROXY_LIST, GLOBAL_PROXY_INDEX
    d = request.json or {}
    proxies = d.get('proxies', [])
    if isinstance(proxies, str):
        proxies = [p.strip() for p in proxies.split('\n') if p.strip()]
    seen = set()
    unique = []
    for p in proxies:
        p = p.strip()
        if p and p not in seen:
            seen.add(p)
            unique.append(p)
    with GLOBAL_PROXY_LOCK:
        GLOBAL_PROXY_LIST = unique
        GLOBAL_PROXY_INDEX = 0
    return jsonify({'success': True, 'count': len(unique)})


@app.route('/api/proxy/status')
def api_proxy_status():
    return jsonify({'count': len(GLOBAL_PROXY_LIST),
                    'current_index': GLOBAL_PROXY_INDEX,
                    'preview': GLOBAL_PROXY_LIST[:5]})


@app.route('/api/proxy/clear', methods=['POST'])
def api_proxy_clear():
    global GLOBAL_PROXY_LIST, GLOBAL_PROXY_INDEX
    with GLOBAL_PROXY_LOCK:
        GLOBAL_PROXY_LIST = []
        GLOBAL_PROXY_INDEX = 0
    return jsonify({'success': True})


@app.route('/api/proxy/test', methods=['POST'])
def api_proxy_test():
    proxy = (request.json or {}).get('proxy', '').strip()
    if not proxy:
        return jsonify({'success': False, 'error': 'Thiếu proxy'})
    ok = test_proxy(proxy)
    return jsonify({'success': True, 'alive': ok})


@app.route('/api/proxy/fetch', methods=['POST'])
def api_px_fetch():
    try:
        limit = int((request.json or {}).get('limit', 500))
        proxies = fetch_proxies(limit)
        return jsonify({'success': True, 'proxies': proxies,
                        'total': len(proxies)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/chuyenpage/scan', methods=['POST'])
def api_cp_scan():
    d = request.json or {}
    token = d.get('token', '').strip()
    use_proxy = d.get('use_proxy', False)
    if not token:
        return jsonify({'success': False, 'error': 'Token trống'})
    try:
        t = ChuyenPageTool(use_proxy=use_proxy)
        uid, name = t.get_user_info(token)
        if not uid:
            return jsonify({'success': False, 'error': 'Token không hợp lệ'})
        pages = t.get_pages(token, uid)
        return jsonify({'success': True, 'uid': uid, 'name': name,
                        'pages': pages})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/chuyenpage/transfer', methods=['POST'])
def api_cp_transfer():
    d = request.json or {}
    stk = d.get('source_token', '').strip()
    spwd = d.get('source_password', '').strip()
    ttk = d.get('target_token', '').strip()
    puids = d.get('page_uids', [])
    use_proxy = d.get('use_proxy', False)
    if not all([stk, spwd, ttk, puids]):
        return jsonify({'success': False, 'error': 'Thiếu thông tin'})
    sid = str(uuid.uuid4())
    SESSION_STATUS[sid] = 'running'
    SESSION_LOGS[sid] = []

    def run():
        try:
            t = ChuyenPageTool(use_proxy=use_proxy)
            t.log_callback = lambda m: log_to_session(sid, m)
            if use_proxy and t.proxy:
                log_to_session(sid, f"🌐 Proxy: {t.proxy}")
            tuid, tname = t.get_user_info(ttk)
            if not tuid:
                log_to_session(sid, "❌ Token đích sai")
                SESSION_STATUS[sid] = 'error'
                return
            log_to_session(sid, f"🚀 Chuyển {len(puids)} page → {tname}")
            ok_cnt = 0
            fail_cnt = 0
            for pu in puids:
                if SESSION_STATUS.get(sid) == 'stopped':
                    break
                log_to_session(sid, f"⏳ Xử lý: {pu}")
                ok, msg = t.transfer(stk, spwd, pu, ttk)
                if ok:
                    ok_cnt += 1
                    log_to_session(sid, f"✅ OK: {pu}")
                else:
                    fail_cnt += 1
                    log_to_session(sid, f"❌ Fail: {pu} - {msg}")
                time.sleep(1)
            log_to_session(sid, f"📊 OK={ok_cnt} FAIL={fail_cnt}")
            SESSION_STATUS[sid] = 'done'
        except Exception as e:
            log_to_session(sid, f"❌ {e}")
            SESSION_STATUS[sid] = 'error'

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True, 'session_id': sid})


@app.route('/api/instagram/start', methods=['POST'])
def api_ig_start():
    d = request.json or {}
    num = int(d.get('num_accounts', 1))
    pwd = d.get('password', '').strip()
    use_proxy = d.get('use_proxy', False)
    if len(pwd) < 6:
        return jsonify({'success': False, 'error': 'Password ≥ 6 ký tự'})
    sid = str(uuid.uuid4())
    SESSION_STATUS[sid] = 'running'
    SESSION_LOGS[sid] = []

    def run():
        try:
            t = InstagramReg(use_proxy=use_proxy)
            t.log_callback = lambda m: log_to_session(sid, m)
            t.is_stopped = lambda: SESSION_STATUS.get(sid) == 'stopped'
            log_to_session(sid, f"🚀 Tạo {num} IG acc")
            ok = 0
            for i in range(num):
                if SESSION_STATUS.get(sid) == 'stopped':
                    break
                log_to_session(sid, f"\n=== ACC {i+1}/{num} ===")
                if t.create_account(pwd):
                    ok += 1
                if i < num - 1:
                    time.sleep(3)
            log_to_session(sid, f"\n📊 Thành công: {ok}/{num}")
            SESSION_STATUS[sid] = 'done'
        except Exception as e:
            log_to_session(sid, f"❌ {e}")
            SESSION_STATUS[sid] = 'error'

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True, 'session_id': sid})


@app.route('/api/regfb/start', methods=['POST'])
def api_fb_start():
    d = request.json or {}
    num = int(d.get('num_accounts', 1))
    pwd = d.get('password', 'anhem1234').strip()
    use_proxy = d.get('use_proxy', False)
    sid = str(uuid.uuid4())
    SESSION_STATUS[sid] = 'running'
    SESSION_LOGS[sid] = []

    def run():
        try:
            t = FacebookIOSReg(use_proxy=use_proxy)
            t.log_callback = lambda m: log_to_session(sid, m)
            t.is_stopped = lambda: SESSION_STATUS.get(sid) == 'stopped'
            log_to_session(sid, f"🚀 Tạo {num} FB acc")
            ok = 0
            for i in range(num):
                if SESSION_STATUS.get(sid) == 'stopped':
                    break
                log_to_session(sid, f"\n=== ACC {i+1}/{num} ===")
                success, info = t.register(pwd)
                if success:
                    ok += 1
                if i < num - 1:
                    time.sleep(5)
            log_to_session(sid, f"\n📊 Thành công: {ok}/{num}")
            SESSION_STATUS[sid] = 'done'
        except Exception as e:
            log_to_session(sid, f"❌ {e}")
            SESSION_STATUS[sid] = 'error'

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True, 'session_id': sid})


@app.route('/api/fb/regpagepr5', methods=['POST'])
def api_fb_regpage_pr5():
    d = request.json or {}
    token = d.get('token', '').strip()
    count = int(d.get('count', 1))
    category = d.get('category', 'Cá nhân')
    use_proxy = d.get('use_proxy', False)
    names_input = d.get('names', [])
    if not token:
        return jsonify({'success': False, 'error': 'Token trống'})
    sid = str(uuid.uuid4())
    SESSION_STATUS[sid] = 'running'
    SESSION_LOGS[sid] = []

    def run():
        try:
            t = FBPageAutoRegPR5(use_proxy=use_proxy)
            t.log_callback = lambda m: log_to_session(sid, m)
            t.is_stopped = lambda: SESSION_STATUS.get(sid) == 'stopped'
            log_to_session(sid, f"🚀 Tạo {count} Page PR5 ({category})"
                                f"{' [Proxy]' if use_proxy else ''}")
            ok = 0
            for i in range(count):
                if SESSION_STATUS.get(sid) == 'stopped':
                    break
                log_to_session(sid, f"\n{'='*30}")
                log_to_session(sid, f"📄 PAGE {i+1}/{count}")
                log_to_session(sid, f"{'='*30}")
                pname = names_input[i] if i < len(names_input) and names_input[i] else None
                result = t.create_pr5_page(token, pname, category)
                if result.get('ok'):
                    ok += 1
                    log_to_session(sid,
                                   f"✅ THÀNH CÔNG: {result.get('page_name')} "
                                   f"(ID: {result.get('page_id')}) "
                                   f"PR+: {result.get('profile_plus')}")
                    with open('acc_page_pr5.txt', 'a', encoding='utf-8') as f:
                        f.write(f"{result.get('page_id')}|"
                                f"{result.get('page_name')}|"
                                f"{category}\n")
                else:
                    log_to_session(sid,
                                   f"❌ THẤT BẠI: {result.get('page_name')} - "
                                   f"{result.get('error')}")
                if i < count - 1:
                    time.sleep(5)
            log_to_session(sid, f"\n📊 Thành công: {ok}/{count}")
            SESSION_STATUS[sid] = 'done'
        except Exception as e:
            log_to_session(sid, f"❌ {e}")
            SESSION_STATUS[sid] = 'error'

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True, 'session_id': sid})


@app.route('/api/login/check', methods=['POST'])
def api_login_check():
    d = request.json or {}
    platform = d.get('platform', 'facebook').lower()
    cookies_list = d.get('cookies', [])
    use_proxy = d.get('use_proxy', False)
    if not cookies_list:
        return jsonify({'success': False, 'error': 'Không có cookie'})
    sid = str(uuid.uuid4())
    SESSION_STATUS[sid] = 'running'
    SESSION_LOGS[sid] = []

    def run():
        try:
            live = 0
            die = 0
            results = []
            log_to_session(sid, f"🔐 Check {len(cookies_list)} cookie "
                                f"{platform.upper()}"
                                f"{' [Proxy]' if use_proxy else ''}")
            for i, ck in enumerate(cookies_list):
                if SESSION_STATUS.get(sid) == 'stopped':
                    break
                ck = ck.strip()
                if not ck:
                    continue
                checker = CookieLoginChecker(platform, use_proxy=use_proxy)
                log_to_session(sid, f"\n=== Cookie #{i+1} ===")
                if checker.proxy:
                    log_to_session(sid, f"🌐 Proxy: {checker.proxy}")
                if platform == 'facebook':
                    result = checker.login_facebook(ck)
                else:
                    result = checker.login_instagram(ck)
                if result.get('ok'):
                    live += 1
                    nm = result.get('name') or result.get('username') or ''
                    log_to_session(sid,
                                   f"✅ LIVE: {nm} "
                                   f"(UID: {result.get('uid')})")
                    results.append({'cookie': ck, 'status': 'LIVE',
                                    'uid': result.get('uid'),
                                    'name': nm,
                                    'avatar': result.get('avatar', '')})
                else:
                    die += 1
                    log_to_session(sid, f"❌ DIE: {result.get('error')}")
                    results.append({'cookie': ck, 'status': 'DIE',
                                    'uid': result.get('uid', ''),
                                    'error': result.get('error')})
                time.sleep(1)
            log_to_session(sid, f"\n📊 LIVE={live} | DIE={die}")
            FARM_RESULTS[sid] = results
            SESSION_STATUS[sid] = 'done'
        except Exception as e:
            log_to_session(sid, f"❌ {e}")
            SESSION_STATUS[sid] = 'error'

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True, 'session_id': sid})


@app.route('/api/login/results/<sid>')
def api_login_results(sid):
    return jsonify({'results': FARM_RESULTS.get(sid, [])})


@app.route('/api/farm/start', methods=['POST'])
def api_farm_start():
    d = request.json or {}
    platform = d.get('platform', 'facebook').lower()
    cookie_str = d.get('cookie', '').strip()
    duration = int(d.get('duration', 5))
    actions_per_min = int(d.get('actions_per_min', 3))
    use_proxy = d.get('use_proxy', False)
    if not cookie_str:
        return jsonify({'success': False, 'error': 'Thiếu cookie'})
    sid = str(uuid.uuid4())
    SESSION_STATUS[sid] = 'running'
    SESSION_LOGS[sid] = []

    def run():
        try:
            farmer = AccountFarmer(platform, use_proxy=use_proxy)
            farmer.log_callback = lambda m: log_to_session(sid, m)
            farmer.is_stopped = lambda: SESSION_STATUS.get(sid) == 'stopped'
            farmer.warmup(cookie_str, duration, actions_per_min)
            SESSION_STATUS[sid] = 'done'
        except Exception as e:
            log_to_session(sid, f"❌ {e}")
            SESSION_STATUS[sid] = 'error'

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True, 'session_id': sid})


@app.route('/api/fb/reaction', methods=['POST'])
def api_fb_reaction():
    d = request.json or {}
    result = fb_reaction(d.get('token', '').strip(),
                         d.get('post_id', '').strip(),
                         d.get('reaction', 'LIKE').strip().upper(),
                         d.get('use_proxy', False))
    return jsonify({'success': result.get('ok', False), **result})


@app.route('/api/fb/getpage', methods=['POST'])
def api_fb_getpage():
    d = request.json or {}
    result = fb_get_pages(d.get('token', '').strip(),
                          d.get('use_proxy', False))
    return jsonify({'success': result.get('ok', False), **result})


@app.route('/api/fb/getid', methods=['POST'])
def api_fb_getid():
    d = request.json or {}
    result = fb_get_uid_from_link(d.get('link', '').strip(),
                                  d.get('use_proxy', False))
    return jsonify({'success': result.get('ok', False), **result})


@app.route('/api/fb/likepage', methods=['POST'])
def api_fb_likepage():
    d = request.json or {}
    result = fb_like_page(d.get('token', '').strip(),
                          d.get('target_uid', '').strip(),
                          d.get('use_proxy', False))
    return jsonify({'success': result.get('ok', False), **result})


@app.route('/api/fb/upavatar', methods=['POST'])
def api_fb_upavatar():
    d = request.json or {}
    result = fb_upload_avatar(d.get('token', '').strip(),
                              d.get('image_url', '').strip(),
                              d.get('use_proxy', False))
    return jsonify({'success': result.get('ok', False), **result})


@app.route('/api/fb/upcover', methods=['POST'])
def api_fb_upcover():
    d = request.json or {}
    result = fb_upload_cover(d.get('token', '').strip(),
                             d.get('image_url', '').strip(),
                             d.get('use_proxy', False))
    return jsonify({'success': result.get('ok', False), **result})


@app.route('/api/fb/follow', methods=['POST'])
def api_fb_follow():
    d = request.json or {}
    result = fb_follow(d.get('token', '').strip(),
                       d.get('target_uid', '').strip(),
                       d.get('use_proxy', False))
    return jsonify({'success': result.get('ok', False), **result})


@app.route('/api/fb/comment', methods=['POST'])
def api_fb_comment():
    d = request.json or {}
    result = fb_comment(d.get('token', '').strip(),
                        d.get('post_id', '').strip(),
                        d.get('text', '').strip(),
                        d.get('use_proxy', False))
    return jsonify({'success': result.get('ok', False), **result})


@app.route('/api/fb/share', methods=['POST'])
def api_fb_share():
    d = request.json or {}
    result = fb_share(d.get('token', '').strip(),
                      d.get('post_id', '').strip(),
                      d.get('use_proxy', False))
    return jsonify({'success': result.get('ok', False), **result})


@app.route('/api/fb/getinfo', methods=['POST'])
def api_fb_getinfo():
    d = request.json or {}
    result = fb_get_info(d.get('token', '').strip(),
                         d.get('use_proxy', False))
    return jsonify({'success': result.get('ok', False), **result})


@app.route('/api/gettoken/parse', methods=['POST'])
def api_tk_parse():
    raw = (request.json or {}).get('raw', '')
    return jsonify({'success': True, 'result': parse_token_cookie(raw)})


@app.route('/api/logs/<sid>')
def api_logs(sid):
    def gen():
        idx = 0
        while True:
            if sid in SESSION_LOGS:
                logs = SESSION_LOGS[sid]
                if idx < len(logs):
                    for l in logs[idx:]:
                        yield f"data: {json.dumps(l, ensure_ascii=False)}\n\n"
                    idx = len(logs)
            st = SESSION_STATUS.get(sid, 'unknown')
            yield f"data: {json.dumps({'status': st}, ensure_ascii=False)}\n\n"
            if st in ['done', 'error', 'stopped']:
                yield f"data: {json.dumps({'status': 'closed'}, ensure_ascii=False)}\n\n"
                break
            time.sleep(0.5)
    return Response(stream_with_context(gen()),
                    mimetype='text/event-stream')


@app.route('/api/stop/<sid>', methods=['POST'])
def api_stop(sid):
    SESSION_STATUS[sid] = 'stopped'
    return jsonify({'success': True})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 60)
    print("  🚀 VNDEVCODE MULTI TOOL WEB - FULL v3")
    print(f"  🌐 http://localhost:{port}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
