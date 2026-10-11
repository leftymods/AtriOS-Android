#
# Must be included from activate_adb.sh
#

function print_syntax()
{
    echo "Syntax: $0 {--sound|--quasmodrom|--glagol|--all} {--network} {activate|deactivate|check}"
}

if [ -z "$1" ]; then
    print_syntax
    exit 1
fi

ARG_SOUND=false
ARG_QUASMODROM=false
ARG_GLAGOL=false
ARG_CMD=""
ARG_NETWORK=false

FLAG_NO_READY=3
while [[ $# -gt 0 ]]
do
    key="$1"
    case $key in
        --sound)
            ARG_SOUND=true
            FLAG_NO_READY=$(($FLAG_NO_READY & ~1))
            shift
            ;;
        --quasmodrom)
            ARG_QUASMODROM=true
            FLAG_NO_READY=$(($FLAG_NO_READY & ~1))
            shift
            ;;
        --glagol)
            ARG_GLAGOL=true
            FLAG_NO_READY=$(($FLAG_NO_READY & ~1))
            shift
            ;;
        --all)
            ARG_SOUND=true
            ARG_QUASMODROM=true
            ARG_GLAGOL=true
            FLAG_NO_READY=$(($FLAG_NO_READY & ~1))
            shift
            ;;        
        activate)
            ARG_CMD="activate"
            FLAG_NO_READY=$(($FLAG_NO_READY & ~2))
            shift
            ;;
        deactivate)
            ARG_CMD="deactivate"
            FLAG_NO_READY=$(($FLAG_NO_READY & ~2))
            shift
            ;;
        check)
            ARG_CMD="check"
            FLAG_NO_READY=$(($FLAG_NO_READY & ~3))
            shift
            ;;
        --network)
            ARG_NETWORK=true
            shift
            ;;
        *)
            print_syntax
            exit 1
            ;;
    esac
done

if [ "$FLAG_NO_READY" != "0" ]; then
    print_syntax
    exit
fi

export ARG_SOUND="$ARG_SOUND"
export ARG_QUASMODROM="$ARG_QUASMODROM"
export ARG_GLAGOL="$ARG_GLAGOL"
export ARG_CMD="$ARG_CMD"
export ARG_NETWORK="$ARG_NETWORK"
export ADB_LOG="/data/quasar/quasar_adb.log"
export MARKER_SOUND="/data/quasar_activate_adb_sound"
export MARKER_QUASMODROM="/data/quasar_activate_adb_quasmodrom"
export MARKER_GLAGOL="/data/quasar_activate_adb_glagol"
export MARKER_NETWORK="/data/quasar_activate_network_adb"

if [ -f "${ADB_LOG}" ]; then
	ADB_LOG_SIZE=`(wc -c "${ADB_LOG}" 2> /dev/null || echo 0)| sed -e "s|^\([0-9]*\).*|\1|g"`
	if [ "${ADB_LOG_SIZE}" -gt "2048" ]; then
		mv -f "${ADB_LOG}" "${ADB_LOG}.1"
	fi
fi

if [ "$ARG_CMD" = "activate" ]; then
    if [ "$ARG_NETWORK" = "true" ]; then
        echo "`date`: Set network flag for adb" >> "${ADB_LOG}"
        touch "$MARKER_NETWORK"
    fi

    if [ "$ARG_SOUND" = "true" ]; then
        echo "`date`: Activate adb by sound" >> "${ADB_LOG}"
        touch "$MARKER_SOUND" || exit 1
    fi

    if [ "$ARG_QUASMODROM" = "true" ]; then
        echo "`date`: Activate adb by quasmodrom config" >> "${ADB_LOG}"
        touch "$MARKER_QUASMODROM" || exit 1
    fi

    if [ "$ARG_GLAGOL" = "true" ]; then
        echo "`date`: Activate adb by glagol" >> "${ADB_LOG}"
        touch "$MARKER_GLAGOL" || exit 1
    fi
elif [ "$ARG_CMD" = "check" ]; then
    if [ -f "$MARKER_SOUND" ] || [ -f "$MARKER_QUASMODROM" ] || [ -f "$MARKER_GLAGOL" ]; then
        echo "Activation file exists. Activate adb" >> "${ADB_LOG}"
        ARG_CMD="activate"
        if [ -f "$MARKER_NETWORK" ]; then
            ARG_NETWORK=true
        fi
    else
        exit 0
    fi
else
    if [ -f "$MARKER_NETWORK" ]; then
        echo "`date`: Reset network flag for adb" >> "${ADB_LOG}"
        rm "$MARKER_NETWORK"
    fi

    if [ "$ARG_SOUND" = "true" ]; then
        echo "`date`: Deactivate adb by sound" >> "${ADB_LOG}"
        rm "$MARKER_SOUND"
    fi

    if [ "$ARG_QUASMODROM" = "true" ]; then
        echo "`date`: Deactivate adb by quasmodrom config" >> "${ADB_LOG}"
        rm "$MARKER_QUASMODROM"
    fi

    if [ "$ARG_GLAGOL" = "true" ]; then
        echo "`date`: Deactivate adb by glagol config" >> "${ADB_LOG}"
        rm "$MARKER_GLAGOL"
    fi

    for i in $MARKER_SOUND $MARKER_QUASMODROM $MARKER_GLAGOL; do
    	if [ -f "${i}" ]; then
    		echo "Activation file $i exist. adb still activated";
    		echo "`date`: Activation file $i exist. adb still activated" >> "${ADB_LOG}"
    		exit 0;
    	fi
    done
fi
