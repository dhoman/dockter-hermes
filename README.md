# Dockter Hermes

If you are like me and want to run [Hermes Agent](https://github.com/NousResearch/hermes-agent) on your computer but don't want to give it barebones access to your computer and want to run it with Docker this project is for you. If you are also like me and also want to be able to access your agent from other computers but are scared of how to properly do it without exposing it to the entire internet this project is also for you as we make it a lot easier to setup with [tailscale](https://github.com/tailscale/tailscale) (ie your own private network on the web.)

This is a both a sample of a docker compose, and a script for common docker commands (so you don't have to memorize long parameter driven docker commands to do the simpliest things for your hermes agent (ie start, stop, rebuild, debug logs, run shell commands in gateway / dashboard, etc.)

And is also a [tailscale](https://github.com/tailscale/tailscale) reverse proxy.

Small shell helpers for running  with Docker Compose.

Dockter Hermes keeps the Hermes checkout untouched. Local machine settings live in `~/.hermes/dockter-hermes`, and the helper composes them with the upstream `docker-compose.yml`.

## Install

Clone [dhoman/dockter-hermes](https://github.com/dhoman/dockter-hermes) to:

```sh
mkdir -p ~/.hermes
git clone https://github.com/dhoman/dockter-hermes ~/.hermes/dockter-hermes
```

If you copied the files manually instead of cloning, make the helper executable:

```sh
chmod +x ~/.hermes/dockter-hermes/dockter-hermes-helpers.sh
```

Add the helper to your shell profile.

For Zsh:

```sh
echo 'source ~/.hermes/dockter-hermes/dockter-hermes-helpers.sh' >> ~/.zshrc
```

For Bash:

```sh
echo 'source ~/.hermes/dockter-hermes/dockter-hermes-helpers.sh' >> ~/.bashrc
```

Then open a new terminal, or load it in the current one:

```sh
source ~/.hermes/dockter-hermes/dockter-hermes-helpers.sh
```

## Configure

Dockter Hermes needs to know where your local `hermes-agent` checkout lives. It auto-detects common locations, or you can create `config` from the example:

```sh
cp ~/.hermes/dockter-hermes/config.example ~/.hermes/dockter-hermes/config
```

Edit `~/.hermes/dockter-hermes/config`:

```sh
DOCKTER_HERMES_DIR="/path/to/hermes-agent"
```

Optional Docker Compose overrides can be created from the example:

```sh
cp ~/.hermes/dockter-hermes/docker-compose.override.example.yml \
  ~/.hermes/dockter-hermes/docker-compose.override.yml
```

The live `config` and `docker-compose.override.yml` files are intentionally ignored by git.

## Quickstart

```sh
dockter-hermes-setup
dockter-hermes-start
dockter-hermes-dashboard
```

Open:

```text
http://127.0.0.1:9119/
```

To use a different dashboard port:

```sh
export DOCKTER_HERMES_DASHBOARD_PORT=9123
dockter-hermes-start
```

## Commands

### Basic Operations

| Command | Description |
| --- | --- |
| `dockter-hermes-start [gateway\|dashboard\|all]` | Start containers. Defaults to `all`. |
| `dockter-hermes-stop` | Stop the compose stack. |
| `dockter-hermes-restart [gateway\|dashboard\|all]` | Restart containers. Defaults to `gateway`. |
| `dockter-hermes-status` | Check compose status and Hermes-looking Docker containers. |
| `dockter-hermes-logs [gateway\|dashboard\|all] [docker logs args]` | View live logs. Defaults to `gateway`. |

### Container Access

| Command | Description |
| --- | --- |
| `dockter-hermes-shell [gateway\|dashboard]` | Open a Bash shell in a container. Defaults to `gateway`. |
| `dockter-hermes-exec [gateway\|dashboard] <command>` | Run a command inside a running container. Defaults to `gateway`, the primary control-plane service. |
| `dockter-hermes-oneoff <args>` | Run `hermes` arguments in a temporary gateway container created with `docker compose run --rm`; the container stops after the command exits. |
| `dockter-hermes-chat` | Open interactive Hermes chat through the gateway container. |
| `dockter-hermes-setup` | Run the Hermes setup wizard in a one-off gateway container. |

`dockter-hermes-exec` is the command you will likely use most. Any `hermes` command from the Hermes docs can be run inside the gateway container by prefixing it with `dockter-hermes-exec`:

```sh
dockter-hermes-exec hermes profile create recipe-helper --description "Weeknight dinner ideas"
```

Keep the `hermes` in the command, since `exec` runs exactly what you pass it. Commands run as your host uid (the same user the gateway runs as), not root; use `dockter-hermes-shell` if you need a root shell. If the stack is not running, use `dockter-hermes-oneoff` instead and drop the leading `hermes` (for example, `dockter-hermes-oneoff profile list`).

### Dashboard and Health

| Command | Description |
| --- | --- |
| `dockter-hermes-dashboard` | Start the dashboard and open `http://127.0.0.1:9119/`. |
| `dockter-hermes-health` | Run `hermes gateway status --deep`, with HTTP health fallback when available. |

### Config and Navigation

| Command | Description |
| --- | --- |
| `dockter-hermes-cd` | Jump to the Hermes Agent project directory. |
| `dockter-hermes-config` | Print Dockter Hermes helper config. |
| `dockter-hermes-config get [key]` | Print a Hermes config value (`hermes config get` inside Docker). |
| `dockter-hermes-config set <key> <value>` | Set a Hermes config value (`hermes config set` inside Docker). |
| `dockter-hermes-config <subcommand>` | Any other `hermes config` subcommand: `unset`, `show`, `path`, `check`, `migrate`, ... |
| `dockter-hermes-home` | Jump to the Hermes data directory. |
| `dockter-hermes-workspace` | Jump to the Hermes workspace directory. |
| `dockter-hermes-show-config` | Print Hermes app config and env files with secrets redacted. |
| `dockter-hermes-help` | Show all available commands. |

### Maintenance

| Command | Description |
| --- | --- |
| `dockter-hermes-update` | Pull latest source, rebuild the gateway image, and recreate containers. |
| `dockter-hermes-rebuild [gateway\|dashboard\|all]` | Rebuild the gateway image and force-recreate containers. Defaults to `all`. |
| `dockter-hermes-clean` | Remove compose containers and volumes after confirmation. |

## Configuration Files

Dockter Hermes stores helper state under:

```sh
${HERMES_HOME:-~/.hermes}/dockter-hermes
```

The helper loads Docker Compose files in this order:

1. `${DOCKTER_HERMES_DIR}/docker-compose.yml`
2. `${DOCKTER_HERMES_DIR}/docker-compose.extra.yml`, when present
3. `${HERMES_HOME:-~/.hermes}/dockter-hermes/docker-compose.override.yml`, when present

Useful environment variables:

| Variable | Purpose |
| --- | --- |
| `DOCKTER_HERMES_DIR` | Path to the local `hermes-agent` checkout. |
| `HERMES_HOME` | Host Hermes data directory. Defaults to `~/.hermes`. |
| `HERMES_UID` | UID passed into Docker Compose. Defaults to `id -u`. |
| `HERMES_GID` | GID passed into Docker Compose. Defaults to `id -g`. |
| `DOCKTER_HERMES_DOCKER_BIN` | Docker executable path. Auto-detects common macOS locations. |
| `DOCKTER_HERMES_DASHBOARD_PORT` | Dashboard port. Defaults to `9119`. |
| `DOCKTER_HERMES_WAIT_TIMEOUT` | Seconds `dockter-hermes-restart` waits for containers to be running. Defaults to `60`. |
| `DOCKTER_HERMES_API_PORT` | Gateway API health-check port. Defaults to `8642`. |
| `DOCKTER_HERMES_GATEWAY_CONTAINER` | Gateway container name for direct `docker exec` health checks. Defaults to `hermes`. |
| `DOCKTER_HERMES_DASHBOARD_CONTAINER` | Dashboard container name. Defaults to `hermes-dashboard`. |
| `HERMES_PREFIX_PROXY_PREFIX` | Public path prefix for the optional prefix proxy. Defaults to `/hermes`. |
| `HERMES_PREFIX_PROXY_PORT` | Local prefix proxy port. Defaults to `9120`. |
| `HERMES_PREFIX_PROXY_TARGET` | Backend dashboard URL for the prefix proxy. Defaults to `http://127.0.0.1:${DOCKTER_HERMES_DASHBOARD_PORT:-9119}` in the example compose file. |

## Tailscale Serve With `/hermes`

Hermes Dashboard can be exposed privately on a Tailnet with Tailscale Serve.

If you want Hermes to live at a path prefix such as `/hermes`, use the included prefix proxy from `docker-compose.override.example.yml`. By default it listens locally on `127.0.0.1:9120`, forwards to the Hermes dashboard on `127.0.0.1:9119`, strips `/hermes`, and adds:

```text
X-Forwarded-Prefix: /hermes
```

That header lets Hermes generate prefixed redirects, cookies, assets, API URLs, and websocket URLs.

Example Tailscale command:

```sh
tailscale serve --bg --set-path /hermes http://127.0.0.1:9120
```

If you change the prefix proxy port, use that port in the Tailscale command:

```sh
export HERMES_PREFIX_PROXY_PORT=9124
tailscale serve --bg --set-path /hermes http://127.0.0.1:9124
```

If you also serve another local app:

```sh
tailscale serve --bg --set-path /openclaw http://127.0.0.1:3200
tailscale serve status
```

Before exposing the dashboard beyond localhost, enable Hermes dashboard authentication in `~/.hermes/config.yaml`.

### How to enable Hermes dashboard authentication

Hermes includes a username/password dashboard auth provider. Configure it under the `dashboard.basic_auth` block:

```yaml
dashboard:
  basic_auth:
    username: "your-username"
    password_hash: "scrypt$..."
    password: ""
    secret: "random-session-signing-secret"
    session_ttl_seconds: 43200
```

Fields:

| Field | Purpose | How to set it |
| --- | --- | --- |
| `username` | Username for the dashboard login page. | Pick any username. |
| `password_hash` | Scrypt hash of your dashboard password. | Generate it with the command below. Do not store your plaintext password. |
| `password` | Plaintext password fallback. | Leave this as `""` when using `password_hash`. |
| `secret` | Random key used to sign browser login sessions. This is not your password and not a password hint. | Generate it with `openssl rand -base64 32`. |
| `session_ttl_seconds` | How long dashboard login sessions last. | Common values: `3600` = 1 hour, `43200` = 12 hours, `86400` = 24 hours, `604800` = 7 days. |

Generate a password hash:

```sh
docker exec -it hermes-dashboard python -c 'from plugins.dashboard_auth.basic import hash_password; import getpass; p=getpass.getpass("New dashboard password: "); q=getpass.getpass("Repeat dashboard password: "); assert p == q, "passwords did not match"; print(hash_password(p))'
```

Generate the session-signing secret:

```sh
openssl rand -base64 32
```

Then edit `~/.hermes/config.yaml`:

```yaml
dashboard:
  basic_auth:
    username: "your-username"
    password_hash: "scrypt$32768$8$1$..."
    password: ""
    secret: "paste-output-from-openssl-here"
    session_ttl_seconds: 43200
```

Verify that your password matches the stored hash:

```sh
docker exec -it hermes-dashboard python -c 'from hermes_cli.config import cfg_get, load_config; from plugins.dashboard_auth.basic import _verify_password; import getpass; b=cfg_get(load_config(),"dashboard","basic_auth",default={}); print("username:", b.get("username")); print("password ok:", _verify_password(getpass.getpass("Password to test: "), b.get("password_hash","")))'
```

Expected output:

```text
username: your-username
password ok: True
```

Restart the dashboard after changing `config.yaml`:

```sh
dockter-hermes-restart dashboard
```


## Common Workflows

Update Hermes Agent:

```sh
dockter-hermes-update
```

Rebuild without pulling:

```sh
dockter-hermes-rebuild
```

View logs:

```sh
dockter-hermes-logs
dockter-hermes-logs dashboard
```

Open a shell:

```sh
dockter-hermes-shell
dockter-hermes-shell dashboard
```

Print helper config:

```sh
dockter-hermes-config
```

Get and set Hermes app config values:

```sh
dockter-hermes-config get model
dockter-hermes-config set terminal.backend docker
dockter-hermes-config unset terminal.backend
```

These run `hermes config ...` in the running gateway container, or in a temporary container if the gateway is stopped. Restart services after a change with `dockter-hermes-restart all`.

Print Hermes app config with secrets redacted:

```sh
dockter-hermes-show-config
```

## Requirements

- Docker with Docker Compose
- Bash or Zsh
- A local Hermes Agent checkout with `docker-compose.yml`
- Tailscale, only if you want Tailnet access

## Development

Run the helper tests:

```sh
./test-dockter-hermes-helpers.sh
```

Test with fresh helper config:

```sh
unset DOCKTER_HERMES_DIR
rm -f "${HERMES_HOME:-$HOME/.hermes}/dockter-hermes/config"
source ~/.hermes/dockter-hermes/dockter-hermes-helpers.sh
dockter-hermes-start
```
