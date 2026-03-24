# Troubleshooting

Use this file only when the request is about failures, invalid output, or recovery steps.

## 40164: IP Not In Whitelist

1. Confirm the request is going to the official WeChat API from the current machine.
2. Add the current server public IP to the WeChat Official Account console at `开发 -> 基本配置 -> IP 白名单`.
3. Retry `python3 wechat_mp.py test` after the whitelist change propagates.

## 40001: Invalid access_token

1. Verify `config.yaml` contains the correct `appid` and `appsecret`.
2. Delete `.cache/token_cache.json` if credentials are correct but the cached token is stale.
3. Retry `python3 wechat_mp.py test`.

## Markdown Conversion Failure

1. Verify Node is installed.
2. Run `cd scripts && npm ci`.
3. Re-run the conversion flow. Do not silently downgrade to plain HTML generation.

## Cover Image Failure

1. If the caller provided a local path, confirm the file exists.
2. If the caller provided a remote URL, confirm the URL is reachable from the running environment.
3. If no cover was provided, confirm the WeChat material library already has at least one image.
4. Prefer an explicit cover in production instead of relying on the default library fallback.
