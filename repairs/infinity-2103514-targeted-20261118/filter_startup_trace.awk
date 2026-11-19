# Input: adb logcat -v threadtime. Output: only structured startup trace fields.
$1 ~ /^[0-9][0-9]-[0-9][0-9]$/ && $2 ~ /^[0-9][0-9]:[0-9][0-9]:[0-9][0-9][.][0-9]+$/ &&
$3 ~ /^[0-9]+$/ && $4 ~ /^[0-9]+$/ && $6 == "Kodi" {
    if (match($0, /InfinityStartupTrace stage=(dispatch[.](fresh|reused)|execute[.]enter|gil[.]acquired|interpreter[.](create|created|returned|failed)|bytecode[.](enter|exception|cancelled_before_entry)|gate[.]checkpoint_closed|execution[.]finished|trace[.]overflow) request=[0-9]+ invoker=-?[0-9]+ tid=[0-9]+ us=[0-9]+ value=-?[0-9]+ flags=[0-9]+ tracked=[0-9]+( addon=[A-Za-z0-9._-]+)?$/)) {
        print $1, $2, $3, $4, substr($0, RSTART, RLENGTH)
        fflush()
    }
}
