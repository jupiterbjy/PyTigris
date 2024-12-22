# Tigris API Reverse Engineering Memo


## Login

Normal login. Only used to get `siteId`, it's session id doesn't matter much.

Once `siteId` is held - it NEVER CHANGES per company and allow you to login without password. **DO. NOT. LEAK.**


### Request

```json
{
  "method": "POST",
  "url": "https://www.tigrison.com/login",
  "headers": {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
  },
  "body": {
    "siteId": "",
    "timeZoneId": "Asia/Seoul",
    "recaptchaToken": "",
    "loginId": "{EMAIL}",
    "passwd": "{PASSWORD}"
  }
}
```

### Success

```json
{
  "code": 0,
  "message": "성공",
  "data": {
    "siteId": "SITE_ID_NEVER_LEAK_OR_UR_FCKED",
    "sessionId": "SESSION_ID",
    "passwdChangeType": "NONE",
    "emptyInfoYn": "Y",
    "redirect5240Page": "Y",
    "siteWebChatVersion": null
  }
}
```

### Fail

```json
{
  "code": 100,
  "message": "ID 또는 비밀번호가 잘못 되었습니다.",
  "data": null
}
```

---

## Index

Called after login to fetch SSO login URL with hardcoded password. (but won't write here)

This returned URL is *EXTREMELY DANGEROUS* - refer to [`Cloud SSO Login`](#cloud-sso-login)


### Request

Seemingly only `sessionId` is required.

```json
{
  "method": "GET",
  "url": "https://www.tigrison.com/hr/index",
  "cookies": {
    "_tigris_sid": "{SESSION_ID}"
  }
}
```

### Success

```json
{
  "code": 0,
  "message": "성공",
  "data": "https://api.tigris5240.com/cloudSsologinUser.do?siteId={SITE_ID}&userMailId={EMAIL}&loginUserId={EMAIL}&loginPassword={CONSTANT_PASSWORD}&multiLangCd=ko"
}
```


## Cloud SSO Login

This is used to open web interface using URL from previous [`Index`](#index) api response. 

If `siteId`, email, hardcoded password is known, one can **LOGIN AS ANYONE, ANYWHERE WITHOUT PASSWORD**
(What an actual fuck???)

So ***DO. NOT. LEAK.***

### Request

```json
{
  "method": "POST",
  "url": "https://www.tigrison.com/login",
  "params": {
    "siteId": "{SITE_ID}",
    "userMailId": "{EMAIL}",
    "loginUserId": "{EMAIL}",
    "loginPassword": "{CONSTANT_PASSWORD}",
    "multiLangCd": "ko"
  }
}
```

---

## Fetch calender data


### Request

- `searchSYmd`: start time in ISO 8601 format (`YYYY-MM-DDTHH:MM:SS+09:00`)
- `searchEYmd`: end time in ISO 8601 format (`YYYY-MM-DDTHH:MM:SS+09:00`)

```json
{
  "method": "POST",
  "url": "https://api.tigris5240.com/TAADclzVcatnCldrMgr.do",
  "headers": {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
  },
  "cookies": {
    "JSESSIONID": "{SESSION_ID}",
    "colShowYn": "N"
  },
  "params": {
    "cmd": "getTAADclzVcatnCldrMgr"
  },
  "body": {
    "searchSYmd": "{START_TIME}",
    "searchEYmd": "{END_TIME}",
    "cmmSearchOrgCd": "",
    "orgSearchType": "N",
    "searchPosCd": "",
    "searchResCd": ""
  }
}
```

### Success

```json
{
    "Message": "",
    "DATA": [
        {
            "kind": null,
            "title": null,
            "leavNm": null,
            "leavCd": null,
            "personInfo": null,
            "orgCd": null,
            "orgNm": null,
            "posCd": null,
            "posNm": null,
            "resCd": null,
            "resNm": null,
            "wktypeCd": null,
            "wktypeNm": null,
            "staYmd": null,
            "endYmd": null,
            "endYmdAdd": null,
            "agentName": null,
            "allDay": null,
            "staHm": null,
            "endHm": null,
            "reqStatusCd": null,
            "reason": null,
            "note": null
        },
        ...
    ]
}
```


| Parameter Name | Data Type         | Explanation (Speculation)                                                                                                  |
|----------------|-------------------|----------------------------------------------------------------------------------------------------------------------------|
| kind           | String            | The type of event. `vacation` usually                                                                                      |
| title          | String            | Title of the event. Has (△) sign if it's not approved yet                                                                  |
| leavNm         | String            | Name of the vacation in Korean                                                                                             |
| leavCd         | Integer           | Unique identifier for the vacation type                                                                                    |
| personInfo     | String            | Information about the person responsible in `{orgNm}{resNm}{posNm}{wktypeNm}` format. set to `///` if it's global vacation |
| orgCd          | String (nullable) | Organizational code (usually null for global events)                                                                       |
| orgNm          | String (nullable) | Organizational name                                                                                                        |
| posCd          | String (nullable) | Position code (usually null for global events)                                                                             |
| posNm          | String (nullable) | Position name                                                                                                              |
| resCd          | String (nullable) | Resignation code (usually null for global events)                                                                          |
| resNm          | String (nullable) | Resignation name                                                                                                           |
| wktypeCd       | String (nullable) | Work type code                                                                                                             |
| wktypeNm       | String (nullable) | Work type name                                                                                                             |
| staYmd         | String            | Start date of the vacation in YYYY-MM-DD format                                                                            |
| endYmd         | String            | End date of the vacation in YYYY-MM-DD format                                                                              |
| endYmdAdd      | String (nullable) | Immediate day after `endYmd` in YYYY-MM-DD format                                                                          |
| agentName      | String (nullable) | Agent name (usually null for global events)                                                                                |
| allDay         | Boolean           | Whether the vacation is a full-day or half-day                                                                             |
| staHm          | String (nullable) | Start hour of the vacation (usually null for global events)                                                                |
| endHm          | String (nullable) | End hour of the vacation (usually null for global events)                                                                  |
| reqStatusCd    | String (nullable) | Status code indicating whether the request was approved or rejected                                                        |
| reason         | String (nullable) | Reason for taking the vacation (null for global events)                                                                    |
| note           | String (nullable) | Additional information written by requesters (null for global events)                                                      |


### Fail

Redirected to `http://api.tigris5240.com/Error.do?code={ERROR_CODE}`
