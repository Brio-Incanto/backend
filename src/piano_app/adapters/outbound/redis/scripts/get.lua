local revisions_key = KEYS[1]
local state_key = KEYS[2]
local meta_key = KEYS[3]

local keys_count = redis.call(
    'EXISTS', revisions_key, state_key, meta_key
)
if keys_count == 0 then
    return {'not_found'}
end
if keys_count ~= 3 then
    redis.call('DEL', revisions_key, state_key, meta_key)
    return {'corrupt', 'partial_keys'}
end

local cursor, current_version = unpack(redis.call('HMGET', state_key, 'cursor', 'version'))
if not cursor or not current_version then
    redis.call('DEL', revisions_key, state_key, meta_key)
    return {'corrupt', 'partial_state'}
end
local author, title, updated_at, score =
    unpack(redis.call('HMGET', meta_key, 'author', 'title', 'updated_at', 'score'))
if not author or not title or not updated_at or not score then
    redis.call('DEL', revisions_key, state_key, meta_key)
    return {'corrupt', 'partial_meta'}
end

if tonumber(current_version) == nil then
    redis.call('DEL', revisions_key, state_key, meta_key)
    return {'corrupt', 'invalid_version'}
end
cursor = tonumber(cursor)
local revisions_length = redis.call('LLEN', revisions_key)
if cursor == nil or cursor < 0 or cursor >= revisions_length then
    redis.call('DEL', revisions_key, state_key, meta_key)
    return {'corrupt', 'cursor_out_of_range'}
end

return {
    'ok',
    redis.call('LINDEX', revisions_key, cursor),
    current_version,
    author,
    title,
    updated_at,
    score,
}
