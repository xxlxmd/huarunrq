# custom_components/huaruirq/const.py
DOMAIN = "huaruirq"
DATA_SCHEMA = vol.Schema({  # 根据需要定义
    vol.Required("cno"): str,
})