"""Per-slot Docker container manager for SaaS-Bench.

Port formula: BASE_PORT + slot_id * slot_offset + app_index
Default:      30000     + slot_id * 20           + app_index

Container naming: rollout_{slot_id}_{app_name}
Compose project:  rollout_{slot_id}_{app_name}
"""

import os
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from string import Template


_BASE_PORT = int(os.environ.get("SAAS_BASE_PORT", 30000))
_SLOT_OFFSET = 40  # 23 apps (index 0-22); 40 gives headroom
_SLOT_PREFIX = os.environ.get("SAAS_SLOT_PREFIX", "rollout")


_TMP_DIR = os.environ.get(
    "SAAS_BENCH_TMP",
    os.path.join(tempfile.gettempdir(), "saas_bench"),
)
os.makedirs(_TMP_DIR, exist_ok=True)

# Repo root = parent of the saas_bench/ package directory.
# Used to resolve {repo_root} in apps.yaml `start` commands and to anchor
# compose template paths declared there.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_READY_OK_STATUSES = {200, 301, 302, 303, 401, 403}
_READY_INTERVAL = 2.0


def _wait_ready(port: int, health_path: str, timeout: int, hostname: str = "localhost") -> float:
    """Poll http://{hostname}:{port}{health_path} until ready or timeout.

    Accepts response statuses in _READY_OK_STATUSES as ready.
    Raises RuntimeError on timeout (caller treats as fatal task failure).
    Returns elapsed seconds when ready.
    """
    url = f"http://{hostname}:{port}{health_path}"
    start = time.time()
    deadline = start + timeout
    last_err = "no probe attempted"
    while time.time() < deadline:
        status = None
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "rollout-probe/1.0"})
            with urllib.request.urlopen(req, timeout=3) as r:
                status = r.status
        except urllib.error.HTTPError as e:
            status = e.code
        except Exception as e:
            last_err = f"{type(e).__name__}: {str(e)[:100]}"
        if status is not None:
            if status in _READY_OK_STATUSES:
                return round(time.time() - start, 1)
            last_err = f"HTTP {status}"
        time.sleep(_READY_INTERVAL)
    elapsed = round(time.time() - start, 1)
    raise RuntimeError(
        f"app on port {port} not ready in {timeout}s "
        f"(probed {url}, last={last_err}, elapsed={elapsed}s)"
    )


class SlotManager:
    def __init__(self, apps_config: dict, slot_id: int):
        self.apps = apps_config
        self.slot_id = slot_id

    # -- Public interface -----------------------------------------------------

    def get_port(self, app: str) -> int:
        return _BASE_PORT + self.slot_id * _SLOT_OFFSET + self.apps[app]["app_index"]

    def get_container_name(self, app: str) -> str:
        return f"{_SLOT_PREFIX}_{self.slot_id}_{app}"

    def get_port_map(self, apps: list[str]) -> dict[str, int]:
        return {app: self.get_port(app) for app in apps}

    def get_pg_port(self, app: str) -> int | None:
        """Return the exposed Postgres port for an app, or None if not configured."""
        offset = self.apps.get(app, {}).get("pg_port_offset")
        if offset is not None:
            return self.get_port(app) + int(offset)
        return None

    def start_apps(self, apps: list[str], hostname: str = "localhost") -> None:
        # Stop any stale containers first (sequentially, fast)
        for app in apps:
            self._stop_one(app)
        # Start all apps in parallel — each polls its own readiness
        with ThreadPoolExecutor(max_workers=len(apps)) as pool:
            futures = {pool.submit(self._start_one, app, hostname): app for app in apps}
            for fut in as_completed(futures):
                fut.result()  # re-raise any exception

    def stop_apps(self, apps: list[str]) -> None:
        for app in apps:
            self._stop_one(app)

    # -- Internal helpers -----------------------------------------------------

    def _start_one(self, app: str, hostname: str) -> None:
        cfg = self._get(app)
        port = self.get_port(app)
        name = self.get_container_name(app)

        print(f"  [slot {self.slot_id}] starting {app} on :{port}...", flush=True)

        if cfg.get("start_type") == "compose":
            self._start_compose(app, cfg, port, name, hostname)
        else:
            # Build extra format vars (e.g. pg_port for Baserow Postgres exposure)
            fmt = dict(container=name, port=port, hostname=hostname, repo_root=_REPO_ROOT)
            pg_offset = cfg.get("pg_port_offset")
            if pg_offset is not None:
                fmt["pg_port"] = port + int(pg_offset)
            cmd = cfg["start"].format(**fmt)
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f"[slot {self.slot_id}] failed to start {app}: {r.stderr.strip()}")

        # Readiness probe (replaces fixed sleep)
        health_path = cfg.get("health_path", "/")
        timeout = cfg.get("startup_wait", 600)
        try:
            elapsed = _wait_ready(port, health_path, timeout, hostname)
            print(f"  [slot {self.slot_id}] {app} ready in {elapsed}s", flush=True)
        except RuntimeError as e:
            ps = subprocess.run(
                f"docker ps -a --filter 'name={name}' --format '{{{{.Names}}}} {{{{.Status}}}}'",
                shell=True, capture_output=True, text=True,
            )
            logs = subprocess.run(
                f"docker logs --tail 20 {name} 2>&1",
                shell=True, capture_output=True, text=True,
            )
            raise RuntimeError(
                f"[slot {self.slot_id}] {app} readiness FAILED: {e}\n"
                f"  docker_ps: {ps.stdout.strip()}\n"
                f"  logs_tail: {logs.stdout[-600:]}"
            ) from e

    def _start_compose(self, app: str, cfg: dict, port: int, prefix: str, hostname: str) -> None:
        tpl_path = cfg["compose_template_file"]
        # resolve relative path from repo root
        if not os.path.isabs(tpl_path):
            here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            tpl_path = os.path.join(here, tpl_path)

        with open(tpl_path) as f:
            content = Template(f.read()).safe_substitute(prefix=prefix, port=port, hostname=hostname)

        tmp = f"{_TMP_DIR}/{prefix}.yml"
        with open(tmp, "w") as f:
            f.write(content)

        cmd = f"docker compose --project-name {prefix} -f {tmp} up -d"
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"[slot {self.slot_id}] compose failed for {app}: {r.stderr.strip()}")

    def _stop_one(self, app: str) -> None:
        cfg = self._get(app)
        prefix = self.get_container_name(app)

        if cfg.get("start_type") == "compose":
            # Stop and remove all containers created by compose (without relying on docker compose down)
            containers = self._compose_containers(app, cfg, prefix)
            for c in containers:
                subprocess.run(
                    f"docker stop {c} 2>/dev/null; docker rm {c} 2>/dev/null",
                    shell=True, capture_output=True, text=True,
                )
            # Remove named volumes
            for suffix in cfg.get("compose_volumes", []):
                vol = f"{prefix}{suffix}"
                subprocess.run(
                    f"docker volume rm {vol} 2>/dev/null",
                    shell=True, capture_output=True, text=True,
                )
            # Remove compose network (naming convention: {project}_{network_in_yaml})
            # Template uses $prefix-net as the network name → actual name = {prefix}_{prefix}-net
            net = f"{prefix}_{prefix}-net"
            subprocess.run(
                f"docker network rm {net} 2>/dev/null",
                shell=True, capture_output=True, text=True,
            )
            # Clean up temporary yml
            tmp = f"{_TMP_DIR}/{prefix}.yml"
            if os.path.exists(tmp):
                os.unlink(tmp)
        else:
            subprocess.run(
                f"docker stop {prefix} 2>/dev/null; docker rm -v {prefix} 2>/dev/null",
                shell=True, capture_output=True, text=True,
            )

    def _compose_containers(self, app: str, cfg: dict, prefix: str) -> list[str]:
        """Parse all container_name fields from the compose template, substituting $prefix."""
        tpl_path = cfg.get("compose_template_file", "")
        if not tpl_path:
            return [prefix]
        if not os.path.isabs(tpl_path):
            here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            tpl_path = os.path.join(here, tpl_path)
        try:
            with open(tpl_path) as f:
                content = f.read()
        except OSError:
            return [prefix]
        names = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("container_name:"):
                raw = stripped.split(":", 1)[1].strip()
                # Substitute $prefix (excluding volume names of the ${prefix}_* form)
                name = raw.replace("$prefix", prefix)
                names.append(name)
        return names if names else [prefix]

    def _get(self, app: str) -> dict:
        if app not in self.apps:
            raise KeyError(f"Unknown app '{app}'. Check rollout/apps.yaml.")
        return self.apps[app]
