#!/usr/bin/env bash
set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
COMPOSE_FILE="docker-compose.yml"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Colors ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

# ── Help ──────────────────────────────────────────────────────────────────────
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --setup   Run full data setup after deploy (downloads backgrounds,"
    echo "            fetches authors/books/quotes). Required on first deploy."
    echo "  --help    Show this message."
    echo ""
    echo "Examples:"
    echo "  First deploy:   ./deploy.sh --setup"
    echo "  Update deploy:  ./deploy.sh"
    echo ""
    echo "Once the database is ready, start the automation with:"
    echo "  ./run_automation.sh"
    exit 0
}

# ── Prerequisites ─────────────────────────────────────────────────────────────
check_deps() {
    info "Checking prerequisites..."
    for cmd in docker git; do
        command -v "$cmd" &>/dev/null || error "'$cmd' is not installed."
    done
    docker compose version &>/dev/null || error "Docker Compose plugin not found. Install it with: apt-get install docker-compose-plugin"
    info "All prerequisites satisfied."
}

# ── .env validation ───────────────────────────────────────────────────────────
check_env() {
    [[ -f "$APP_DIR/.env" ]] || error ".env file not found at $APP_DIR/.env — copy your credentials file before deploying."
    local required_vars=(MYSQL_ROOT_PASSWORD MYSQL_DATABASE MYSQL_USER MYSQL_PASSWORD DB_HOST DB_PORT)
    local missing=()
    # shellcheck source=/dev/null
    source "$APP_DIR/.env"
    for var in "${required_vars[@]}"; do
        [[ -n "${!var:-}" ]] || missing+=("$var")
    done
    [[ ${#missing[@]} -eq 0 ]] || error "Missing required variables in .env: ${missing[*]}"
    info ".env validated."
}

# ── Pull latest code ──────────────────────────────────────────────────────────
pull_code() {
    info "Pulling latest code from git..."
    git -C "$APP_DIR" pull origin main || warn "git pull failed — continuing with current code."
}

# ── Ensure local directories exist ────────────────────────────────────────────
ensure_dirs() {
    mkdir -p \
        "$APP_DIR/logs" \
        "$APP_DIR/Data/media/autor_img" \
        "$APP_DIR/Data/media/backgrounds" \
        "$APP_DIR/Data/media/cover_books" \
        "$APP_DIR/Data/media/post"
    info "Local directories ready."
}

# ── Tear down existing containers and volumes ─────────────────────────────────
teardown() {
    info "Removing existing containers and volumes..."
    docker compose down -v --remove-orphans 2>/dev/null || true
    info "Teardown complete."
}

# ── Build images ──────────────────────────────────────────────────────────────
build() {
    info "Building Docker images..."
    docker compose --profile data-only build --no-cache
    info "Build complete."
}

# ── Start MySQL and wait for healthy ──────────────────────────────────────────
start_db() {
    info "Starting MySQL..."
    docker compose up -d mysql

    info "Waiting for MySQL to be healthy..."
    local attempts=0
    until [[ "$(docker inspect --format='{{.State.Health.Status}}' mysql_quotes_books 2>/dev/null)" == "healthy" ]]; do
        attempts=$((attempts + 1))
        [[ $attempts -gt 30 ]] && error "MySQL did not become healthy after 90s. Run: docker logs mysql_quotes_books"
        echo -n "."
        sleep 3
    done
    echo ""
    info "MySQL is healthy."
}

# ── Initial data setup (backgrounds + authors/books/quotes) ───────────────────
run_setup() {
    info "Running initial data setup — this may take several hours..."
    docker compose --profile data-only run --rm data
    info "Data setup complete."
}

# ── Media HTTP server ─────────────────────────────────────────────────────────
start_media_server() {
    local port=8000
    local serve_dir="$APP_DIR/Data/media/post"
    local log_file="$APP_DIR/logs/media_server.log"
    local pid_file="$APP_DIR/logs/media_server.pid"

    # Kill any existing server on this port
    if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
        info "Stopping existing media server (PID $(cat "$pid_file"))..."
        kill "$(cat "$pid_file")" || true
    fi
    # Kill any stray process on the port (macOS: lsof, Linux: fuser)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        lsof -ti :"$port" 2>/dev/null | xargs kill -9 2>/dev/null || true
    else
        fuser -k "${port}/tcp" 2>/dev/null || true
    fi

    # Start server in background from the post directory
    nohup python3 -m http.server "$port" --directory "$serve_dir" \
        >> "$log_file" 2>&1 &
    echo $! > "$pid_file"
    info "Media server started (PID $!, port $port)."

    # Get public IP (try several providers with fallback)
    local public_ip
    public_ip=$(
        curl -s --max-time 5 ifconfig.me      2>/dev/null ||
        curl -s --max-time 5 icanhazip.com     2>/dev/null ||
        curl -s --max-time 5 api.ipify.org     2>/dev/null ||
        echo ""
    )
    public_ip="${public_ip// /}"   # trim whitespace

    if [[ -z "$public_ip" ]]; then
        warn "Could not determine public IP automatically. Set POST_BASE_URL manually in .env"
        MEDIA_SERVER_URL="http://<YOUR_VM_PUBLIC_IP>:${port}"
    else
        # Wrap IPv6 addresses in brackets for valid URL format
        if [[ "$public_ip" == *:* ]]; then
            MEDIA_SERVER_URL="http://[${public_ip}]:${port}"
        else
            MEDIA_SERVER_URL="http://${public_ip}:${port}"
        fi
        # Update POST_BASE_URL in .env
        if grep -q "^POST_BASE_URL=" "$APP_DIR/.env"; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s|^POST_BASE_URL=.*|POST_BASE_URL=${MEDIA_SERVER_URL}|" "$APP_DIR/.env"
            else
                sed -i "s|^POST_BASE_URL=.*|POST_BASE_URL=${MEDIA_SERVER_URL}|" "$APP_DIR/.env"
            fi
            info "Updated POST_BASE_URL in .env → $MEDIA_SERVER_URL"
        else
            echo "POST_BASE_URL=${MEDIA_SERVER_URL}" >> "$APP_DIR/.env"
            info "Added POST_BASE_URL to .env → $MEDIA_SERVER_URL"
        fi
    fi

    # Register @reboot cron so the server restarts after VM reboot (Linux only)
    if [[ "$OSTYPE" != "darwin"* ]]; then
        local reboot_cmd="@reboot python3 -m http.server $port --directory $serve_dir >> $log_file 2>&1"
        if ! crontab -l 2>/dev/null | grep -q "http.server"; then
            (crontab -l 2>/dev/null || true; echo "$reboot_cmd") | crontab -
            info "Media server registered in crontab (@reboot)."
        fi
    fi
}

# ── Summary ───────────────────────────────────────────────────────────────────
print_summary() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Deploy complete!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "  Media server URL (POST_BASE_URL):"
    echo -e "    ${GREEN}${MEDIA_SERVER_URL:-http://<PUBLIC_IP>:8000}${NC}"
    echo ""
    if ! $RUN_SETUP; then
        echo "  FIRST DEPLOY? Populate the DB now with:"
        echo "    ./deploy.sh --setup"
        echo "  (this downloads backgrounds, authors, books — takes a while)"
        echo ""
    fi
    echo "  Once the DB is ready, start the automation:"
    echo "    ./run_automation.sh"
    echo ""
    echo "  MySQL logs:    docker logs mysql_quotes_books -f"
    echo "  Media server:  tail -f $APP_DIR/logs/media_server.log"
    echo "  Stop all:      docker compose down"
    echo ""
}

# ── Main ──────────────────────────────────────────────────────────────────────
RUN_SETUP=false

for arg in "$@"; do
    case "$arg" in
        --setup) RUN_SETUP=true ;;
        --help)  usage ;;
        *) error "Unknown option: $arg. Use --help for usage." ;;
    esac
done

cd "$APP_DIR"

MEDIA_SERVER_URL=""

info "=== IG Quotes Automation — Deploy ==="
check_deps
check_env
pull_code
ensure_dirs
teardown
build
start_db
start_media_server

if $RUN_SETUP; then
    run_setup
else
    warn "Skipping data setup. Run './deploy.sh --setup' once the DB is ready."
fi

print_summary
