local revisions_key = KEYS[1]
local state_key = KEYS[2]
local meta_key = KEYS[3]
local author_drafts_key = KEYS[4]

local draft_id = ARGV[1]
local author_id = ARGV[2]
local title = ARGV[3]
local score = ARGV[4]
local initial_revision = ARGV[5]
local ttl_seconds = ARGV[6]

local initial_version = 0
local updated_at = redis.call('TIME')[1]

local keys_count = redis.call(
    'EXISTS', revisions_key, state_key, meta_key
)
if keys_count == 3 then
    return {'exists'}
end
if keys_count ~= 0 then
    redis.call('DEL', revisions_key, state_key, meta_key)
    redis.call('SREM', author_drafts_key, draft_id)
    return {'corrupt', 'partial_keys'}
end

redis.call('RPUSH', revisions_key, initial_revision)
redis.call(
    'HSET',
    state_key,
    'cursor', 0,
    'version', initial_version
)
redis.call(
    'HSET',
    meta_key,
    'author', author_id,
    'title', title,
    'updated_at', updated_at,
    'score', score
)

redis.call('SADD', author_drafts_key, draft_id)

redis.call('EXPIRE', revisions_key, ttl_seconds)
redis.call('EXPIRE', state_key, ttl_seconds)
redis.call('EXPIRE', meta_key, ttl_seconds)

return {'ok', initial_version, updated_at}
