"""HuaRunRQ 集成核心逻辑"""
import asyncio
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import logging

DOMAIN = "huarunrq"
PLATFORMS = ["sensor"]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """设置集成的基础结构"""
    # 确保数据结构存在，避免 KeyError
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["loaded_entries"] = set()
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """设置单个配置项"""
    entry_id = config_entry.entry_id
    
    # 确保数据结构存在（双重检查，防止 async_setup 未被调用）
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
        hass.data[DOMAIN]["loaded_entries"] = set()
    
    # 检查配置项是否已加载
    if entry_id in hass.data[DOMAIN]["loaded_entries"]:
        _LOGGER.warning("配置项 %s 已加载，跳过重复设置", entry_id)
        return True
    
    _LOGGER.info("加载配置项 %s (title=%s)", entry_id, config_entry.title)
    
    try:
        # 使用新版API（单数形式）
        if hasattr(hass.config_entries, "async_forward_entry_setup"):
            _LOGGER.debug("使用新版API: async_forward_entry_setup")
            for platform in PLATFORMS:
                await hass.config_entries.async_forward_entry_setup(config_entry, platform)
        else:
            # 旧版API（复数形式）
            _LOGGER.debug("使用旧版API: async_forward_entry_setups")
            await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
        
        # 标记配置项为已加载
        hass.data[DOMAIN]["loaded_entries"].add(entry_id)
        
        _LOGGER.info("配置项 %s 加载成功", entry_id)
        config_entry.async_on_unload(
            config_entry.add_update_listener(async_update_options)
        )
        return True
            
    except Exception as e:
        _LOGGER.exception("配置项加载异常: %s", str(e))
        return False


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """卸载配置项"""
    entry_id = config_entry.entry_id
    _LOGGER.info("卸载配置项 %s", entry_id)
    
    try:
        # 确保数据结构存在
        if DOMAIN not in hass.data or "loaded_entries" not in hass.data[DOMAIN]:
            _LOGGER.warning("尝试卸载未加载的配置项 %s", entry_id)
            return True
        
        # 卸载平台
        unload_tasks = [
            hass.config_entries.async_forward_entry_unload(config_entry, platform)
            for platform in PLATFORMS
        ]
        
        # 等待所有卸载任务完成
        unload_results = await asyncio.gather(*unload_tasks)
        unloaded = all(unload_results)
        
        # 移除已加载标记
        if entry_id in hass.data[DOMAIN]["loaded_entries"]:
            hass.data[DOMAIN]["loaded_entries"].remove(entry_id)
            
        if unloaded and not hass.data[DOMAIN]["loaded_entries"]:
            hass.data.pop(DOMAIN, None)
            
        _LOGGER.info("配置项 %s 卸载 %s", entry_id, "成功" if unloaded else "失败")
        return unloaded
        
    except Exception as e:
        _LOGGER.exception("配置项卸载异常: %s", str(e))
        return False


async def async_update_options(hass: HomeAssistant, config_entry: ConfigEntry):
    """配置更新时重新加载"""
    _LOGGER.info("配置项 %s 已更新，重新加载", config_entry.entry_id)
    await hass.config_entries.async_reload(config_entry.entry_id)
