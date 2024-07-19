"""Services for javis_lock integration."""
"""Services for javis_lock integration."""

from datetime import datetime, time
import logging

import voluptuous as vol

from homeassistant.const import ATTR_ENTITY_ID, CONF_ENABLED, WEEKDAYS
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.util.dt import as_utc

from .const import (
    CONF_ALL_DAY,
    CONF_AUTO_UNLOCK,
    CONF_END_TIME,
    CONF_START_TIME,
    CONF_WEEK_DAYS,
    DOMAIN,
    SVC_CLEANUP_PASSCODES,
    SVC_CONFIG_PASSAGE_MODE,
    SVC_CREATE_PASSCODE,
    SVC_LIST_PASSCODES,
    SVC_LIST_UNLOCK_RECORDS,
    SVC_DELETE_PASSCODE,
    SVC_CHANGE_PASSCODE
    SVC_LIST_PASSCODES
)
from .coordinator import LockUpdateCoordinator, coordinator_for
from .models import AddPasscodeConfig, OnOff, PassageModeConfig
import traceback
_LOGGER = logging.getLogger(__name__)


class Services:
    """Wraps service handlers."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the service singleton."""
        self.hass = hass

    def register(self) -> None:
        """Register services for javis_lock integration."""
        #tạm thời bỏ lại vì chưa dùng
        # self.hass.services.async_register(
        #     DOMAIN,
        #     SVC_CONFIG_PASSAGE_MODE,
        #     self.handle_configure_passage_mode,
        #     schema=vol.Schema(
        #         {
        #             vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
        #             vol.Required(CONF_ENABLED): cv.boolean,
        #             vol.Optional(CONF_AUTO_UNLOCK, default=False): cv.boolean,
        #             vol.Optional(CONF_ALL_DAY, default=False): cv.boolean,
        #             vol.Optional(CONF_START_TIME, default=time()): cv.time,
        #             vol.Optional(CONF_END_TIME, default=time()): cv.time,
        #             vol.Optional(CONF_WEEK_DAYS, default=WEEKDAYS): cv.weekdays,
        #         }
        #     ),
        #     supports_response=SupportsResponse.OPTIONAL,
        # )
        """Register services for javis_lock integration."""

        #Tạo passcode
        self.hass.services.async_register(
        self.hass.services.async_register(
            DOMAIN,
            SVC_CREATE_PASSCODE,
            self.handle_create_passcode,
            vol.Schema(
            SVC_CONFIG_PASSAGE_MODE,
            self.handle_configure_passage_mode,
            schema=vol.Schema(
                {
                    vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
                    vol.Required("passcode_name"): cv.string,
                    vol.Required("type"): cv.string,
                    vol.Optional("start_time"): cv.datetime,
                    vol.Optional("end_time"): cv.datetime,
                }
                
            ),
            supports_response=SupportsResponse.OPTIONAL,
        )

        #Xóa mã hết hạn
        self.hass.services.async_register(
        self.hass.services.async_register(
            DOMAIN,
            SVC_CLEANUP_PASSCODES,
            self.handle_cleanup_passcodes,
            schema=vol.Schema(
                {
                    vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
                    vol.Required("passcode_name"): cv.string,
                    vol.Required("type"): cv.string,
                    vol.Required("start_time", default=time()): cv.datetime,
                    vol.Required("end_time", default=time()): cv.datetime,
                    
                }
                
            ),
            supports_response=SupportsResponse.OPTIONAL,
        )

        #lấy danh sách passcode
        self.hass.services.async_register(
            DOMAIN,
            SVC_LIST_PASSCODES,
            self.handle_list_passcodes,
            schema=vol.Schema(
                {
                    vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
                }
            ),
            supports_response=SupportsResponse.OPTIONAL,
        )

        #lấy danh sách unlock record
        self.hass.services.async_register(
            DOMAIN,
            SVC_LIST_UNLOCK_RECORDS,
            self.handle_list_unlock_records,
            schema=vol.Schema(
                {
                    vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
                    vol.Required("page_no"): cv.string,
                    vol.Required("page_size"): cv.string,
                }
            ),
            supports_response=SupportsResponse.OPTIONAL,
        )

        #delete passcode
        self.hass.services.async_register(
            DOMAIN,
            SVC_DELETE_PASSCODE,
            self.handle_delete_passcode,
            schema=vol.Schema(
                {
                    vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
                    vol.Required("keyboardPwdId"): cv.string,
                }
            ),
            supports_response=SupportsResponse.OPTIONAL,
        )

        #change passcode
        self.hass.services.async_register(
            DOMAIN,
            SVC_CHANGE_PASSCODE,
            self.handle_change_passcode,
            vol.Schema(
                {
                    vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
                    vol.Required("keyboardPwdId"): cv.string,
                    vol.Optional("keyboardPwdName"): cv.string,
                    vol.Optional("newKeyboardPwd"): cv.string,
                }
                
            ),
            supports_response=SupportsResponse.OPTIONAL,
        )


    def _get_coordinator(self, call: ServiceCall) -> LockUpdateCoordinator:
        _LOGGER.info(f"Call data: {call.data}")
        self.hass.services.async_register(
            DOMAIN,
            SVC_LIST_PASSCODES,
            self.handle_list_passcodes,
            schema=vol.Schema(
                {
                    vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
                }
            ),
            supports_response=SupportsResponse.OPTIONAL,
        )

    def _get_coordinators(self, call: ServiceCall) -> list[LockUpdateCoordinator]:
        _LOGGER.info(f"Call data: {call.data}")
        entity_ids = call.data.get(ATTR_ENTITY_ID)
        _LOGGER.info(f"Entity ids: {entity_ids}")
        coordinator = None
        _LOGGER.info(f"Entity ids: {entity_ids}")
        if entity_ids:
            entity_id = entity_ids[0]
            coordinator = coordinator_for(self.hass, entity_id)
        return coordinator

    # async def handle_configure_passage_mode(self, call: ServiceCall):
    #     """Enable passage mode for the given entities."""
    #     start_time = call.data.get(CONF_START_TIME)
    #     end_time = call.data.get(CONF_END_TIME)
    #     days = [WEEKDAYS.index(day) + 1 for day in call.data.get(CONF_WEEK_DAYS)]

    #     config = PassageModeConfig(
    #         passageMode=OnOff.on if call.data.get(CONF_ENABLED) else OnOff.off,
    #         autoUnlock=OnOff.on if call.data.get(CONF_AUTO_UNLOCK) else OnOff.off,
    #         isAllDay=OnOff.on if call.data.get(CONF_ALL_DAY) else OnOff.off,
    #         startDate=start_time.hour * 60 + start_time.minute,
    #         endDate=end_time.hour * 60 + end_time.minute,
    #         weekDays=days,
    #     )

    #     for coordinator in self._get_coordinator(call):
    #         if await coordinator.api.set_passage_mode(coordinator.lock_id, config):
    #             coordinator.data.passage_mode_config = config
    #             coordinator.async_update_listeners()

    async def handle_create_passcode(self, call: ServiceCall):
        """Create a new passcode for the given entities."""
        try:
            _LOGGER.info(f"Creating passcode for {call.data.get('passcode_name')}")
        try:
            _LOGGER.info(f"Creating passcode for {call.data.get('passcode_name')}")
            start_time_val = call.data.get("start_time")
            start_time_utc = as_utc(start_time_val)
            start_time_ts = start_time_utc.timestamp()
            start_time = start_time_ts * 1000

            if int(call.data.get("type")) <= 2:
                start_time = 0
                end_time = 0
            elif int(call.data.get("type")) == 3:
                if call.data.get("start_time") is None or call.data.get("end_time") is None:
                    return {"error": "Need start time and end time with period passcode."}
                start_time_val = call.data.get("start_time")
                start_time_utc = as_utc(start_time_val)
                start_time_ts = int(start_time_utc.timestamp() / 3600) * 3600
                start_time = start_time_ts * 1000
            end_time_val = call.data.get("end_time")
            end_time_utc = as_utc(end_time_val)
            end_time_ts = end_time_utc.timestamp()
            end_time = end_time_ts * 1000

                end_time_val = call.data.get("end_time")
                end_time_utc = as_utc(end_time_val)
                end_time_ts = int(end_time_utc.timestamp() / 3600) * 3600
                end_time = end_time_ts * 1000
                if start_time >= end_time:
                    return {"error": "Start time must be less than end time."}
            else:
                if call.data.get("start_time") is None or call.data.get("end_time") is None:
                    return {"error": "Need start time and end time with cyclic passcode."}
                start_time_val = call.data.get("start_time")
                start_time_val = datetime.now().replace(hour=start_time_val.hour, minute=start_time_val.minute, second=start_time_val.second)
                start_time_utc = as_utc(start_time_val)
                start_time_ts = int(start_time_utc.timestamp() / 3600) * 3600
                start_time = start_time_ts * 1000
            config = AddPasscodeConfig(
                type=call.data.get("type"),
                passcodeName=call.data.get("passcode_name"),
                startDate=start_time,
                endDate=end_time,
            )
            _LOGGER.info(f"Passcode start create for {config.passcode_name}")
            for coordinator in self._get_coordinators(call):
                _LOGGER.info(f"Passcode start create for {coordinator.lock_id}")
                responce =  await coordinator.api.add_passcode(coordinator.lock_id, config)
                _LOGGER.info(f"Passcode created for {coordinator.lock_id} {responce}")
                return responce
        except Exception as e:
            _LOGGER.error(f"Error creating passcode: {traceback.format_exc()}")

                end_time_val = call.data.get("end_time")
                end_time_val = datetime.now().replace(hour=end_time_val.hour, minute=end_time_val.minute, second=end_time_val.second)
                end_time_utc = as_utc(end_time_val)
                end_time_ts = int(end_time_utc.timestamp() / 3600) * 3600
                end_time = end_time_ts * 1000
                if start_time >= end_time:
                    return {"error": "Start time must be less than end time."}

    async def handle_list_passcodes(self, call: ServiceCall) -> ServiceResponse:
        """List passcode"""
        res = {"list": []}
        for coordinator in self._get_coordinators(call):
            res = await coordinator.api.list_passcodes(coordinator.lock_id, is_parse=False)
        
        return res

            config = AddPasscodeConfig(
                type=call.data.get("type"),
                passcodeName=call.data.get("passcode_name"),
                startDate=start_time,
                endDate=end_time,
            )
            _LOGGER.info(f"Passcode start create for {config.passcode_name}")
            coordinator = self._get_coordinator(call)
            if not coordinator:
                return {"error": "No coordinator found for the given entity."}
            responce =  await coordinator.api.add_passcode(coordinator.lock_id, config)
            return responce
        except Exception as e:
            _LOGGER.error(f"Error creating passcode: {traceback.format_exc()}")
            return {"error": f"Error creating passcode: {traceback.format_exc()}"}

    async def handle_list_passcodes(self, call: ServiceCall) -> ServiceResponse:
        """List passcode"""
        res = {"list": []}
        coordinator = self._get_coordinator(call)
        _LOGGER.info(f"handle_list_passcodes")
        if not coordinator:
            return {"error": "No coordinator found for the given entity."}
        res = await coordinator.api.list_passcodes(coordinator.lock_id, is_parse=False)
        
        return res


    async def handle_cleanup_passcodes(self, call: ServiceCall) -> ServiceResponse:
        """Clean up expired passcodes for the given entities."""
        removed = []
        coordinator = self._get_coordinator(call)
        if not coordinator:
            return {"error": "No coordinator found for the given entity."}
        codes = await coordinator.api.list_passcodes(coordinator.lock_id)
        for code in codes:
            if code.expired:
                await coordinator.api.delete_passcode(coordinator.lock_id, code.id)
                removed.append(code.name)
        return {"removed": removed}

    
    async def handle_list_unlock_records(self, call: ServiceCall) -> ServiceResponse:
        coordinator = self._get_coordinator(call)
        _LOGGER.info(f"handle_list_unlock_records")
        if coordinator:
            return await coordinator.api.list_unlock_records(coordinator.lock_id, int(call.data.get("page_no")), int(call.data.get("page_size")))
        return {"error": "No coordinator found for the given entity."}
    
    
    async def handle_delete_passcode(self, call: ServiceCall) -> ServiceResponse:
        coordinator = self._get_coordinator(call)
        _LOGGER.info(f"handle_list_unlock_records")
        res = {"error": "Delete passcode fail."}
        if coordinator:
            res = await coordinator.api.delete_passcode(coordinator.lock_id, int(call.data.get("keyboardPwdId")))
        return res
    
    async def handle_change_passcode(self, call: ServiceCall) -> ServiceResponse:
        coordinator = self._get_coordinator(call)
        _LOGGER.info(f"handle_change_passcode")
        res = {"error": "Change passcode fail."}
        if call.data.get("newKeyboardPwd") is None and call.data.get("keyboardPwdName") is None:
            return {"error": "New passcode or passcode name is required."}
        if coordinator:
            res = await coordinator.api.change_passcode(coordinator.lock_id, 
                                                               int(call.data.get("keyboardPwdId")), 
                                                               call.data.get("newKeyboardPwd") if call.data.get("newKeyboardPwd") else "",
                                                                 call.data.get("keyboardPwdName") if call.data.get("keyboardPwdName") else "")
        return res