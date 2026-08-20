-- KEYS[1] is the author's draft-id SET; every following triple of KEYS
-- (grouped 3-per-draft, in the same order as ARGV) is that draft's own
-- revisions/state/meta keys, built by the caller
local author_drafts_key = KEYS[1]
local rows = {}

local function process_draft(draft_id, revisions_key, state_key, meta_key)
    local keys_count = redis.call('EXISTS', revisions_key, state_key, meta_key)
    if keys_count ~= 3 then
        redis.call('DEL', revisions_key, state_key, meta_key)
        redis.call('SREM', author_drafts_key, draft_id)
        return
    end

    local cursor, current_version = unpack(redis.call('HMGET', state_key, 'cursor', 'version'))
    if not cursor or not current_version then
        redis.call('DEL', revisions_key, state_key, meta_key)
        redis.call('SREM', author_drafts_key, draft_id)
        return
    end

    local author, title, updated_at, score =
        unpack(redis.call('HMGET', meta_key, 'author', 'title', 'updated_at', 'score'))
    if not author or not title or not updated_at or not score then
        redis.call('DEL', revisions_key, state_key, meta_key)
        redis.call('SREM', author_drafts_key, draft_id)
        return
    end

    table.insert(rows, draft_id)
    table.insert(rows, author)
    table.insert(rows, title)
    table.insert(rows, updated_at)
    table.insert(rows, score)
end

for i, draft_id in ipairs(ARGV) do
    local base = (i - 1) * 3
    process_draft(draft_id, KEYS[base + 2], KEYS[base + 3], KEYS[base + 4])
end

return {'ok', unpack(rows)}
