"""Constants for the TTLock integration."""

DOMAIN = "javis_lock"
TT_API = "api"
TT_LOCKS = "locks"

OAUTH2_TOKEN = "https://euapi.ttlock.com/oauth2/token"
CONF_WEBHOOK_URL = "webhook_url"
CONF_WEBHOOK_STATUS = "webhook_status"

SIGNAL_NEW_DATA = f"{DOMAIN}.data_received"


CONF_AUTO_UNLOCK = "auto_unlock"
CONF_ALL_DAY = "all_day"
CONF_START_TIME = "start_time"
CONF_END_TIME = "end_time"
CONF_WEEK_DAYS = "days"

SVC_CONFIG_PASSAGE_MODE = "configure_passage_mode"
SVC_CREATE_PASSCODE = "create_passcode"
SVC_CLEANUP_PASSCODES = "cleanup_passcodes"
SVC_LIST_PASSCODES = "list_passcodes"
SVC_LIST_UNLOCK_RECORDS = "list_unlock_records"
SVC_DELETE_PASSCODE = "delete_passcode"
SVC_CHANGE_PASSCODE = "change_passcode"
SVC_UPDATE_LOCK = "update_lock"

HOST1 = "javisco.com"
HOST2 = "javishome.io"
HOST3 = "javiscloud.com"

# SERVER_URL = "https://improved-liger-tops.ngrok-free.app"
SERVER_URL = "https://lock-api."