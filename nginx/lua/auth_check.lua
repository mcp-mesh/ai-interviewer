-- auth_check.lua - Session validation and user context extraction
local redis = require "resty.redis"
local json = require "cjson"

-- DEV_MODE bypass for development  
local dev_mode = ngx.var.dev_mode
ngx.log(ngx.INFO, "DEV_MODE check: ", dev_mode or "nil")
if dev_mode == "true" then
    ngx.log(ngx.INFO, "DEV_MODE: Bypassing authentication")
    -- Set fake bearer token for development
    ngx.var.bearer_token = "dev_fake_bearer_token"
    return  -- Skip authentication in dev mode
end

-- Allowlist of unprotected routes that don't require authentication
local unprotected_routes = {
    "^/api/jobs/?$",                    -- GET /api/jobs (list all jobs)
    "^/api/jobs/categories/?$",         -- GET /api/jobs/categories (job categories)
    "^/api/jobs/featured/?$",           -- GET /api/jobs/featured (featured jobs)
    "^/api/jobs/[^/]+/?$",             -- GET /api/jobs/{id} (job details)
    "^/api/health/?$"                   -- GET /api/health (health check)
}

-- Check if current URI matches any unprotected route
local uri = ngx.var.uri
for _, pattern in ipairs(unprotected_routes) do
    if string.match(uri, pattern) then
        ngx.log(ngx.INFO, "Unprotected route accessed: ", uri)
        ngx.var.bearer_token = ""  -- Set empty bearer token for unprotected routes
        return  -- Skip authentication for unprotected routes
    end
end

ngx.log(ngx.INFO, "Protected route accessed: ", uri, " - authentication required")

-- Get session cookie
local session_cookie = ngx.var.cookie_session_id
ngx.log(ngx.ERR, "Auth check - session cookie received: ", session_cookie or "nil")
if not session_cookie then
    ngx.log(ngx.INFO, "No session cookie found, redirecting to login")
    return ngx.redirect("/login")
end

-- Connect to Redis
local red = redis:new()
red:set_timeout(1000) -- 1 second
local ok, err = red:connect("redis", 6379)
if not ok then
    ngx.log(ngx.ERR, "Failed to connect to Redis: ", err)
    return ngx.redirect("/login?error=redis_connection")
end

-- Validate session
ngx.log(ngx.ERR, "Auth check - looking for session key: ", "session:" .. session_cookie)
local session_data, err = red:get("session:" .. session_cookie)
ngx.log(ngx.ERR, "Auth check - Redis get result: ", session_data or "nil", ", error: ", err or "none")
if not session_data or session_data == ngx.null then
    ngx.log(ngx.INFO, "Invalid or expired session: ", session_cookie)
    red:close()
    return ngx.redirect("/login?error=invalid_session")
end

-- Parse session data
local ok, session = pcall(json.decode, session_data)
if not ok or type(session) ~= "table" then
    ngx.log(ngx.ERR, "Failed to parse session data - ok: ", ok, ", session type: ", type(session))
    ngx.log(ngx.ERR, "Session data: ", string.sub(session_data, 1, 200))
    red:del("session:" .. session_cookie)
    red:close()
    return ngx.redirect("/login?error=invalid_session_data")
end

local current_time = ngx.time()

-- Check if session is expired
if session.expires_at and session.expires_at < current_time then
    ngx.log(ngx.INFO, "Session expired for user: ", session.user_email or "unknown")
    red:del("session:" .. session_cookie)
    red:close()
    return ngx.redirect("/login?error=session_expired")
end

-- Set bearer token variable for Authorization header (use id_token JWT for local parsing)
ngx.var.bearer_token = session.id_token or ""

-- Update session last activity
session.last_activity = current_time
red:setex("session:" .. session_cookie, 86400, json.encode(session)) -- Extend for 24 hours

red:close()

ngx.log(ngx.INFO, "Authentication successful for user: ", session.user_email or "unknown")