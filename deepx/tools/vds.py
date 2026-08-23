import asyncio
import io
import json
import os
import posixpath
import re
import socket
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False


class VDSConnectionPool:
    """Manages persistent SSH and SFTP connections for fast sub-second execution."""

    def __init__(self):
        self._clients: Dict[str, Any] = {}
        self._sftps: Dict[str, Any] = {}

    def _get_key(self, host: str, port: int, username: str) -> str:
        return f"{username}@{host}:{port}"

    def get_client(
        self,
        host: str,
        port: int = 22,
        username: str = "root",
        password: Optional[str] = None,
        key_path: Optional[str] = None,
        key_content: Optional[str] = None,
        passphrase: Optional[str] = None,
        timeout: int = 15,
    ) -> Tuple[Optional[Any], Optional[str]]:
        """Get an existing active SSH connection or establish a new one."""
        if not PARAMIKO_AVAILABLE:
            return None, "Paramiko is not installed in the environment. Please install it with 'pip install paramiko'."

        key = self._get_key(host, port, username)
        client = self._clients.get(key)

        if client is not None:
            transport = client.get_transport()
            if transport is not None and transport.is_active():
                return client, None
            else:
                self.close_connection(host, port, username)

        # Establish new connection
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            connect_kwargs: Dict[str, Any] = {
                "hostname": host,
                "port": int(port),
                "username": username,
                "timeout": timeout,
                "banner_timeout": timeout,
                "auth_timeout": timeout,
                "look_for_keys": True,
                "allow_agent": True,
            }

            if password:
                connect_kwargs["password"] = str(password)

            if key_content:
                pkey = None
                key_io = io.StringIO(key_content.strip())
                for key_cls in (paramiko.RSAKey, paramiko.Ed25519Key, paramiko.ECDSAKey, paramiko.DSSKey):
                    try:
                        key_io.seek(0)
                        pkey = key_cls.from_private_key(key_io, password=passphrase)
                        break
                    except Exception:
                        continue
                if pkey is None:
                    return None, "Failed to parse inline private key content (RSA/Ed25519/ECDSA)."
                connect_kwargs["pkey"] = pkey
            elif key_path:
                expanded_path = os.path.expanduser(os.path.expandvars(key_path))
                if os.path.exists(expanded_path):
                    connect_kwargs["key_filename"] = expanded_path
                else:
                    return None, f"Private key file not found: {key_path}"

            client.connect(**connect_kwargs)
            transport = client.get_transport()
            if transport:
                transport.set_keepalive(15)

            self._clients[key] = client
            return client, None
        except paramiko.AuthenticationException as e:
            return None, f"SSH Authentication failed for {username}@{host}:{port}: {e}"
        except (socket.timeout, TimeoutError):
            return None, f"Connection timed out while connecting to {host}:{port} ({timeout}s)"
        except paramiko.SSHException as e:
            return None, f"SSH connection error to {host}:{port}: {e}"
        except Exception as e:
            return None, f"Failed to connect to {host}:{port}: {e}"

    def get_sftp(
        self,
        host: str,
        port: int = 22,
        username: str = "root",
        password: Optional[str] = None,
        key_path: Optional[str] = None,
        key_content: Optional[str] = None,
        passphrase: Optional[str] = None,
        timeout: int = 15,
    ) -> Tuple[Optional[Any], Optional[str]]:
        """Get an existing active SFTP client or open a new one."""
        client, err = self.get_client(
            host, port, username, password, key_path, key_content, passphrase, timeout
        )
        if err or client is None:
            return None, err

        key = self._get_key(host, port, username)
        sftp = self._sftps.get(key)
        if sftp is not None:
            try:
                sftp.stat(".")
                return sftp, None
            except Exception:
                try:
                    sftp.close()
                except Exception:
                    pass
                self._sftps.pop(key, None)

        try:
            sftp = client.open_sftp()
            self._sftps[key] = sftp
            return sftp, None
        except Exception as e:
            return None, f"Failed to open SFTP session to {host}:{port}: {e}"

    def close_connection(self, host: str, port: int = 22, username: str = "root"):
        key = self._get_key(host, port, username)
        if key in self._sftps:
            try:
                self._sftps[key].close()
            except Exception:
                pass
            self._sftps.pop(key, None)
        if key in self._clients:
            try:
                self._clients[key].close()
            except Exception:
                pass
            self._clients.pop(key, None)

    def close_all(self):
        for sftp in list(self._sftps.values()):
            try:
                sftp.close()
            except Exception:
                pass
        self._sftps.clear()
        for client in list(self._clients.values()):
            try:
                client.close()
            except Exception:
                pass
        self._clients.clear()


_GLOBAL_VDS_POOL = VDSConnectionPool()


class VDSToolsMixin:
    """High-performance VDS / VPS server deployment and remote management tools."""

    @property
    def vds_pool(self) -> VDSConnectionPool:
        return _GLOBAL_VDS_POOL

    def _get_vds_profiles_path(self) -> str:
        base_dir = getattr(self, "cwd", os.getcwd())
        deepx_dir = os.path.join(base_dir, ".deepx")
        os.makedirs(deepx_dir, exist_ok=True)
        return os.path.join(deepx_dir, "vds_profiles.json")

    def _load_vds_profiles(self) -> Dict[str, Dict[str, Any]]:
        path = self._get_vds_profiles_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_vds_profiles(self, profiles: Dict[str, Dict[str, Any]]):
        path = self._get_vds_profiles_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)

    def _resolve_vds_credentials(self, args: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        """Resolve host, port, username, password, and keys from args, profiles, or environment."""
        profile_name = args.get("profile") or args.get("server")
        profiles = self._load_vds_profiles()

        config: Dict[str, Any] = {}
        if profile_name and profile_name in profiles:
            config = dict(profiles[profile_name])
        elif "default" in profiles and not args.get("host"):
            config = dict(profiles["default"])
        elif len(profiles) == 1 and not args.get("host"):
            config = dict(next(iter(profiles.values())))

        # Override with explicit args
        if args.get("host"):
            config["host"] = str(args["host"]).strip()
        if args.get("port"):
            config["port"] = int(args["port"])
        if args.get("username") or args.get("user"):
            config["username"] = str(args.get("username") or args.get("user")).strip()
        if args.get("password") is not None:
            config["password"] = str(args["password"])
        if args.get("key_path") or args.get("key_file"):
            config["key_path"] = str(args.get("key_path") or args.get("key_file"))
        if args.get("key_content"):
            config["key_content"] = str(args["key_content"])
        if args.get("passphrase"):
            config["passphrase"] = str(args["passphrase"])

        # Fallback to environment variables if still missing
        if not config.get("host"):
            config["host"] = os.getenv("VDS_HOST", "").strip()
        if not config.get("username"):
            config["username"] = os.getenv("VDS_USER", os.getenv("VDS_USERNAME", "root")).strip()
        if not config.get("password") and os.getenv("VDS_PASSWORD"):
            config["password"] = os.getenv("VDS_PASSWORD")
        if not config.get("port"):
            env_port = os.getenv("VDS_PORT", "22")
            try:
                config["port"] = int(env_port)
            except ValueError:
                config["port"] = 22
        if not config.get("key_path") and os.getenv("VDS_KEY_PATH"):
            config["key_path"] = os.getenv("VDS_KEY_PATH")

        if not config.get("host"):
            return {}, "No VDS host specified. Provide 'host' in args, save a profile via action='save_profile', or set VDS_HOST in .env."

        config.setdefault("port", 22)
        config.setdefault("username", "root")
        return config, None

    def _sftp_mkdir_p(self, sftp: Any, remote_directory: str):
        """Recursively create remote directory hierarchy via SFTP."""
        parts = []
        path = posixpath.normpath(remote_directory)
        while path and path not in ("/", "."):
            parts.append(path)
            path = posixpath.dirname(path)
        parts.reverse()

        for d in parts:
            try:
                sftp.stat(d)
            except Exception:
                try:
                    sftp.mkdir(d)
                except Exception:
                    pass

    def vds_deploy(self, action: str = None, **kwargs) -> str:
        """Main dispatcher for all VDS and SSH deployment operations."""
        action = (action or kwargs.get("action") or "").strip().lower()
        if not action:
            action = "exec" if kwargs.get("command") else "test_connection"

        # Profile management actions (local only)
        if action == "save_profile":
            name = kwargs.get("name") or kwargs.get("profile") or "default"
            host = kwargs.get("host")
            if not host:
                return "[Error: 'host' is required to save a VDS profile]"
            profiles = self._load_vds_profiles()
            profiles[name] = {
                "host": host,
                "port": int(kwargs.get("port", 22)),
                "username": kwargs.get("username") or kwargs.get("user") or "root",
                "password": kwargs.get("password"),
                "key_path": kwargs.get("key_path") or kwargs.get("key_file"),
            }
            # Clean None values
            profiles[name] = {k: v for k, v in profiles[name].items() if v is not None}
            self._save_vds_profiles(profiles)
            return f"[OK: VDS profile '{name}' saved successfully ({profiles[name].get('username')}@{host}:{profiles[name].get('port')})]"

        elif action == "list_profiles":
            profiles = self._load_vds_profiles()
            if not profiles:
                return "[VDS Profiles: No saved profiles found. You can add one with action='save_profile']"
            lines = ["### Saved VDS Profiles:"]
            for name, p in profiles.items():
                auth_type = "key" if p.get("key_path") else ("password" if p.get("password") else "system agent / default")
                lines.append(f"- **{name}**: `{p.get('username', 'root')}@{p.get('host')}:{p.get('port', 22)}` (Auth: {auth_type})")
            return "\n".join(lines)

        elif action == "remove_profile":
            name = kwargs.get("name") or kwargs.get("profile")
            if not name:
                return "[Error: 'name' or 'profile' is required to remove a profile]"
            profiles = self._load_vds_profiles()
            if name in profiles:
                del profiles[name]
                self._save_vds_profiles(profiles)
                return f"[OK: VDS profile '{name}' removed]"
            return f"[Error: VDS profile '{name}' not found]"

        # Remote actions requiring SSH / SFTP connection
        creds, err = self._resolve_vds_credentials(kwargs)
        if err:
            return f"[Error: {err}]"

        host = creds["host"]
        port = creds["port"]
        username = creds["username"]
        password = creds.get("password")
        key_path = creds.get("key_path")
        key_content = creds.get("key_content")
        passphrase = creds.get("passphrase")
        timeout = int(kwargs.get("timeout", 30))

        if action in ("test", "test_connection", "ping"):
            return self._vds_test_connection(host, port, username, password, key_path, key_content, passphrase, timeout)
        elif action in ("exec", "run", "cmd"):
            return self._vds_exec(host, port, username, password, key_path, key_content, passphrase, timeout, kwargs)
        elif action in ("script", "run_script"):
            return self._vds_script(host, port, username, password, key_path, key_content, passphrase, timeout, kwargs)
        elif action in ("upload", "put"):
            return self._vds_upload(host, port, username, password, key_path, key_content, passphrase, timeout, kwargs)
        elif action in ("download", "get"):
            return self._vds_download(host, port, username, password, key_path, key_content, passphrase, timeout, kwargs)
        elif action in ("write_file", "put_file"):
            return self._vds_write_file(host, port, username, password, key_path, key_content, passphrase, timeout, kwargs)
        elif action in ("edit_file", "patch_file"):
            return self._vds_edit_file(host, port, username, password, key_path, key_content, passphrase, timeout, kwargs)
        elif action in ("read_file", "get_file"):
            return self._vds_read_file(host, port, username, password, key_path, key_content, passphrase, timeout, kwargs)
        elif action in ("service", "systemd"):
            return self._vds_service(host, port, username, password, key_path, key_content, passphrase, timeout, kwargs)
        elif action in ("docker", "compose", "docker_compose"):
            return self._vds_docker(host, port, username, password, key_path, key_content, passphrase, timeout, kwargs)
        elif action in ("quick_deploy", "deploy"):
            return self._vds_quick_deploy(host, port, username, password, key_path, key_content, passphrase, timeout, kwargs)
        elif action in ("sys_info", "status", "info"):
            return self._vds_sys_info(host, port, username, password, key_path, key_content, passphrase, timeout)
        elif action in ("disconnect", "close"):
            self.vds_pool.close_connection(host, port, username)
            return f"[OK: Closed active connection to {username}@{host}:{port}]"
        else:
            return f"[Error: Unknown VDS action '{action}'. Supported actions: test_connection, exec, script, upload, download, write_file, edit_file, read_file, service, docker, quick_deploy, sys_info, save_profile, list_profiles, remove_profile]"

    def _vds_test_connection(
        self, host: str, port: int, username: str, password: Optional[str],
        key_path: Optional[str], key_content: Optional[str], passphrase: Optional[str], timeout: int
    ) -> str:
        start_time = time.time()
        client, err = self.vds_pool.get_client(
            host, port, username, password, key_path, key_content, passphrase, timeout
        )
        if err or client is None:
            return f"[VDS Connection Failed: {err}]"

        latency_ms = int((time.time() - start_time) * 1000)

        # Run quick system check
        try:
            stdin, stdout, stderr = client.exec_command(
                "uname -srm && (cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"' || true) && uptime -p",
                timeout=10,
            )
            out = stdout.read().decode("utf-8", errors="replace").strip().splitlines()
            uname = out[0] if len(out) > 0 else "Linux"
            os_name = out[1] if len(out) > 1 and out[1] else uname
            uptime = out[2] if len(out) > 2 else "running"

            return (
                f"✅ **VDS Connected Successfully!**\n"
                f"• **Target:** `{username}@{host}:{port}`\n"
                f"• **Latency:** `{latency_ms} ms`\n"
                f"• **OS / Distro:** {os_name} ({uname})\n"
                f"• **Uptime:** {uptime}\n"
                f"• **Session:** Active (connection cached for subsequent sub-second operations)"
            )
        except Exception as e:
            return f"✅ VDS Connected (`{username}@{host}:{port}`, latency: {latency_ms} ms), but probe command returned: {e}"

    def _vds_exec(
        self, host: str, port: int, username: str, password: Optional[str],
        key_path: Optional[str], key_content: Optional[str], passphrase: Optional[str], timeout: int,
        kwargs: Dict[str, Any]
    ) -> str:
        command = kwargs.get("command") or kwargs.get("cmd")
        if not command or not str(command).strip():
            return "[Error: 'command' argument is required for action='exec']"

        client, err = self.vds_pool.get_client(
            host, port, username, password, key_path, key_content, passphrase, timeout
        )
        if err or client is None:
            return f"[VDS Connection Error: {err}]"

        cwd = kwargs.get("cwd") or kwargs.get("workdir")
        env = kwargs.get("env") or {}
        sudo = kwargs.get("sudo", False)

        cmd_to_run = str(command).strip()
        if cwd:
            cmd_to_run = f"cd {posixpath.normpath(str(cwd))} && {cmd_to_run}"

        if env and isinstance(env, dict):
            env_prefix = " ".join(f"{k}={json.dumps(str(v))}" for k, v in env.items())
            cmd_to_run = f"export {env_prefix} && {cmd_to_run}"

        if sudo and username != "root":
            cmd_to_run = f"sudo -S -p '' bash -c {json.dumps(cmd_to_run)}"

        start_time = time.time()
        try:
            stdin, stdout, stderr = client.exec_command(cmd_to_run, timeout=timeout, get_pty=bool(sudo))
            if sudo and password:
                stdin.write(f"{password}\n")
                stdin.flush()

            out = stdout.read().decode("utf-8", errors="replace")
            err_out = stderr.read().decode("utf-8", errors="replace")
            exit_code = stdout.channel.recv_exit_status()
            elapsed = round(time.time() - start_time, 2)

            result_parts = []
            if out.strip():
                result_parts.append(out.strip())
            if err_out.strip():
                result_parts.append(f"[STDERR]\n{err_out.strip()}")
            if exit_code != 0:
                result_parts.append(f"[Exit Code: {exit_code}]")

            res_text = "\n\n".join(result_parts) if result_parts else "[OK: Command completed with no output]"
            return f"{res_text}\n\n[Duration: {elapsed}s | Server: {username}@{host}]"
        except socket.timeout:
            return f"[Error: Command timed out after {timeout} seconds on {host}]"
        except Exception as e:
            return f"[Error executing remote command: {e}]"

    def _vds_script(
        self, host: str, port: int, username: str, password: Optional[str],
        key_path: Optional[str], key_content: Optional[str], passphrase: Optional[str], timeout: int,
        kwargs: Dict[str, Any]
    ) -> str:
        script = kwargs.get("script") or kwargs.get("content") or kwargs.get("code")
        if not script or not str(script).strip():
            return "[Error: 'script' argument is required for action='script']"

        sftp, err = self.vds_pool.get_sftp(
            host, port, username, password, key_path, key_content, passphrase, timeout
        )
        if err or sftp is None:
            return f"[VDS SFTP Error: {err}]"

        client, _ = self.vds_pool.get_client(host, port, username, password, key_path, key_content, passphrase, timeout)
        if client is None:
            return "[Error: SSH client unavailable]"

        remote_temp_script = f"/tmp/deepx_run_{int(time.time() * 1000)}.sh"
        try:
            # Upload script
            script_bytes = script.encode("utf-8")
            sftp.putfo(io.BytesIO(script_bytes), remote_temp_script)
            sftp.chmod(remote_temp_script, 0o755)

            # Execute script
            cwd = kwargs.get("cwd")
            sudo = kwargs.get("sudo", False)
            exec_cmd = f"bash -e {remote_temp_script}"
            if cwd:
                exec_cmd = f"cd {posixpath.normpath(str(cwd))} && {exec_cmd}"
            if sudo and username != "root":
                exec_cmd = f"sudo {exec_cmd}"

            start_time = time.time()
            stdin, stdout, stderr = client.exec_command(exec_cmd, timeout=timeout)
            out = stdout.read().decode("utf-8", errors="replace")
            err_out = stderr.read().decode("utf-8", errors="replace")
            exit_code = stdout.channel.recv_exit_status()
            elapsed = round(time.time() - start_time, 2)

            # Cleanup
            try:
                sftp.remove(remote_temp_script)
            except Exception:
                pass

            result_parts = []
            if out.strip():
                result_parts.append(out.strip())
            if err_out.strip():
                result_parts.append(f"[STDERR]\n{err_out.strip()}")
            if exit_code != 0:
                result_parts.append(f"[Exit Code: {exit_code}]")

            res_text = "\n\n".join(result_parts) if result_parts else "[OK: Script executed successfully]"
            return f"{res_text}\n\n[Duration: {elapsed}s | Server: {username}@{host}]"
        except Exception as e:
            try:
                sftp.remove(remote_temp_script)
            except Exception:
                pass
            return f"[Error running remote script: {e}]"

    def _vds_upload(
        self, host: str, port: int, username: str, password: Optional[str],
        key_path: Optional[str], key_content: Optional[str], passphrase: Optional[str], timeout: int,
        kwargs: Dict[str, Any]
    ) -> str:
        local_path = kwargs.get("local_path") or kwargs.get("src")
        remote_path = kwargs.get("remote_path") or kwargs.get("dest")
        if not local_path or not remote_path:
            return "[Error: 'local_path' and 'remote_path' are required for action='upload']"

        local_abs = os.path.abspath(os.path.join(getattr(self, "cwd", os.getcwd()), str(local_path)))
        if not os.path.exists(local_abs):
            return f"[Error: Local path not found: '{local_path}' (resolved: {local_abs})]"

        sftp, err = self.vds_pool.get_sftp(
            host, port, username, password, key_path, key_content, passphrase, timeout
        )
        if err or sftp is None:
            return f"[VDS SFTP Error: {err}]"

        def should_exclude(rel_path: str) -> bool:
            parts = Path(rel_path).parts
            for p in parts:
                if p in (".git", "__pycache__", ".venv", "node_modules", ".idea", ".vscode"):
                    return True
                if p.endswith(".pyc"):
                    return True
            return False

        remote_dest = posixpath.normpath(str(remote_path))
        start_time = time.time()
        file_count = 0
        total_bytes = 0

        try:
            if os.path.isfile(local_abs):
                parent_dir = posixpath.dirname(remote_dest)
                if parent_dir:
                    self._sftp_mkdir_p(sftp, parent_dir)
                # If remote dest is a directory ending with /
                target_file = remote_dest
                if str(remote_path).endswith("/") or str(remote_path).endswith("\\"):
                    self._sftp_mkdir_p(sftp, remote_dest)
                    target_file = posixpath.join(remote_dest, os.path.basename(local_abs))
                sftp.put(local_abs, target_file)
                file_count = 1
                total_bytes = os.path.getsize(local_abs)
            else:
                # Directory upload
                self._sftp_mkdir_p(sftp, remote_dest)
                for root, dirs, files in os.walk(local_abs):
                    rel_dir = os.path.relpath(root, local_abs)
                    if rel_dir != ".":
                        if should_exclude(rel_dir):
                            continue
                        cur_remote_dir = posixpath.join(remote_dest, rel_dir.replace("\\", "/"))
                        self._sftp_mkdir_p(sftp, cur_remote_dir)

                    for file in files:
                        rel_file = os.path.relpath(os.path.join(root, file), local_abs)
                        if should_exclude(rel_file):
                            continue
                        cur_local_file = os.path.join(root, file)
                        cur_remote_file = posixpath.join(remote_dest, rel_file.replace("\\", "/"))
                        cur_remote_dir = posixpath.dirname(cur_remote_file)
                        self._sftp_mkdir_p(sftp, cur_remote_dir)

                        sftp.put(cur_local_file, cur_remote_file)
                        file_count += 1
                        total_bytes += os.path.getsize(cur_local_file)

            elapsed = round(time.time() - start_time, 2)
            size_mb = round(total_bytes / (1024 * 1024), 2)
            return (
                f"✅ **SFTP Upload Completed!**\n"
                f"• **Source:** `{local_path}`\n"
                f"• **Destination:** `{username}@{host}:{remote_dest}`\n"
                f"• **Files Uploaded:** {file_count} ({size_mb} MB)\n"
                f"• **Duration:** {elapsed}s"
            )
        except Exception as e:
            return f"[Error during SFTP upload: {e}]"

    def _vds_download(
        self, host: str, port: int, username: str, password: Optional[str],
        key_path: Optional[str], key_content: Optional[str], passphrase: Optional[str], timeout: int,
        kwargs: Dict[str, Any]
    ) -> str:
        remote_path = kwargs.get("remote_path") or kwargs.get("src")
        local_path = kwargs.get("local_path") or kwargs.get("dest")
        if not remote_path or not local_path:
            return "[Error: 'remote_path' and 'local_path' are required for action='download']"

        local_abs = os.path.abspath(os.path.join(getattr(self, "cwd", os.getcwd()), str(local_path)))
        os.makedirs(os.path.dirname(local_abs), exist_ok=True)

        sftp, err = self.vds_pool.get_sftp(
            host, port, username, password, key_path, key_content, passphrase, timeout
        )
        if err or sftp is None:
            return f"[VDS SFTP Error: {err}]"

        remote_target = posixpath.normpath(str(remote_path))
        start_time = time.time()
        try:
            sftp.get(remote_target, local_abs)
            size_bytes = os.path.getsize(local_abs)
            elapsed = round(time.time() - start_time, 2)
            return (
                f"✅ **SFTP Download Completed!**\n"
                f"• **Remote Source:** `{username}@{host}:{remote_target}`\n"
                f"• **Local File:** `{local_path}` ({size_bytes} bytes)\n"
                f"• **Duration:** {elapsed}s"
            )
        except Exception as e:
            return f"[Error during SFTP download: {e}]"

    def _vds_write_file(
        self, host: str, port: int, username: str, password: Optional[str],
        key_path: Optional[str], key_content: Optional[str], passphrase: Optional[str], timeout: int,
        kwargs: Dict[str, Any]
    ) -> str:
        remote_path = kwargs.get("path") or kwargs.get("remote_path")
        content = kwargs.get("content")
        if not remote_path or content is None:
            return "[Error: 'path' and 'content' are required for action='write_file']"

        sftp, err = self.vds_pool.get_sftp(
            host, port, username, password, key_path, key_content, passphrase, timeout
        )
        if err or sftp is None:
            return f"[VDS SFTP Error: {err}]"

        remote_target = posixpath.normpath(str(remote_path))
        parent = posixpath.dirname(remote_target)
        if parent:
            self._sftp_mkdir_p(sftp, parent)

        try:
            data = content.encode("utf-8")
            sftp.putfo(io.BytesIO(data), remote_target)
            mode = kwargs.get("mode")
            if mode:
                if isinstance(mode, str) and mode.startswith("0o"):
                    mode_int = int(mode, 8)
                else:
                    mode_int = int(mode)
                sftp.chmod(remote_target, mode_int)

            return f"✅ [OK: Written {len(data)} bytes to remote file '{remote_target}' on {username}@{host}]"
        except Exception as e:
            return f"[Error writing remote file: {e}]"

    def _vds_read_file(
        self, host: str, port: int, username: str, password: Optional[str],
        key_path: Optional[str], key_content: Optional[str], passphrase: Optional[str], timeout: int,
        kwargs: Dict[str, Any]
    ) -> str:
        remote_path = kwargs.get("path") or kwargs.get("remote_path")
        if not remote_path:
            return "[Error: 'path' is required for action='read_file']"

        sftp, err = self.vds_pool.get_sftp(
            host, port, username, password, key_path, key_content, passphrase, timeout
        )
        if err or sftp is None:
            return f"[VDS SFTP Error: {err}]"

        remote_target = posixpath.normpath(str(remote_path))
        start_line = int(kwargs.get("start_line", 1))
        end_line = int(kwargs.get("end_line", 500))

        try:
            buf = io.BytesIO()
            sftp.getfo(remote_target, buf)
            buf.seek(0)
            text = buf.read().decode("utf-8", errors="replace")
            lines = text.splitlines()
            total_lines = len(lines)

            slice_lines = lines[max(0, start_line - 1):end_line]
            formatted_lines = [
                f"{i + start_line}: {line}" for i, line in enumerate(slice_lines)
            ]
            content_block = "\n".join(formatted_lines)
            return (
                f"### Remote File: `{remote_target}` ({total_lines} total lines, showing {start_line}-{min(end_line, total_lines)})\n"
                f"```\n{content_block}\n```"
            )
        except FileNotFoundError:
            return f"[Error: Remote file not found: '{remote_target}']"
        except Exception as e:
            return f"[Error reading remote file: {e}]"

    def _vds_edit_file(
        self, host: str, port: int, username: str, password: Optional[str],
        key_path: Optional[str], key_content: Optional[str], passphrase: Optional[str], timeout: int,
        kwargs: Dict[str, Any]
    ) -> str:
        remote_path = kwargs.get("path") or kwargs.get("remote_path")
        target = kwargs.get("target")
        replacement = kwargs.get("replacement")
        if not remote_path or target is None or replacement is None:
            return "[Error: 'path', 'target', and 'replacement' are required for action='edit_file']"

        sftp, err = self.vds_pool.get_sftp(
            host, port, username, password, key_path, key_content, passphrase, timeout
        )
        if err or sftp is None:
            return f"[VDS SFTP Error: {err}]"

        remote_target = posixpath.normpath(str(remote_path))

        try:
            buf = io.BytesIO()
            sftp.getfo(remote_target, buf)
            buf.seek(0)
            text = buf.read().decode("utf-8", errors="replace")

            crlf = "\r\n" in text
            norm_text = text.replace("\r\n", "\n")
            norm_target = str(target).replace("\r\n", "\n")
            norm_replacement = str(replacement).replace("\r\n", "\n")

            if norm_target not in norm_text:
                return f"[Error: target content not found in remote file '{remote_target}']"

            count = norm_text.count(norm_target)
            if count > 1 and not kwargs.get("allow_multiple", False):
                return (
                    f"[Error: target content appears {count} times in remote file '{remote_target}'. "
                    "Please provide a more specific target or set allow_multiple=True]"
                )

            new_text = norm_text.replace(
                norm_target, norm_replacement, 1 if not kwargs.get("allow_multiple", False) else -1
            )
            if crlf:
                new_text = new_text.replace("\n", "\r\n")

            out_buf = io.BytesIO(new_text.encode("utf-8"))
            sftp.putfo(out_buf, remote_target)
            return f"✅ [OK: Successfully edited remote file '{remote_target}' on {username}@{host} ({count} occurrence(s) replaced)]"
        except FileNotFoundError:
            return f"[Error: Remote file not found: '{remote_target}']"
        except Exception as e:
            return f"[Error editing remote file: {e}]"

    def _vds_service(
        self, host: str, port: int, username: str, password: Optional[str],
        key_path: Optional[str], key_content: Optional[str], passphrase: Optional[str], timeout: int,
        kwargs: Dict[str, Any]
    ) -> str:
        service_name = kwargs.get("service") or kwargs.get("name")
        op = kwargs.get("operation") or kwargs.get("op") or "status"
        if not service_name:
            return "[Error: 'service' name is required for action='service']"

        op = op.lower().strip()
        lines = int(kwargs.get("lines", 50))
        sudo_prefix = "sudo " if (username != "root" and kwargs.get("sudo", False)) else ""

        if op in ("start", "stop", "restart", "reload", "enable", "disable"):
            cmd = f"{sudo_prefix}systemctl {op} {service_name} && systemctl status {service_name} --no-pager"
        elif op in ("status", "check"):
            cmd = f"systemctl status {service_name} --no-pager"
        elif op in ("logs", "log", "journal"):
            cmd = f"{sudo_prefix}journalctl -u {service_name} -n {lines} --no-pager"
        elif op in ("daemon_reload", "daemon-reload"):
            cmd = f"{sudo_prefix}systemctl daemon-reload"
        else:
            return f"[Error: Unknown service operation '{op}'. Supported: start, stop, restart, reload, enable, disable, status, logs, daemon-reload]"

        kwargs["command"] = cmd
        return self._vds_exec(host, port, username, password, key_path, key_content, passphrase, timeout, kwargs)

    def _vds_docker(
        self, host: str, port: int, username: str, password: Optional[str],
        key_path: Optional[str], key_content: Optional[str], passphrase: Optional[str], timeout: int,
        kwargs: Dict[str, Any]
    ) -> str:
        op = kwargs.get("operation") or kwargs.get("op") or "ps"
        op = op.lower().strip()
        compose_file = kwargs.get("compose_file") or kwargs.get("file")
        service = kwargs.get("service") or ""

        compose_flag = f"-f {posixpath.normpath(str(compose_file))} " if compose_file else ""

        if op in ("ps", "status"):
            cmd = f"docker compose {compose_flag}ps" if compose_file else "docker ps -a"
        elif op in ("up", "start"):
            cmd = f"docker compose {compose_flag}up -d --build {service}".strip()
        elif op in ("down", "stop"):
            cmd = f"docker compose {compose_flag}down" if compose_file else f"docker stop {service}"
        elif op in ("restart",):
            cmd = f"docker compose {compose_flag}restart {service}".strip() if compose_file else f"docker restart {service}"
        elif op in ("logs", "log"):
            tail = int(kwargs.get("tail", 100))
            cmd = f"docker compose {compose_flag}logs --tail={tail} {service}".strip() if compose_file else f"docker logs --tail={tail} {service}"
        elif op in ("build",):
            cmd = f"docker compose {compose_flag}build {service}".strip()
        elif op in ("prune",):
            cmd = "docker system prune -f"
        else:
            return f"[Error: Unknown docker operation '{op}'. Supported: ps, up, down, restart, logs, build, prune]"

        kwargs["command"] = cmd
        return self._vds_exec(host, port, username, password, key_path, key_content, passphrase, timeout, kwargs)

    def _vds_quick_deploy(
        self, host: str, port: int, username: str, password: Optional[str],
        key_path: Optional[str], key_content: Optional[str], passphrase: Optional[str], timeout: int,
        kwargs: Dict[str, Any]
    ) -> str:
        """End-to-end automated deployment pipeline in one step."""
        local_path = kwargs.get("local_path", ".")
        remote_path = kwargs.get("remote_path")
        if not remote_path:
            return "[Error: 'remote_path' is required for action='quick_deploy' (e.g. /opt/myapp)]"

        build_commands = kwargs.get("build_commands") or kwargs.get("commands") or []
        if isinstance(build_commands, str):
            build_commands = [build_commands]

        service_name = kwargs.get("service")
        docker_compose = kwargs.get("docker_compose", False)
        healthcheck_url = kwargs.get("healthcheck_url")

        report_steps = []

        # Step 1: Upload project files
        report_steps.append("1. **Uploading project files via SFTP...**")
        upload_res = self._vds_upload(
            host, port, username, password, key_path, key_content, passphrase, timeout,
            {"local_path": local_path, "remote_path": remote_path, "exclude": kwargs.get("exclude")}
        )
        if "[Error" in upload_res:
            return f"❌ Quick Deploy Failed at Upload Step:\n{upload_res}"
        report_steps.append("   ✔ Files synchronized successfully.")

        # Step 2: Build / Setup commands
        if build_commands:
            report_steps.append("2. **Executing build / setup commands...**")
            for idx, cmd in enumerate(build_commands, 1):
                res = self._vds_exec(
                    host, port, username, password, key_path, key_content, passphrase, timeout,
                    {"command": cmd, "cwd": remote_path, "sudo": kwargs.get("sudo", False)}
                )
                if "[Exit Code:" in res:
                    return f"❌ Quick Deploy Failed at Build Command Step ({cmd}):\n{res}"
                report_steps.append(f"   ✔ Command #{idx} succeeded: `{cmd}`")

        # Step 3: Service / Docker restart
        if docker_compose:
            report_steps.append("3. **Starting Docker Compose stack...**")
            dock_res = self._vds_docker(
                host, port, username, password, key_path, key_content, passphrase, timeout,
                {"operation": "up", "cwd": remote_path}
            )
            report_steps.append(f"   ✔ Docker status:\n```\n{dock_res}\n```")
        elif service_name:
            report_steps.append(f"3. **Restarting Systemd service `{service_name}`...**")
            srv_res = self._vds_service(
                host, port, username, password, key_path, key_content, passphrase, timeout,
                {"service": service_name, "operation": "restart"}
            )
            report_steps.append(f"   ✔ Service status:\n```\n{srv_res}\n```")

        # Step 4: Healthcheck
        if healthcheck_url:
            report_steps.append(f"4. **Checking healthcheck endpoint `{healthcheck_url}`...**")
            check_res = self._vds_exec(
                host, port, username, password, key_path, key_content, passphrase, 15,
                {"command": f"curl -s -o /dev/null -w '%{{http_code}}' --max-time 10 {healthcheck_url}"}
            )
            report_steps.append(f"   • HTTP Response Code: `{check_res.strip()}`")

        return "🚀 **Quick Deployment Pipeline Succeeded!**\n\n" + "\n".join(report_steps)

    def _vds_sys_info(
        self, host: str, port: int, username: str, password: Optional[str],
        key_path: Optional[str], key_content: Optional[str], passphrase: Optional[str], timeout: int
    ) -> str:
        client, err = self.vds_pool.get_client(
            host, port, username, password, key_path, key_content, passphrase, timeout
        )
        if err or client is None:
            return f"[VDS Connection Error: {err}]"

        sys_cmd = (
            "echo '=== OS & KERNEL ===' && uname -a && cat /etc/os-release 2>/dev/null | grep PRETTY_NAME || true; "
            "echo '=== CPU & LOAD ===' && lscpu 2>/dev/null | grep -E 'Model name|CPU\\(s\\):|CPU MHz' || nproc; uptime; "
            "echo '=== MEMORY USAGE ===' && free -h; "
            "echo '=== DISK SPACE ===' && df -h -x tmpfs -x devtmpfs -x overlay; "
            "echo '=== LISTENING PORTS ===' && (ss -tulpn 2>/dev/null || netstat -tuln 2>/dev/null || true) | head -n 25"
        )
        try:
            stdin, stdout, stderr = client.exec_command(sys_cmd, timeout=15)
            out = stdout.read().decode("utf-8", errors="replace")
            return f"📊 **Remote Server Diagnostics (`{username}@{host}:{port}`)**:\n```\n{out.strip()}\n```"
        except Exception as e:
            return f"[Error fetching remote system info: {e}]"
