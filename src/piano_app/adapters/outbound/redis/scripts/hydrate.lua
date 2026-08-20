local revisions_key = KEYS[1]
local state_key = KEYS[2]
local meta_key = KEYS[3]

local cursor = ARGV[1]
local version = ARGV[2]
local author_id = ARGV[3]
local title = ARGV[4]
local score = ARGV[5]
local updated_at = ARGV[6]
local ttl_seconds = ARGV[7]
local revisions_start_arg = 8

local keys_count = redis.call(
    'EXISTS', revisions_key, state_key, meta_key
)
if keys_count == 3 then
    return {'exists'}
end
if keys_count ~= 0 then
    redis.call('DEL', revisions_key, state_key, meta_key)
    return {'corrupt', 'partial_keys'}
end

if ARGV[revisions_start_arg] == nil then
    return {'corrupt', 'missing_revisions'}
end

redis.call('RPUSH', revisions_key, unpack(ARGV, revisions_start_arg))
redis.call(
    'HSET',
    state_key,
    'cursor', cursor,
    'version', version
)
redis.call(
    'HSET',
    meta_key,
    'author', author_id,
    'title', title,
    'updated_at', updated_at,
    'score', score
)

redis.call('EXPIRE', revisions_key, ttl_seconds)
redis.call('EXPIRE', state_key, ttl_seconds)
redis.call('EXPIRE', meta_key, ttl_seconds)

return {'ok'}
