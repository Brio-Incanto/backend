-- when committing a new revision, the remaining redo revisions are removed
-- if the number of revisions exceeds the limit, the oldest one is removed
-- A commit still returns not_found after TTL/eviction so the tiered adapter can
-- hydrate from cold.

-- TODO: if the draft vanished between load and commit (TTL/eviction race), this
--  currently fails with DraftStoreNotFoundError, losing the caller's edit
local revisions_key = KEYS[1]
local state_key = KEYS[2]
local meta_key = KEYS[3]

local new_revision = ARGV[1]
local version = ARGV[2]
local max_size = tonumber(ARGV[3])
local ttl_seconds = ARGV[4]

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
if version ~= current_version then
    return {'version_conflict', current_version}
end
cursor = tonumber(cursor)
local revisions_length = redis.call('LLEN', revisions_key)
if cursor == nil or cursor < 0 or cursor >= revisions_length then
    redis.call('DEL', revisions_key, state_key, meta_key)
    return {'corrupt', 'cursor_out_of_range'}
end

redis.call('LTRIM', revisions_key, 0, cursor)
redis.call('RPUSH', revisions_key, new_revision)

if redis.call('LLEN', revisions_key) > max_size then
    redis.call('LTRIM', revisions_key, -max_size, -1)
end

local new_cursor = redis.call('LLEN', revisions_key) - 1
redis.call('HSET', state_key, 'cursor', new_cursor)
local new_version = redis.call('HINCRBY', state_key, 'version', 1)
redis.call('HSET', meta_key, 'updated_at', redis.call('TIME')[1])

redis.call('EXPIRE', revisions_key, ttl_seconds)
redis.call('EXPIRE', state_key, ttl_seconds)
redis.call('EXPIRE', meta_key, ttl_seconds)

return {'ok', new_version}
