#!/usr/bin/env bash
set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
COMPOSE_FILE="docker-compose.yml"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_TZ="Europe/Dublin"
CRON_SCHEDULE_MORNING="0 8  * * *"   # 08:00 Dublin time
CRON_SCHEDULE_EVENING="0 18 * * *"   # 18:00 Dublin time

# ── Colors ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

# ── Prerequisites ─────────────────────────────────────────────────────────────
check_deps() {
    for cmd in docker; do
        command -v "$cmd" &>/dev/null || error "'$cmd' is not installed."
    done
    docker compose version &>/dev/null || error "Docker Compose plugin not found."
}

# ── Check MySQL is running ────────────────────────────────────────────────────
check_db() {
    local status
    status="$(docker inspect --format='{{.State.Health.Status}}' mysql_quotes_books 2>/dev/null || true)"
    [[ "$status" == "healthy" ]] || error "MySQL is not running or not healthy. Run './deploy.sh' first."
    info "MySQL is healthy."
}

# ── Run automation once immediately ──────────────────────────────────────────
run_now() {
    info "Running main_automation.py now..."
    docker compose --profile data-only run --rm data python main_automation.py
    info "Automation run complete."
}

# ── Install cron jobs (08:00 and 18:00 Dublin time) ───────────────────────────
setup_cron() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        warn "Cron setup skipped on macOS (run this on the Ubuntu VM for scheduling)."
        return
    fi

    local log_file="$APP_DIR/logs/automation.log"
    local cron_cmd="cd $APP_DIR && docker compose --profile data-only run --rm data python main_automation.py >> $log_file 2>&1"

    if crontab -l 2>/dev/null | grep -q "main_automation.py"; then
        warn "Cron jobs already exist — skipping. Edit with: crontab -e"
        return
    fi

    # CRON_TZ makes cron interpret the schedules in Dublin time (handles DST automatically)
    (
        crontab -l 2>/dev/null
        echo "CRON_TZ=$CRON_TZ"
        echo "$CRON_SCHEDULE_MORNING $cron_cmd"
        echo "$CRON_SCHEDULE_EVENING $cron_cmd"
    ) | crontab -

    info "Cron jobs installed (timezone: $CRON_TZ):"
    info "  Morning → 08:00 Dublin"
    info "  Evening → 18:00 Dublin"
}

# ── Summary ───────────────────────────────────────────────────────────────────
print_summary() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Automation active!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "  Schedule:      08:00 and 18:00 (Europe/Dublin)"
    echo "  Logs:          tail -f $APP_DIR/logs/automation.log"
    echo "  Edit schedule: crontab -e"
    echo "  View cron:     crontab -l"
    echo ""
}

# ── Main ──────────────────────────────────────────────────────────────────────
cd "$APP_DIR"

info "=== IG Quotes Automation — Start ==="
check_deps
check_db
run_now
setup_cron
print_summary
