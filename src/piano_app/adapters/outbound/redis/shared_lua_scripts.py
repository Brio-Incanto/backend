# Lua scripts are used to achieve atomicity of operations on Redis.
#
# Used by BOTH RedisDraftHistory and RedisDraftCache (load/commit/undo/redo are
# identical hot-tier mechanics regardless of which port a class satisfies) —
# scripts owned by only one of them live in that adapter's own file instead
# (RedisDraftHistory: _CREATE_SCRIPT; RedisDraftCache: _HYDRATE_SCRIPT /
# _LOAD_SNAPSHOT_SCRIPT).
_LOAD_SCRIPT: str = """
local revisions_key = KEYS[1]
local cursor_key = KEYS[2]
local version_key = KEYS[3]
local author_key = KEYS[4]
local score_key = KEYS[5]

local keys_count = redis.call(
    'EXISTS', revisions_key, cursor_key, version_key, author_key, score_key
)
if keys_count == 0 then
    return {'not_found'}
end
if keys_count ~= 5 then
    return {'corrupt', 'partial_keys'}
end

local cursor = tonumber(redis.call('GET', cursor_key))
local revisions_length = redis.call('LLEN', revisions_key)
if cursor == nil or cursor < 0 or cursor >= revisions_length then
    return {'corrupt', 'cursor_out_of_range'}
end

local version = redis.call('GET', version_key)
if tonumber(version) == nil then
    return {'corrupt', 'invalid_version'}
end

return {
    'ok',
    redis.call('LINDEX', revisions_key, cursor),
    version,
    redis.call('GET', author_key),
    redis.call('GET', score_key)
}
"""

# when committing a new revision, the remaining redo revisions are removed
# if the number of revisions exceeds the limit, the oldest one is removed
# A commit still returns not_found after TTL/eviction so the tiered adapter can
# hydrate from cold.

# TODO: if the draft vanished between load and commit (TTL/eviction race), this
# currently fails with DraftNotFoundError, losing the caller's edit. The real fix
# is NOT here -- it belongs in the application-service orchestrator, as part of
# the future hot(Redis)/cold(Postgres) get-or-create cascade: on a miss, load from
# cold storage, hydrate it back into the hot cache, and only then apply/commit.
# This adapter should stay a plain hot-tier store and not try to "recover" on its
# own by inventing data the orchestrator doesn't know about.
_COMMIT_SCRIPT: str = """
local revisions_key = KEYS[1]
local cursor_key = KEYS[2]
local version_key = KEYS[3]
local author_key = KEYS[4]
local score_key = KEYS[5]

local new_revision = ARGV[1]
local version = ARGV[2]
local max_size = tonumber(ARGV[3])
local ttl_seconds = ARGV[4]

local keys_count = redis.call(
    'EXISTS', revisions_key, cursor_key, version_key, author_key, score_key
)
if keys_count == 0 then
    return {'not_found'}
end
if keys_count ~= 5 then
    return {'corrupt', 'partial_keys'}
end

local current_version = redis.call('GET', version_key)
if tonumber(current_version) == nil then
    return {'corrupt', 'invalid_version'}
end
if version ~= current_version then
    return {'version_conflict', current_version}
end

local cursor = tonumber(redis.call('GET', cursor_key))
local revisions_length = redis.call('LLEN', revisions_key)
if cursor == nil or cursor < 0 or cursor >= revisions_length then
    return {'corrupt', 'cursor_out_of_range'}
end

redis.call('LTRIM', revisions_key, 0, cursor)
redis.call('RPUSH', revisions_key, new_revision)

if redis.call('LLEN', revisions_key) > max_size then
    redis.call('LTRIM', revisions_key, -max_size, -1)
end

local new_cursor = redis.call('LLEN', revisions_key) - 1
redis.call('SET', cursor_key, new_cursor)
local new_version = redis.call('INCR', version_key)

redis.call('EXPIRE', revisions_key, ttl_seconds)
redis.call('EXPIRE', cursor_key, ttl_seconds)
redis.call('EXPIRE', version_key, ttl_seconds)
redis.call('EXPIRE', author_key, ttl_seconds)
redis.call('EXPIRE', score_key, ttl_seconds)

return {'ok', new_version}
"""

_UNDO_SCRIPT: str = """
local revisions_key = KEYS[1]
local cursor_key = KEYS[2]
local version_key = KEYS[3]
local author_key = KEYS[4]
local score_key = KEYS[5]

local version = ARGV[1]
local ttl_seconds = ARGV[2]

local keys_count = redis.call(
    'EXISTS', revisions_key, cursor_key, version_key, author_key, score_key
)
if keys_count == 0 then
    return {'not_found'}
end
if keys_count ~= 5 then
    return {'corrupt', 'partial_keys'}
end

local current_version = redis.call('GET', version_key)
if tonumber(current_version) == nil then
    return {'corrupt', 'invalid_version'}
end
if version ~= current_version then
    return {'version_conflict', current_version}
end

local cursor = tonumber(redis.call('GET', cursor_key))
local revisions_length = redis.call('LLEN', revisions_key)
if cursor == nil or cursor < 0 or cursor >= revisions_length then
    return {'corrupt', 'cursor_out_of_range'}
end

redis.call('EXPIRE', revisions_key, ttl_seconds)
redis.call('EXPIRE', cursor_key, ttl_seconds)
redis.call('EXPIRE', version_key, ttl_seconds)
redis.call('EXPIRE', author_key, ttl_seconds)
redis.call('EXPIRE', score_key, ttl_seconds)

if cursor == 0 then
    return {'no_change', current_version}
end

redis.call('DECR', cursor_key)
local new_version = redis.call('INCR', version_key)

return {'ok', new_version}
"""

_REDO_SCRIPT: str = """
local revisions_key = KEYS[1]
local cursor_key = KEYS[2]
local version_key = KEYS[3]
local author_key = KEYS[4]
local score_key = KEYS[5]

local version = ARGV[1]
local ttl_seconds = ARGV[2]

local keys_count = redis.call(
    'EXISTS', revisions_key, cursor_key, version_key, author_key, score_key
)
if keys_count == 0 then
    return {'not_found'}
end
if keys_count ~= 5 then
    return {'corrupt', 'partial_keys'}
end

local current_version = redis.call('GET', version_key)
if tonumber(current_version) == nil then
    return {'corrupt', 'invalid_version'}
end
if version ~= current_version then
    return {'version_conflict', current_version}
end

local cursor = tonumber(redis.call('GET', cursor_key))
local length = redis.call('LLEN', revisions_key)
if cursor == nil or cursor < 0 or cursor >= length then
    return {'corrupt', 'cursor_out_of_range'}
end

redis.call('EXPIRE', revisions_key, ttl_seconds)
redis.call('EXPIRE', cursor_key, ttl_seconds)
redis.call('EXPIRE', version_key, ttl_seconds)
redis.call('EXPIRE', author_key, ttl_seconds)
redis.call('EXPIRE', score_key, ttl_seconds)

if cursor == length - 1 then
    return {'no_change', current_version}
end

redis.call('INCR', cursor_key)
local new_version = redis.call('INCR', version_key)

return {'ok', new_version}
"""
