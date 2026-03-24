---
name: wechat-mp-skill
description: Use when the agent needs to create, inspect, count, or delete WeChat Official Account drafts, convert Markdown to WeChat-compatible HTML, or troubleshoot 40164, 40001, token cache, and cover upload failures. Do not use for final publish flows, non-WeChat CMS tasks, or advanced custom layout design.
---

# WeChat MP Draft Skill

Create and manage WeChat Official Account drafts with a deterministic flow.
Use this skill to turn source content into a draft, inspect draft state, and recover from the common operational failures around tokens, cover images, and Markdown conversion.

## When To Use

1. Use this skill when the request is about WeChat Official Account draft creation or draft-box operations.
2. Use this skill when the request mentions Markdown-to-WeChat HTML conversion or common WeChat draft API failures such as `40164` or `40001`.
3. Do not use this skill for final publish/release flows, non-WeChat content systems, or custom visual design work.

## Workflow

1. Identify the requested operation.
If the user wants to create a draft, continue to Step 2.
If the user wants to list, count, or delete drafts, skip to Step 6.
If the user asks for troubleshooting only, skip to Step 8.

2. Validate local prerequisites before creating a draft.
Check that `config.yaml` exists and contains `appid` and `appsecret`.
If Markdown input is expected, verify the converter exists at `scripts/convert_markdown_to_wx_html.mjs` and dependencies are installed with `cd scripts && npm ci`.

3. Normalize the input into the supported command contract.
Use the request shapes in `references/command-contract.md`.
If the input contains only a title and no body, treat that as incomplete input and ask for content unless the user explicitly wants the title duplicated as the body.

4. Prepare content for the WeChat draft API.
If the content is already HTML, pass it through unchanged.
If the content is Markdown, run the converter script instead of generating ad-hoc HTML.
If the user provided a cover image, pass its local path or URL through the draft creation flow.

5. Create the draft and report the result.
Run `python3 wechat_mp.py draft --title "..." --content "..."` for CLI flows, or let `handler.py` route the request in chat flows.
Return the title and resulting `media_id`.
If creation fails, continue to Step 8.

6. Handle draft-box management requests deterministically.
For list requests, use `草稿列表` or `查看草稿` semantics and return the formatted list.
For count requests, use `python3 wechat_mp.py count` or the handler count route.
For delete requests, require an explicit `media_id` before deleting.

7. Use progressive disclosure for implementation details.
Read `references/command-contract.md` for supported chat and CLI shapes.
Read `references/troubleshooting.md` only when the request is about failures or recovery.
Read `handler.py` only when you need routing details.
Read `wechat_mp.py` only when you need API, cache, or upload behavior.

8. Troubleshoot by matching the failure mode.
For `40164`, follow the IP whitelist recovery path in `references/troubleshooting.md`.
For `40001`, validate credentials first and then clear `.cache/token_cache.json` if needed.
For cover upload failures, distinguish between missing local files, inaccessible remote URLs, and an empty material library.
For Markdown conversion failures, require Node and the converter dependencies instead of silently degrading output quality.

## Quick Reference

- Create draft: `发布草稿` or `python3 wechat_mp.py draft --title "标题" --content "<p>正文</p>"`
- List drafts: `草稿列表`, `查看草稿`, or `python3 wechat_mp.py list --count 5`
- Count drafts: `草稿数量` or `python3 wechat_mp.py count`
- Delete draft: `删除草稿 MEDIA_ID` or `python3 wechat_mp.py delete --media-id MEDIA_ID`
- Help: `微信草稿帮助` or `草稿帮助`

## Common Mistakes

- Treating this skill as a publish-to-production workflow. It only creates and manages drafts.
- Letting Markdown silently fall back to weak HTML conversion. Use the converter script or fail clearly.
- Relying on the default cover image in production. An empty material library will break draft creation.
- Mixing generic “微信草稿” wording into unrelated chat. Use the exact command phrases when routing matters.

## Validation

- For discovery validation, use `assets/discovery-validation-prompt.txt`.
- For workflow validation, use `assets/logic-validation-prompt.txt`.
- For failure-mode review, use `assets/edge-case-validation-prompt.txt`.

## Files

- Command contract: `references/command-contract.md`
- Failure recovery: `references/troubleshooting.md`
- Discovery validation: `assets/discovery-validation-prompt.txt`
- Workflow validation: `assets/logic-validation-prompt.txt`
- Edge-case validation: `assets/edge-case-validation-prompt.txt`
- Chat router: `handler.py`
- API implementation: `wechat_mp.py`
- Markdown converter: `scripts/convert_markdown_to_wx_html.mjs`
