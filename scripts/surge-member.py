#!/usr/bin/env python3
"""SURGE member-authorized knowledge and personal progress client. Standard library only; OAuth credentials stay local."""
from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
import hashlib
import hmac
from http.client import HTTPException
import http.server
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import socket
import stat
import sys
import tempfile
import threading
import time
from urllib import error, parse, request
import webbrowser


DEFAULT_ORIGIN = "https://login.erduo.art"
SCOPES = "member:read member:download member:progress"
LICENSE_SCOPE = "member:license"
SUPPORTED_SCOPES = set(SCOPES.split()) | {LICENSE_SCOPE}
MAX_JSON = 2 * 1024 * 1024


class ClientError(Exception):
    def __init__(self, message, *, status=None, code=None):
        super().__init__(message)
        self.status, self.code = status, code


def normalize_origin(value):
    parsed = parse.urlsplit(value)
    if parsed.username or parsed.password or parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ClientError("origin 必须是没有路径、查询或凭据的站点地址")
    if not parsed.hostname:
        raise ClientError("origin 缺少主机名")
    try:
        parsed.port
    except ValueError as exc:
        raise ClientError("origin 端口格式不正确") from exc
    try:
        local = ipaddress.ip_address(parsed.hostname).is_loopback
    except ValueError:
        local = False
    if parsed.scheme != "https" and not (parsed.scheme == "http" and local):
        raise ClientError("仅允许 HTTPS；本机测试须显式使用回环 IP 的 HTTP 地址")
    if parsed.scheme == "https" and parsed.hostname.endswith("."):
        raise ClientError("请使用规范站点域名")
    return parsed.scheme + "://" + parsed.netloc.lower()


def no_symlinks(path):
    path = Path(os.path.abspath(os.path.expanduser(str(path))))
    for item in [*reversed(path.parents), path]:
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode):
            raise ClientError("路径不能包含符号链接")
    return path


def private_file(path):
    path = no_symlinks(path)
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ClientError("配置必须是独立的普通文件")
    if hasattr(os, "getuid") and info.st_uid != os.getuid():
        raise ClientError("配置文件必须属于当前用户")
    if stat.S_IMODE(info.st_mode) & 0o077:
        raise ClientError("配置文件权限过宽，请设为 600")
    return path


def atomic_config(path, data):
    path = no_symlinks(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    no_symlinks(path.parent)
    info = path.parent.stat()
    if stat.S_IMODE(info.st_mode) & 0o077 or (hasattr(os, "getuid") and info.st_uid != os.getuid()):
        raise ClientError("配置所在目录必须属于当前用户且权限为 700")
    if path.exists():
        private_file(path)
    fd, temp = tempfile.mkstemp(prefix=".surge-config-", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        no_symlinks(path)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


@contextmanager
def config_lock(path):
    """Serialize rotating refresh tokens across CLI processes, without storing tokens in the lock."""
    path = no_symlinks(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    no_symlinks(path.parent)
    info = path.parent.stat()
    if stat.S_IMODE(info.st_mode) & 0o077 or (hasattr(os, "getuid") and info.st_uid != os.getuid()):
        raise ClientError("配置所在目录必须属于当前用户且权限为 700")
    lock = no_symlinks(path.with_name(path.name + ".lock"))
    if lock.exists():
        private_file(lock)
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        os.fchmod(fd, 0o600)
        try:
            if os.name == "nt":
                import msvcrt
                if os.fstat(fd).st_size == 0:
                    os.write(fd, b"0")
                os.lseek(fd, 0, 0)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, OSError) as exc:
            raise ClientError("另一个会员 CLI 命令正在使用此连接，请完成后重试") from exc
        yield
    finally:
        os.close(fd)


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ClientError("请求被重定向，已停止以保护连接凭据")


class Client:
    def __init__(self, config_path, origin=None, timeout=30):
        self.path = no_symlinks(config_path)
        self.data = {}
        if self.path.exists():
            private_file(self.path)
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except (ValueError, OSError) as exc:
                raise ClientError("无法读取连接配置") from exc
            if not isinstance(self.data, dict) or self.data.get("format") != 1:
                raise ClientError("连接配置格式不正确")
        self.origin = normalize_origin(origin or self.data.get("origin") or DEFAULT_ORIGIN)
        if self.data and self.data.get("origin") != self.origin:
            raise ClientError("指定站点与已有配置不同，请为该站点指定独立 --config")
        self.resource = self.origin + "/mcp"
        self.timeout = timeout
        self.opener = request.build_opener(NoRedirect())

    def url(self, value):
        full = parse.urljoin(self.origin + "/", value)
        parsed = parse.urlsplit(full)
        if parsed.username or parsed.password or parsed.fragment:
            raise ClientError("服务地址包含不允许的凭据或片段")
        actual = parsed.scheme + "://" + parsed.netloc.lower()
        if actual != self.origin:
            raise ClientError("拒绝将请求或凭据发往其他站点")
        return full

    def open(self, endpoint, *, data=None, form=None, bearer=None):
        headers = {"Accept": "application/json", "User-Agent": "SURGE-Member-CLI/1"}
        payload = None
        if data is not None:
            payload = json.dumps(data, ensure_ascii=False).encode()
            headers["Content-Type"] = "application/json"
        elif form is not None:
            payload = parse.urlencode(form).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        if bearer:
            headers["Authorization"] = "Bearer " + bearer
        try:
            return self.opener.open(request.Request(self.url(endpoint), data=payload, headers=headers), timeout=self.timeout)
        except error.HTTPError as exc:
            raw = exc.read(8192)
            try:
                body = json.loads(raw)
            except ValueError:
                body = {}
            message = body.get("error_description") or body.get("error") or f"服务返回 HTTP {exc.code}"
            if not isinstance(message, str):
                message = f"服务返回 HTTP {exc.code}"
            for key in ("access_token", "refresh_token"):
                token = self.data.get(key)
                if token:
                    message = message.replace(token, "[凭据已隐藏]")
            raise ClientError(message[:500], status=exc.code, code=body.get("error")) from None
        except (error.URLError, TimeoutError, OSError) as exc:
            raise ClientError("暂时无法连接服务，请检查网络后重试") from exc

    def json(self, endpoint, **kwargs):
        try:
            with self.open(endpoint, **kwargs) as response:
                raw = response.read(MAX_JSON + 1)
        except (HTTPException, OSError) as exc:
            raise ClientError("服务响应中断，请重试读取；授权中断时请重新连接") from exc
        if len(raw) > MAX_JSON:
            raise ClientError("服务返回内容过大，请缩小查询范围")
        try:
            result = json.loads(raw)
        except ValueError as exc:
            raise ClientError("服务未返回有效 JSON") from exc
        if not isinstance(result, dict):
            raise ClientError("服务响应格式不正确")
        return result

    def save_tokens(self, response, *, client_id=None):
        if (not isinstance(response.get("token_type"), str) or response["token_type"].lower() != "bearer" or
                not isinstance(response.get("access_token"), str) or not response["access_token"] or
                not isinstance(response.get("refresh_token"), str) or not response["refresh_token"]):
            raise ClientError("授权服务未返回完整连接凭据")
        try:
            expires = int(response["expires_in"])
        except (KeyError, ValueError, TypeError):
            raise ClientError("授权有效期格式不正确") from None
        if not 0 < expires <= 86400:
            raise ClientError("授权有效期不在支持范围")
        if not isinstance(response.get("scope", SCOPES), str):
            raise ClientError("授权权限格式不正确")
        scopes = response.get("scope", SCOPES).split()
        if any(scope not in SUPPORTED_SCOPES for scope in scopes):
            raise ClientError("授权服务返回了范围外的权限")
        data = {"format": 1, "origin": self.origin, "resource": self.resource,
                "client_id": client_id or self.data.get("client_id"),
                "access_token": response["access_token"], "refresh_token": response["refresh_token"],
                "expires_at": int(time.time()) + expires, "scopes": scopes}
        if not data["client_id"]:
            raise ClientError("连接缺少客户端标识")
        atomic_config(self.path, data)
        self.data = data

    def refresh(self):
        if not self.data.get("refresh_token"):
            raise ClientError("请先运行 login 连接会员账号")
        response = self.json("/oauth/token", form={"grant_type": "refresh_token", "refresh_token": self.data["refresh_token"],
                                                   "client_id": self.data["client_id"], "resource": self.resource})
        self.save_tokens(response)

    def bearer(self):
        if not self.data.get("access_token"):
            raise ClientError("请先运行 login 连接会员账号")
        if self.data.get("resource") != self.resource:
            raise ClientError("配置的授权资源不一致，请重新连接")
        if self.data.get("expires_at", 0) <= time.time() + 30:
            self.refresh()
        return self.data["access_token"]

    def tool(self, name, arguments=None):
        bearer = self.bearer()
        try:
            return self.json("/api/member-agent/v1/tools/" + name, data=arguments or {}, bearer=bearer)
        except ClientError as exc:
            if exc.status != 401:
                raise
            self.refresh()
            return self.json("/api/member-agent/v1/tools/" + name, data=arguments or {}, bearer=self.data["access_token"])

    def status(self):
        return {"connected": bool(self.data.get("access_token")), "origin": self.origin,
                "resource": self.resource, "scopes": self.data.get("scopes", []),
                "access_expires_at": self.data.get("expires_at"), "config": str(self.path),
                "note": "本地连接状态；服务端权限用 access 实时核对"}

    def login(self, *, no_browser=False, wait=300, scopes=SCOPES):
        if scopes not in (SCOPES, LICENSE_SCOPE):
            raise ClientError("不支持的连接权限")
        verifier = secrets.token_urlsafe(48)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        state = secrets.token_urlsafe(32)
        origin = self.origin
        outcome = {}

        class Callback(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def setup(self):
                # A local peer can open a socket without sending a complete request.
                # Bound both idle reads and the whole request, including slow bytes.
                remaining = max(0.001, deadline - time.monotonic())
                self.request.settimeout(min(0.5, remaining))
                super().setup()
                self.deadline_timer = threading.Timer(remaining, self.expire_request)
                self.deadline_timer.daemon = True
                self.deadline_timer.start()

            def expire_request(self):
                try:
                    self.request.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

            def handle(self):
                try:
                    super().handle()
                except OSError:
                    pass  # A timed-out or disconnected callback is not an outcome.

            def finish(self):
                self.deadline_timer.cancel()
                try:
                    super().finish()
                except OSError:
                    pass

            def do_GET(self):
                parts = parse.urlsplit(self.path)
                pairs = parse.parse_qs(parts.query, keep_blank_values=True)
                valid = (parts.path == "/callback" and not outcome and time.monotonic() < deadline and
                         all(len(value) == 1 for value in pairs.values()) and
                         hmac.compare_digest(pairs.get("state", [""])[0], state) and
                         pairs.get("iss", [""])[0] == origin)
                if not valid:
                    self.send_response(400)
                    text = "Callback not accepted. Return to the authorization window."
                else:
                    if pairs.get("error"):
                        outcome["error"] = "授权未完成或已取消"
                    elif pairs.get("code", [""])[0]:
                        outcome["code"] = pairs["code"][0]
                    else:
                        outcome["error"] = "授权回调缺少授权码"
                    self.send_response(200)
                    text = "Authorization received. You can close this window and return to your terminal."
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Security-Policy", "default-src 'none'")
                self.end_headers()
                self.wfile.write(text.encode())

        with http.server.HTTPServer(("127.0.0.1", 0), Callback) as server:
            server.timeout = 0.5
            redirect = f"http://127.0.0.1:{server.server_port}/callback"
            registered = self.json("/oauth/register", data={"client_name": "SURGE 会员 CLI", "redirect_uris": [redirect],
                "grant_types": ["authorization_code", "refresh_token"], "response_types": ["code"], "token_endpoint_auth_method": "none", "scope": scopes})
            client_id = registered.get("client_id")
            if not isinstance(client_id, str) or not client_id:
                raise ClientError("客户端注册未返回有效标识")
            url = self.origin + "/oauth/authorize?" + parse.urlencode({"response_type": "code", "client_id": client_id,
                "redirect_uri": redirect, "scope": scopes, "state": state, "code_challenge": challenge,
                "code_challenge_method": "S256", "resource": self.resource})
            deadline = time.monotonic() + wait
            print("请在浏览器完成会员授权。以下链接仅用于本次连接：\n" + url, file=sys.stderr, flush=True)
            if not no_browser:
                webbrowser.open(url)
            while not outcome and time.monotonic() < deadline:
                server.timeout = min(0.5, max(0.001, deadline - time.monotonic()))
                server.handle_request()
            if not outcome:
                raise ClientError("等待授权超时，请重新运行 login")
            if outcome.get("error"):
                raise ClientError(outcome["error"])
            response = self.json("/oauth/token", form={"grant_type": "authorization_code", "client_id": client_id,
                "code": outcome["code"], "redirect_uri": redirect, "code_verifier": verifier, "resource": self.resource})
            self.save_tokens(response, client_id=client_id)
        return {"connected": True, "origin": self.origin, "scopes": self.data["scopes"], "config": str(self.path)}

    def logout(self):
        if not self.data.get("refresh_token"):
            return {"connected": False, "revoked": False, "note": "本地没有有效连接"}
        # Preserve local credentials on network failure so revocation can be retried.
        with self.open("/oauth/revoke", form={"token": self.data["refresh_token"], "client_id": self.data["client_id"], "token_type_hint": "refresh_token"}) as response:
            response.read(8192)
        atomic_config(self.path, {"format": 1, "origin": self.origin, "resource": self.resource})
        self.data = {"format": 1, "origin": self.origin, "resource": self.resource}
        return {"connected": False, "revoked": True, "origin": self.origin}

    def download(self, resource_id, asset_id, revision, output):
        target = no_symlinks(output)
        if not target.parent.is_dir():
            raise ClientError("下载目录不存在，请先创建目标目录")
        if target.exists():
            raise ClientError("目标文件已存在，请选择新路径；不会覆盖已有文件")
        prepared = self.tool("prepare_download", {"resource_id": resource_id, "asset_id": asset_id, "revision": revision})
        sha = prepared.get("sha256")
        size = prepared.get("size")
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha) or type(size) is not int or size < 0:
            raise ClientError("服务缺少可靠的文件大小或 SHA256，下载已停止")
        url = self.url(prepared.get("url", ""))
        expected_path = "/api/member-agent/v1/resources/" + parse.quote(resource_id, safe="") + "/assets/" + parse.quote(asset_id, safe="")
        parsed = parse.urlsplit(url)
        if parsed.path != expected_path or parse.parse_qs(parsed.query) != {"revision": [str(revision)]}:
            raise ClientError("下载地址与请求的资料、附件或版本不一致")
        fd, temp = tempfile.mkstemp(prefix=".surge-download-", dir=target.parent)
        try:
            os.fchmod(fd, 0o600)
            total, digest = 0, hashlib.sha256()
            with os.fdopen(fd, "wb") as stream, self.open(url, bearer=self.bearer()) as response:
                length = response.headers.get("Content-Length")
                if length is not None and (not length.isdigit() or int(length) != size):
                    raise ClientError("下载响应长度与资料清单不一致")
                while True:
                    chunk = response.read(min(1024 * 1024, max(1, size - total + 1)))
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > size:
                        raise ClientError("下载内容超过预期大小")
                    digest.update(chunk)
                    stream.write(chunk)
                stream.flush()
                os.fsync(stream.fileno())
            if total != size or not hmac.compare_digest(digest.hexdigest(), sha):
                raise ClientError("下载校验失败，未保存为目标文件")
            no_symlinks(target)
            # Atomic no-clobber publication; unlike replace(), this cannot overwrite
            # a file created between the initial check and the finished download.
            os.link(temp, target)
            return {"downloaded": True, "path": str(target), "size": total, "sha256": sha,
                    "resource_id": resource_id, "asset_id": asset_id, "revision": revision}
        except FileExistsError as exc:
            raise ClientError("目标文件已出现，未覆盖已有内容") from exc
        except (HTTPException, OSError) as exc:
            raise ClientError("下载中断或本地文件操作失败，未覆盖目标文件") from exc
        finally:
            if os.path.exists(temp):
                os.unlink(temp)


def parser():
    p = argparse.ArgumentParser(description="SURGE 会员资料与本人任务进度客户端")
    p.add_argument("--config")
    p.add_argument("--license-only", action="store_true", help="使用独立的本人项目授权核验连接")
    p.add_argument("--origin", help="正式站 HTTPS 或显式本机回环 HTTP")
    p.add_argument("--timeout", type=int, default=60)
    sub = p.add_subparsers(dest="command", required=True)
    login = sub.add_parser("login"); login.add_argument("--no-browser", action="store_true"); login.add_argument("--wait", type=int, default=300)
    for name in ("logout", "status", "access", "tasks"):
        sub.add_parser(name)
    search = sub.add_parser("search"); search.add_argument("query"); search.add_argument("--project", dest="project_id"); search.add_argument("--limit", type=int, default=5); search.add_argument("--cursor")
    read = sub.add_parser("read"); read.add_argument("resource_id"); read.add_argument("--section", dest="section_id"); read.add_argument("--revision", type=int); read.add_argument("--offset", type=int); read.add_argument("--limit", type=int); read.add_argument("--section-cursor",dest="section_cursor",type=int)
    workflow = sub.add_parser("workflow"); workflow.add_argument("resource_id"); workflow.add_argument("--revision", type=int)
    download = sub.add_parser("download"); download.add_argument("resource_id"); download.add_argument("asset_id"); download.add_argument("--revision", type=int, required=True); download.add_argument("--output", required=True)
    task=sub.add_parser('task');task.add_argument('task_id')
    start=sub.add_parser('start');start.add_argument('resource_id');start.add_argument('--request-key',required=True);start.add_argument('--question')
    advance=sub.add_parser('advance');advance.add_argument('task_id');advance.add_argument('--expected-version',required=True,type=int);advance.add_argument('--action',choices=['complete','record','restart'],required=True);advance.add_argument('--result')
    ask=sub.add_parser('ask');ask.add_argument('task_id');ask.add_argument('question');ask.add_argument('--expected-version',required=True,type=int)
    verify = sub.add_parser("verify-license")
    verify.add_argument("--project", dest="project_id", choices=("ip-strategist", "agent-motion"), required=True)
    verify.add_argument("--activity", choices=("video_creation", "ip_strategy", "writing", "third_party_service", "team_use", "redistribution", "integration"), required=True)
    verify.add_argument("--platform", required=True)
    verify.add_argument("--account-id", dest="identifier")
    verify.add_argument("--account-url", dest="url")
    verify.add_argument("--certificate", dest="certificate_number")
    verify.add_argument("--pdf", help="只在本地计算 SHA-256，不上传文件")
    return p


def execute(args):
    client = Client(args.config, args.origin, args.timeout)
    command = args.command
    if command == "login":
        if not 1 <= args.wait <= 1800:
            raise ClientError("wait 必须为 1—1800 秒")
        result = client.login(no_browser=args.no_browser, wait=args.wait, scopes=LICENSE_SCOPE if args.license_only else SCOPES)
    elif command == "verify-license":
        if not args.identifier and not args.url:
            raise ClientError("请提供 --account-id 或 --account-url")
        arguments = {"project_id": args.project_id, "activity": args.activity,
                     "account": {k: getattr(args, k) for k in ("platform", "identifier", "url") if getattr(args, k)}}
        if args.certificate_number: arguments["certificate_number"] = args.certificate_number
        if args.pdf:
            if not args.certificate_number: raise ClientError("核对 PDF 时请同时提供 --certificate")
            digest = hashlib.sha256()
            with open(args.pdf, "rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""): digest.update(chunk)
            arguments["pdf_sha256"] = digest.hexdigest()
        result = client.tool("verify_license", arguments)
        if (not isinstance(result, dict) or result.get("schema") != "surge.license-verification/v1" or
                type(result.get("authorized")) is not bool or result.get("project_id") != args.project_id or
                result.get("activity") != args.activity):
            raise ClientError("授权核验响应与本次请求不一致")
        returned_account = result.get("account")
        if not isinstance(returned_account, dict) or any(returned_account.get(k) != v for k, v in arguments["account"].items()):
            raise ClientError("授权核验返回了不同账号")
        result["issuer_origin"] = client.origin
    elif command == "logout": result = client.logout()
    elif command == "status": result = client.status()
    elif command == "access": result = client.tool("get_access")
    elif command == 'tasks':result=client.tool('list_tasks')
    elif command == "download": result = client.download(args.resource_id, args.asset_id, args.revision, args.output)
    else:
        keys = {"search": ("query", "project_id", "limit", "cursor"), "read": ("resource_id", "section_id", "revision", "offset", "limit", "section_cursor"), "workflow": ("resource_id", "revision"),
                'task':('task_id',),'start':('resource_id','request_key','question'),
                'advance':('task_id','expected_version','action','result'),'ask':('task_id','expected_version','question')}[command]
        arguments = {key: getattr(args, key) for key in keys if getattr(args, key) is not None}
        result = client.tool({"search": "search_knowledge", "read": "read_knowledge", "workflow": "get_workflow",
                              'task':'get_task','start':'start_task','advance':'advance_task','ask':'ask_task'}[command], arguments)
    return result

def main(argv=None):
    args = parser().parse_args(argv)
    if args.config is None:
        args.config = str(Path.home() / ".config/surge-member-agent" /
                          ("license.json" if args.license_only else "config.json"))
    try:
        if not 1 <= args.timeout <= 300:
            raise ClientError("timeout 必须为 1—300 秒")
        if args.command == "status":
            result = execute(args)
        else:
            with config_lock(args.config):
                result = execute(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if args.command == "verify-license" and result.get("authorized") is not True else 0
    except (ClientError, OSError) as exc:
        message = str(exc) if isinstance(exc, ClientError) else "本地文件操作失败，请检查目录权限与可用空间"
        print(json.dumps({"ok": False, "error": message, "status": getattr(exc, "status", None)}, ensure_ascii=False), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('{"ok":false,"error":"已取消"}', file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
