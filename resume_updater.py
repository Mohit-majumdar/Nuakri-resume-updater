import logging
import os
import sys
import warnings
from collections.abc import Mapping, Sequence
from logging import config
from pathlib import Path
from configparser import ConfigParser

import requests

warnings.filterwarnings("ignore")


parser = ConfigParser()

try:
    config_file = Path(".").absolute() / "config_properties.conf"
    if config_file.exists():
        parser.read(config_file)
    else:
        raise FileNotFoundError("Config file not found")
except Exception as e:
    print(f"Error in reading config file {e}")
    sys.exit(1)


# Creating log file
LOG_PATH = Path(".").absolute() / "logs"
LOG_PATH.mkdir(exist_ok=True)


CONF_LOG_FILE_PATH = Path(".").absolute() / "log_config.conf"
config.fileConfig(CONF_LOG_FILE_PATH)


USERNAME = parser.get("creds", "Username")
PASSWORD = parser.get("creds", "Password")
RESUME_PATH = parser.get("file", "Resume")
PROFILE_ID = parser.get("profile", "ProfileId", fallback="").strip()

logger = logging.getLogger(__name__)
logger.info("**Start**")

if not Path(RESUME_PATH).exists():
    logger.error("resume not exist")
    sys.exit(1)


def get_tokens():
    logger.info("geting token started")
    url = "https://www.naukri.com/central-login-services/v1/login"
    headers = {
        "Host": "www.naukri.com",
        "Content-Length": "66",
        "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126"',
        "Accept-Language": "en-US",
        "Sec-Ch-Ua-Mobile": "?0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.127 Safari/537.36",
        "Systemid": "jobseeker",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Clientid": "d3skt0p",
        "Cache-Control": "no-cache",
        "Appid": "103",
        "Sec-Ch-Ua-Platform": '"Linux"',
        "Origin": "https://www.naukri.com",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://www.naukri.com/",
        # "Accept-Encoding": "gzip, deflate, br",
        "Priority": "u=1, i",
    }

    # Define the cookies
    cookies = {
        "test": "naukri.com",
        "_t_us": "66F25A4D",
        "_t_s": "seo",
        "_t_sd": "google",
        "_t_r": "1030%2F%2F",
        "persona": "default",
        "_t_ds": "bc37ae51727158861-33bc37ae5-0bc37ae5",
        "J": "0",
        # "ak_bmsc": "31D8F894B95D20939A15618D31BDA06D~000000000000000000000000000000~YAAQBfQwF/uLGxGSAQAAcsywIhmGxQu1+bsOQAmqRfKY0JFBnfpJOZh9GncyC0zY/g0q18NRgJnJJVFS5fo078EaGThQFWvs/Yu7x0SeXnJzGBHCMkki1Kjk1tPCFAV6NYS3NwcpRlgXmaxOJ5NVmSoQNDpOEtbbADrqwaO14/ip1BqRfGQ7bhoZOwgXLW5ws4F+Zct+2996o7lGgPp60iO06pnbTwzTQa2TYxOH2HxzDYXGGuAsfGmgmldQ2pZIDLNeUExdGu8P7f1X1HEsV80FAwobUs2jzzAuDULci5Od0LEAFO3eKF+86FuDD7uLPzylSS1TrjZAsKwoY0i9x1x8wUtuywyPBbeEI9svaJuoqejqJ3wUuz7IDQ36kVPbfIxsk3seUd4wL0lHl/1jo13kqoaCazmg9lBkL3zGY77OsOPON7qrRCzOlCXW7ZAo+yAy1ZKBDxBn0HhL/nA=",
        "_ga": "GA1.1.882075768.1727158844",
        "_gcl_au": "1.1.995618491.1727158845",
        "bm_sv": "18E8DB4693CD4CA2AC338075E5B8C7E9~YAAQBfQwF1aMGxGSAQAAWeCwIhlupcZo3+I0ZADXSMZWxPuf+gT7EVz5Rrhi3JH8jYb7HWjSrCZjVNONTfzqT+kR/CAVffKfi7qQ5ClJIqgaBO4yAWPHpkltnaCYVqY+9LPM3M14Q1qa6e6N6FOckCYMEjWuMTRlPty6qAQ9J1hSGJMjDWyKOyDSz5AiK+BDLyPjpaNYIq+JpM06E7xe9YUMQfGjz05YVpisScx5lqnQBOR2uijOuJLxYL5SnjtT~1",
        "HOWTORT": "cl=1727158930762&r=https%3A%2F%2Fwww.naukri.com%2F&nu=https%3A%2F%2Flogin.naukri.com%2FnLogin%2FLogin.php",
        "_ga_K2YBNZVRLL": "GS1.1.1727158843.1.1.1727158942.60.0.0",
        "_ga_T749QGK6MQ": "GS1.1.1727158845.1.1.1727158942.0.0.0",
    }

    # Define the data to be sent
    data = {
        "username": USERNAME,
        "password": PASSWORD,
    }

    response = requests.post(url, headers=headers, cookies=cookies, json=data)

    if response.status_code == 200:
        logger.info("got tokens")
        response = response.json()

        return {cookie["name"]: cookie["value"] for cookie in response["cookies"]}
    logger.info("unable to get token res: %s", response)
    return {}


def find_profile_id(payload):
    if isinstance(payload, Mapping):
        for key in ("profileId", "profile_id", "profileID"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value

        profiles = payload.get("profiles")
        if isinstance(profiles, Sequence) and not isinstance(profiles, str):
            for profile in profiles:
                if isinstance(profile, Mapping) and (
                    profile.get("isDefault") or profile.get("default") or profile.get("active")
                ):
                    return find_profile_id(profile)
            for profile in profiles:
                profile_id = find_profile_id(profile)
                if profile_id:
                    return profile_id

        for value in payload.values():
            profile_id = find_profile_id(value)
            if profile_id:
                return profile_id

    if isinstance(payload, Sequence) and not isinstance(payload, str):
        for value in payload:
            profile_id = find_profile_id(value)
            if profile_id:
                return profile_id

    return None


def get_profile_id(cookies, headers):
    if PROFILE_ID:
        logger.info("using profile id from config")
        return PROFILE_ID

    urls = [
        "https://www.naukri.com/cloudgateway-mynaukri/resman-aggregator-services/v0/users/self?expand_level=2",
        "https://www.naukri.com/cloudgateway-mynaukri/resman-aggregator-services/v0/users/self/profiles",
    ]

    for url in urls:
        response = requests.get(url, cookies=cookies, headers=headers, verify=False)
        logger.info("profile lookup status %s for %s", response, url)

        if response.status_code != 200:
            logger.info("profile lookup response %s", response.text)
            continue

        profile_id = find_profile_id(response.json())
        if profile_id:
            logger.info("found profile id")
            return profile_id

        logger.info("unable to find profile id in response %s", response.text)

    logger.error("unable to get profile id for logged-in user")
    return None


def vaildate_file():
    logger.info("file validation is started")
    file_path = RESUME_PATH
    file_name = os.path.basename(file_path)

    url = "https://filevalidation.naukri.com/file"
    headers = {
        "Host": "filevalidation.naukri.com",
        "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126"',
        "Accept-Language": "en-US",
        "Sec-Ch-Ua-Mobile": "?0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.127 Safari/537.36",
        "Systemid": "fileupload",
        "Access-Control-Allow-Origin": "*",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Appid": "105",
        "Sec-Ch-Ua-Platform": '"Linux"',
        "Origin": "https://www.naukri.com",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://www.naukri.com/",
        "Accept-Encoding": "gzip, deflate, br",
        "Priority": "u=1, i",
    }
    form_data = {
        "formKey": "F51f8e7e54e205",
        "uploadCallback": "true",
        "fileKey": "UuNpkXe7LOuziK",
        "fileName": file_name,  # Added this line
    }

    files = {"file": (file_name, open(file_path, "rb"), "application/pdf")}
    response = requests.post(url, headers=headers, data=form_data, files=files)

    logger.info("File validate status %s", response)
    logger.info("File validation Response %s", response.text)


def main():
    tokens = get_tokens()
    if not tokens.get("nauk_at"):
        logger.error("login failed, access token not found")
        sys.exit(1)

    vaildate_file()
    cookies = {
        "test": "naukri.com",
        "_t_s": "seo",
        "_t_sd": "google",
        "_t_ds": "bc37ae51727158861-33bc37ae5-0bc37ae5",
        "J": "0",
        "_ga": "GA1.1.882075768.1727158844",
        "_gcl_au": "1.1.995618491.1727158845",
        # "MYNAUKRI[UNID]": "2d49a6af487440e1a12168ea6b696ed1",
        # "ak_bmsc": "EC9800DABCB9B4557730738030BB9A84~000000000000000000000000000000~YAAQNfQwF+DmRcGRAQAAVHVpIxl4GkpdwoElBx2WaQjsEg2RwrqKMFoH0AcodsGGc5TE5+WstkRrsEHZzeWE3iExjPReoCXcRrzIi3D9m0HD6m9g88IPdzl7n0JfrLCWcxiHw23JIqlpshcZMfLG8zQfqq85mN3NmwYGVvb1xSdM/dw7zpODac8hB5KmbIkaemoeEmBz87CvCcQ7BfORNmWdk05qHSMOUKUbae8R1QJFBvRAP/uak6ShYRu64xKXE5nhUPvxfUsxxvO/vqnG3oN5SxmN6GWPdw4LcLRHdGj6DbVqbjY87cjtoczIPsE+M2S0wMY3dUfUQhbQaIJ0IrU6p0nreoFpDHZpbLnAb3e/72XS5zVjDdDkxdwJx+KUJ8gZf8VjjPrfqR54fNc72wvNRulA26rEooQ/764B5+FWSzIXgDHgj6NwpUv7Y+E257i9KXU9NTNn9xx0rjht",
        "_t_r": "1030%2F%2F",
        "persona": "default",
        "nauk_at": tokens.get("nauk_at"),
        "nauk_rt": tokens.get("nauk_rt"),
        "is_login": "1",
        "nauk_sid": tokens.get("nauk_sid"),
        "nauk_otl": tokens.get("nauk_otl"),
        "NKWAP": tokens.get("NKWAP"),
        "_ga_T749QGK6MQ": "GS1.1.1727174886.3.1.1727174901.0.0.0",
        "nauk_ps": "default",
        "_ga_K2YBNZVRLL": "GS1.1.1727174886.4.1.1727174911.35.0.0",
        # "bm_sv": "BB6D3F3616C03E0936DD924E14F93513~YAAQDfQwF37FP9aRAQAAGA2mIxkCCBb3bZ19mxvSWwbOdcQ0gUjMYyOKcv+fpn3oXslNjLAD+r4ib+t9py+07Fjp0SFjmFNPoG8/Pygcv4iWIw+g3lmwWaS+txFXkrm0uw4+XZ4z4pgqAEp2S6yPFCtm0mZ3WtMuFTuJClrwfSGg9X4ofwMVmJzwebSONZNLWUU/s5p8llY3ZIktKu1E5hv1SAAcoBV1bCAkhhPrzA9DtFVEvSL+C90NM+vF4J5M1A==~1",
    }
    headers = {
        "Host": "www.naukri.com",
        # 'Content-Length': '87',
        "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126"',
        "Accept-Language": "en-US",
        "Sec-Ch-Ua-Mobile": "?0",
        "Authorization": f"Bearer {tokens.get('nauk_at')}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.127 Safari/537.36",
        "Systemid": "104",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": "https://www.naukri.com",
        "X-Requested-With": "XMLHttpRequest",
        "Appid": "104",
        "Sec-Ch-Ua-Platform": '"Linux"',
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://www.naukri.com/mnjuser/profile",
        # 'Accept-Encoding': 'gzip, deflate, br',
        "Priority": "u=1, i",
    }
    profile_id = get_profile_id(cookies, headers)
    if not profile_id:
        sys.exit(1)

    headers["X-Http-Method-Override"] = "PUT"
    json_data = {
        "textCV": {
            "formKey": "F51f8e7e54e205",
            "fileKey": "UuNpkXe7LOuziK",
            "textCvContent": None,
        },
    }
    response = requests.post(
        f"https://www.naukri.com/cloudgateway-mynaukri/resman-aggregator-services/v0/users/self/profiles/{profile_id}/advResume",
        cookies=cookies,
        headers=headers,
        json=json_data,
        verify=False,
    )
    logger.info("update file Response status %s", response)
    logger.info("Update file response %s", response.text)


if __name__ == "__main__":
    main()
