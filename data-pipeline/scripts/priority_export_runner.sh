#!/bin/bash
# Priority State Export Runner
# Maintains a pool of exports running continuously overnight

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

PYTHON="/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python"
MAX_CONCURRENT=60
LOG_FILE="logs/priority_runner.log"

# Priority hunting state APIs (in order of importance)
PRIORITY_APIS=(
    # Texas - #1 hunting state
    TX_STATEWIDE TX_STATEWIDE_RECENT TX_HARRIS TX_DALLAS TX_TARRANT TX_BEXAR TX_TRAVIS TX_DENTON TX_WILLIAMSON TX_WILLIAMSON_V2 TX_EL_PASO
    # Wisconsin - #2
    WI_STATEWIDE WI_MILWAUKEE WI_WAUKESHA WI_KENOSHA WI_RACINE WI_BROWN WI_DANE
    # Michigan - #3
    MI_STATEWIDE MI_WAYNE MI_OAKLAND MI_OAKLAND_V2 MI_KENT MI_KENT_V2 MI_MACOMB MI_MACOMB_V2 MI_OTTAWA MI_MARQUETTE MI_WASHTENAW MI_GRAND_TRAVERSE
    # Pennsylvania - #4
    PA_STATEWIDE PA_PASDA_STATEWIDE PA_PHILADELPHIA PA_ALLEGHENY PA_MONTGOMERY PA_BUCKS PA_LANCASTER PA_LANCASTER_V2 PA_BERKS PA_YORK PA_LEHIGH PA_DELAWARE PA_LACKAWANNA
    # Georgia - #5
    GA_FULTON GA_GWINNETT GA_GWINNETT_V2 GA_COBB GA_DEKALB GA_CHEROKEE GA_FORSYTH GA_CHATHAM GA_GLYNN GA_LIBERTY GA_RICHMOND
    # Missouri - #6
    MO_STATEWIDE MO_JACKSON MO_ST_CHARLES MO_ST_CHARLES_V2 MO_CLAY MO_KANSAS_CITY MO_GREENE MO_CHRISTIAN
    # Minnesota - #7
    MN_STATEWIDE MN_HENNEPIN MN_RAMSEY MN_DAKOTA MN_ANOKA
    # Tennessee - #8
    TN_STATEWIDE TN_SHELBY TN_DAVIDSON TN_NASHVILLE TN_KNOX TN_HAMILTON TN_RUTHERFORD TN_MONTGOMERY TN_WILSON
    # New York - #9
    NY_STATEWIDE NY_STATEWIDE_V2 NY_ERIE NY_SUFFOLK NY_WESTCHESTER NY_CENTROIDS
    # Ohio - #10
    OH_STATEWIDE OH_FRANKLIN OH_CUYAHOGA OH_HAMILTON OH_MONTGOMERY OH_SUMMIT OH_SUMMIT_V2 OH_LUCAS
    # Alabama - #11
    AL_STATEWIDE AL_JEFFERSON AL_MOBILE AL_MADISON AL_MADISON_V2 AL_MONTGOMERY
    # Louisiana - #12
    LA_STATEWIDE LA_ORLEANS LA_ORLEANS_V2 LA_JEFFERSON LA_JEFFERSON_V2 LA_EAST_BATON_ROUGE LA_LAFAYETTE
    # Oklahoma - #13
    OK_STATEWIDE OK_OKLAHOMA OK_OKLAHOMA_COUNTY OK_TULSA OK_CLEVELAND
    # Montana - #14
    MT_STATEWIDE MT_STATEWIDE_V2
    # Colorado - #15
    CO_STATEWIDE CO_BOULDER CO_EL_PASO CO_EL_PASO_V2 CO_JEFFERSON CO_ARAPAHOE CO_ARAPAHOE_V2 CO_LARIMER CO_DENVER CO_ADAMS CO_ADAMS_V2 CO_DOUGLAS
)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

get_running_count() {
    ps aux | grep "export_county_parcels.py" | grep -v grep | wc -l | tr -d ' '
}

is_running() {
    ps aux | grep "export_county_parcels.py $1" | grep -v grep | wc -l | tr -d ' '
}

is_completed() {
    local api="$1"
    local filename="parcels_$(echo "$api" | tr '[:upper:]' '[:lower:]').geojson"
    [ -f "output/geojson/$filename" ] && return 0
    return 1
}

launch_export() {
    local api="$1"
    log "Launching: $api"
    nohup $PYTHON scripts/export_county_parcels.py "$api" -o output/geojson > "logs/$(echo "$api" | tr '[:upper:]' '[:lower:]')_auto.log" 2>&1 &
}

log "=========================================="
log "Priority Export Runner Started"
log "Max concurrent: $MAX_CONCURRENT"
log "Total priority APIs: ${#PRIORITY_APIS[@]}"
log "=========================================="

# Main loop
while true; do
    running=$(get_running_count)
    slots_available=$((MAX_CONCURRENT - running))

    if [ $slots_available -gt 0 ]; then
        launched=0
        for api in "${PRIORITY_APIS[@]}"; do
            if [ $launched -ge $slots_available ]; then
                break
            fi

            # Skip if already running
            if [ "$(is_running "$api")" -gt 0 ]; then
                continue
            fi

            # Skip if already completed
            if is_completed "$api"; then
                continue
            fi

            launch_export "$api"
            launched=$((launched + 1))
            sleep 2  # Small delay between launches
        done

        if [ $launched -gt 0 ]; then
            log "Launched $launched new exports. Total running: $((running + launched))"
        fi
    fi

    # Status update every 5 minutes
    log "Status: $running exports running, $(ls output/geojson/*.geojson 2>/dev/null | wc -l) files completed"

    # Check if all done
    all_done=true
    for api in "${PRIORITY_APIS[@]}"; do
        if ! is_completed "$api" && [ "$(is_running "$api")" -eq 0 ]; then
            all_done=false
            break
        fi
    done

    if $all_done; then
        log "All priority exports completed!"
        break
    fi

    sleep 300  # Check every 5 minutes
done

log "Priority Export Runner Finished"
